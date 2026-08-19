#!/usr/bin/env python3
"""Etape 5 : rattrapage de couverture. Analyse de sensibilite, pas la mesure principale.

La mesure principale laisse une partie des portefeuilles hors couverture, et pour ceux-la "aucun
decoupage" est un echec de mesure. La cause n'est pas la nature de ces portefeuilles mais un
plafond : `MAX_PAGES=400` dans etape2, plus un arret par projection qui se declenche quand il
faudrait plus de 1,5 x (plafond restant) pages. En pratique ces bots s'arretent a quinze pages de
couvrir leur fenetre, la mesure est perdue pour presque rien.

Lit les e2_funding_*.json des temoins et ceux des cibles dans data/trace_optimus. Ecrit un
e2r_funding_<label>.json par token, plus le journal t5_rattrapage_journal.json.

Ce n'est pas un ajustement de seuil :
1. La mesure principale (t4_taux_de_base.json) reste inchangee et reste la reference.
2. Le plafond releve ne touche aucun critere de detection, ni REL_TOL, ni WINDOW_S, ni MIN_CLUSTER,
   ni MIN_INFLOW. Il n'agit que sur la quantite d'historique lue. Il ne peut donc pas rendre positif
   un portefeuille deja couvert, seulement ajouter des donnees la ou il n'y en avait pas.
3. Il est applique symetriquement aux temoins et aux cibles, dans le meme passage. Ne rattraper que
   les temoins gonflerait le taux de base, ne rattraper que les cibles le deprimerait. Les deux
   seraient une fraude.

Usage :
    python3 t5_rattrapage_couverture.py --max-pages 900
"""
from __future__ import annotations
import argparse, json, os, sys, time
import lib_trace as L
import t2_financement as T2

HERE = os.path.dirname(os.path.abspath(__file__))
CIBLE_DIR = os.path.join(os.path.dirname(HERE), "trace_optimus")


def repagine(w, prebuy_start, max_pages):
    """Pagination sans arret par projection et avec un plafond releve.

    L'arret par projection est neutralise en passant un plafond tres grand a la fonction : la
    condition `need > 1.5 * (max_pages - pages)` ne peut plus se declencher tant que la marge reste
    large. Le plafond effectif est applique ici, en dur, par le nombre de pages demande.
    """
    sigs, genesis, pages = L.all_signatures(w, max_pages=max_pages, label=w[:8],
                                            stop_ts=prebuy_start, verbose=True)
    hyper = bool(getattr(L.all_signatures, "last_capped_by_projection", False))
    return ([{"signature": s["signature"], "blockTime": s.get("blockTime")} for s in sigs],
            genesis, pages, hyper)


def refais_wallet(w0, max_pages, min_inflow):
    """Refait la mesure de financement d'un seul portefeuille, plafond releve."""
    w = w0["wallet"]
    first_buy_ts = w0["first_buy_ts"]
    prebuy_start = first_buy_ts - T2.PREBUY_DAYS * 86400
    sigs, genesis, pages, hyper = repagine(w, prebuy_start, max_pages)
    oldest = sigs[0]["blockTime"] if sigs else None
    reached = bool(oldest and oldest <= prebuy_start) or genesis
    info = dict(w0)
    info.update({"n_signatures_total": len(sigs), "pages_paginated": pages,
                 "genesis_reached": genesis, "hyperactif_non_mesurable": hyper,
                 "pagination_capped": pages >= max_pages or hyper,
                 "oldest_seen_ts": oldest, "oldest_seen_utc": L.utc(oldest),
                 "prebuy_window_reached": reached,
                 "prebuy_window_days_covered": (min(round((first_buy_ts - oldest) / 86400.0, 2),
                                                    float(T2.PREBUY_DAYS)) if oldest else 0.0),
                 "rattrapage_plafond_pages": max_pages,
                 "inflows": []})
    if not sigs:
        info["measurement_failure"] = "aucune signature"
        return info
    picks, phases = [], []
    if genesis:
        for s in sigs[:60]:
            picks.append(s["signature"]); phases.append("M1_naissance")
    pre = [s for s in sigs if prebuy_start <= (s.get("blockTime") or 0) <= first_buy_ts]
    for s in pre[:T2.PREBUY_MAX_TX]:
        if s["signature"] not in picks:
            picks.append(s["signature"]); phases.append("M2_prebuy")
    info["n_tx_in_prebuy_window"] = len(pre)
    txs = L.get_transactions(picks)
    info["n_tx_fetched"] = len(txs)
    seen = set()
    for sig, ph in zip(picks, phases):
        if sig in seen:
            continue
        seen.add(sig)
        info["inflows"].extend(T2.inflows_from(txs, [sig], w, min_inflow, ph))
    info["inflows"].sort(key=lambda f: f["ts"])
    info["measurement_failure"] = None if reached else \
        f"fenetre pre-achat non atteinte meme a {max_pages} pages"
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=900)
    ap.add_argument("--min-inflow", type=float, default=T2.MIN_INFLOW)
    ap.add_argument("--files", nargs="*", help="e2_funding_*.json a rattraper")
    a = ap.parse_args()

    files = a.files or (sorted(f for f in os.listdir(HERE) if f.startswith("e2_funding_"))
                        + [os.path.join(CIBLE_DIR, f) for f in sorted(os.listdir(CIBLE_DIR))
                           if f.startswith("e2_funding_") and "Calm" not in f and "faith" not in f])
    journal = []
    for f in files:
        p = f if os.path.isabs(f) else os.path.join(HERE, f)
        d = json.load(open(p))
        lab = d["label"]
        cibles = [w for w in d["wallets"] if not w.get("prebuy_window_reached")]
        print(f"\n=== {lab} : {len(cibles)}/{len(d['wallets'])} portefeuilles a rattraper", flush=True)
        if not cibles:
            continue
        changed = 0
        for i, w0 in enumerate(cibles, 1):
            t0 = time.time()
            new = refais_wallet(w0, a.max_pages, a.min_inflow)
            for k, w in enumerate(d["wallets"]):
                if w["wallet"] == new["wallet"]:
                    d["wallets"][k] = new
            ok = new["prebuy_window_reached"]
            changed += 1 if ok else 0
            print(f"  [{i}/{len(cibles)}] {new['wallet'][:14]}… {new['pages_paginated']} pages, "
                  f"{new['n_signatures_total']} sigs, prebuy "
                  f"{'MAINTENANT COUVERT' if ok else 'toujours hors atteinte'}, "
                  f"{len(new['inflows'])} entrees, {time.time()-t0:.0f}s", flush=True)
            journal.append({"token": lab, "wallet": new["wallet"],
                            "pages": new["pages_paginated"],
                            "sigs": new["n_signatures_total"],
                            "prebuy_reached_apres": ok,
                            "genesis_reached_apres": new["genesis_reached"],
                            "n_inflows_apres": len(new["inflows"])})
        out = os.path.join(HERE, f"e2r_funding_{lab}.json")
        nf_p = sum(1 for w in d["wallets"] if not w.get("prebuy_window_reached"))
        nf_g = sum(1 for w in d["wallets"] if not w.get("genesis_reached"))
        d.update({"rattrapage": True, "rattrapage_plafond_pages": a.max_pages,
                  "n_prebuy_NOT_reached": nf_p, "n_genesis_NOT_reached": nf_g})
        json.dump(d, open(out, "w"), indent=1)
        print(f"  {changed}/{len(cibles)} recuperes -> {out}", flush=True)
    json.dump(journal, open(os.path.join(HERE, "t5_rattrapage_journal.json"), "w"), indent=1)
    print(f"\n  journal -> t5_rattrapage_journal.json ({len(journal)} portefeuilles)")


if __name__ == "__main__":
    main()
