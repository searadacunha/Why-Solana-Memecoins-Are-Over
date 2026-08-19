#!/usr/bin/env python3
"""Etape 3 : y a-t-il un decoupage dans le financement des premiers acheteurs ?

Lit e2_funding_<label>.json, ecrit e3_splits_<label>.json.

Trois signatures, de la plus forte a la plus faible :
A. Meme transaction. Plusieurs portefeuilles finances dans une seule transaction. C'est la
   signature du cas ODIN, 12.0001 SOL decoupes en 4 x 3.000000000 depuis une seule adresse.
B. Meme montant, meme moment. Montants egaux a 1e-4 pres, dans une fenetre courte, vers >= 3
   portefeuilles distincts. Exige un groupe temoin, ce motif arrive naturellement.
C. Meme bailleur. Une source qui finance >= 2 des premiers acheteurs, quels que soient les
   montants. Faible seule, mais elle designe le distributeur a remonter a l'etape 4.

Validite : le rapport refuse de conclure « aucun decoupage » si des geneses manquent. Le verdict
est alors `echec_de_mesure` et il est nomme comme tel.

Usage :
    python3 etape3_decoupage.py --funding e2_funding_OPTIMUS.json
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
import lib_trace as L

REL_TOL = 1e-4
WINDOW_S = 3600
MIN_CLUSTER = 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--funding", required=True)
    ap.add_argument("--window", type=int, default=WINDOW_S)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    d = json.load(open(a.funding))
    label = d["label"]
    wallets = d["wallets"]
    out = a.out or f"e3_splits_{label}.json"

    # On ne cherche le decoupage que dans les financements. Les produits de vente sont ecartes :
    # deux bots qui vendent au meme instant sur la meme courbe produisent mecaniquement des montants
    # voisins au meme moment, ce qui fabriquerait un faux decoupage sur tous les tokens actifs.
    rows, n_sales = [], 0
    for w in wallets:
        for f in w["inflows"]:
            if f.get("nature") == "produit_de_vente":
                n_sales += 1
                continue
            rows.append((w["wallet"], f["amount_sol"], f["ts"], f.get("source"),
                         f.get("signature"), f.get("calibre")))
    rows.sort(key=lambda r: (r[1], r[2]))

    # --- A. financements partageant la meme transaction ---------------------------------------
    by_sig = defaultdict(list)
    for w, amt, ts, src, sig, cal in rows:
        by_sig[sig].append((w, amt, src, ts, cal))
    same_tx = []
    for sig, lst in by_sig.items():
        ws = {x[0] for x in lst}
        if len(ws) >= 2:
            same_tx.append({"signature": sig, "n_wallets": len(ws),
                            "utc": L.utc(lst[0][3]),
                            "source": lst[0][2],
                            "source_known": L.KNOWN.get(lst[0][2]),
                            "amounts_sol": sorted(round(x[1], 9) for x in lst),
                            "calibres": sorted({x[4] for x in lst}),
                            "wallets": sorted(ws)})
    same_tx.sort(key=lambda c: -c["n_wallets"])

    # --- B. meme montant, fenetre courte, portefeuilles distincts ------------------------------
    clusters, used = [], set()
    for i, (w, amt, ts, src, sig, cal) in enumerate(rows):
        if i in used or amt <= 0:
            continue
        grp = [(i, w, amt, ts, src, cal)]
        for j in range(i + 1, len(rows)):
            if j in used:
                continue
            w2, a2, t2, s2, g2, c2 = rows[j]
            if abs(a2 - amt) > amt * REL_TOL:
                break
            if w2 != w and abs(t2 - ts) <= a.window:
                grp.append((j, w2, a2, t2, s2, c2))
        ws = {g[1] for g in grp}
        if len(ws) >= MIN_CLUSTER:
            for g in grp:
                used.add(g[0])
            times = [g[3] for g in grp]
            clusters.append({"amount_sol": round(amt, 9), "calibre": cal,
                             "n_wallets": len(ws), "wallets": sorted(ws),
                             "sources": sorted({g[4] for g in grp if g[4]}),
                             "span_seconds": max(times) - min(times),
                             "utc_first": L.utc(min(times))})
    clusters.sort(key=lambda c: -c["n_wallets"])

    # --- C. bailleurs communs a plusieurs premiers acheteurs ----------------------------------
    funders = defaultdict(lambda: {"wallets": set(), "total_sol": 0.0, "n": 0,
                                   "first": None, "amounts": []})
    for w, amt, ts, src, sig, cal in rows:
        if not src:
            continue
        e = funders[src]
        e["wallets"].add(w)
        e["total_sol"] += amt
        e["n"] += 1
        e["amounts"].append(round(amt, 9))
        e["first"] = ts if e["first"] is None else min(e["first"], ts)
    # Un bailleur commun n'a de sens que s'il est prive. Le groupe temoin l'a montre : deux premiers
    # acheteurs de DOGEFORMULA sont finances par le meme portefeuille chaud de Binance, c'est le
    # depot d'un echange, pas une coordination. Les terminaux d'infrastructure connus sont donc
    # comptes a part et ne valent pas comme signature.
    common = sorted(({"funder": s, "n_early_buyers_funded": len(v["wallets"]),
                      "n_transfers": v["n"], "total_sol": round(v["total_sol"], 6),
                      "first_utc": L.utc(v["first"]), "known": L.KNOWN.get(s),
                      "amounts_sol": sorted(v["amounts"])[:20],
                      "wallets": sorted(v["wallets"])}
                     for s, v in funders.items() if len(v["wallets"]) >= 2),
                    key=lambda c: (-c["n_early_buyers_funded"], -c["total_sol"]))
    common_prive = [c for c in common if not c["known"]]
    common_infra = [c for c in common if c["known"]]

    # Deux couvertures distinctes, deux portees de conclusion.
    #  - M1 (financement de naissance, la signature ODIN) n'est testable que si la genese est atteinte.
    #  - M2 (financement pre-achat) n'est testable que si la fenetre pre-achat est couverte.
    # Un negatif ne vaut que sur la portee effectivement couverte, et jamais au-dela.
    n_fail = sum(1 for w in wallets if not w["genesis_reached"])
    n_fail_pre = sum(1 for w in wallets if not w.get("prebuy_window_reached"))
    n_hyper = sum(1 for w in wallets if w.get("hyperactif_non_mesurable"))
    positive = bool(same_tx or clusters or common_prive)
    if positive:
        verdict = "DECOUPAGE DETECTE"
    elif n_fail_pre == 0 and n_fail == 0:
        verdict = ("AUCUN DECOUPAGE — negatif PLEINEMENT VALIDE : geneses et fenetres pre-achat "
                   "atteintes pour tous les portefeuilles.")
    elif n_fail_pre == 0:
        verdict = (f"AUCUN DECOUPAGE — negatif VALIDE SUR LA FENETRE PRE-ACHAT (couverte pour "
                   f"{len(wallets)}/{len(wallets)}), mais {n_fail} portefeuille(s) n'ont pas ete "
                   "remontes jusqu'a leur naissance : la signature de type ODIN (financement de "
                   "naissance) n'est pas testee sur ceux-la.")
    else:
        verdict = (f"ECHEC DE MESURE — aucun decoupage vu, mais {n_fail_pre}/{len(wallets)} "
                   f"portefeuilles dont la fenetre pre-achat n'est pas couverte "
                   f"({n_hyper} hyperactifs). Ce n'est PAS une absence de decoupage.")

    res = {"label": label, "mint": d["mint"], "n_wallets": len(wallets),
           "n_inflows_total": len(rows),
           "n_rentrees_ecartees_produit_de_vente": n_sales,
           "n_genesis_reached": len(wallets) - n_fail, "n_genesis_NOT_reached": n_fail,
           "n_prebuy_reached": len(wallets) - n_fail_pre, "n_prebuy_NOT_reached": n_fail_pre,
           "n_hyperactifs_non_mesurables": n_hyper,
           "wallets_without_genesis": [w["wallet"] for w in wallets if not w["genesis_reached"]],
           "wallets_without_prebuy": [w["wallet"] for w in wallets
                                      if not w.get("prebuy_window_reached")],
           "verdict": verdict,
           "A_meme_transaction": same_tx,
           "B_meme_montant_meme_moment": clusters,
           "C_bailleurs_communs_PRIVES": common_prive,
           "C_bailleurs_communs_infrastructure_sans_valeur": common_infra}
    json.dump(res, open(out, "w"), indent=1)

    print(f"\n=== {label} — {len(wallets)} premiers acheteurs, {len(rows)} entrees de fonds ===")
    print(f"  geneses atteintes : {len(wallets) - n_fail}/{len(wallets)} · "
          f"fenetres pre-achat couvertes : {len(wallets) - n_fail_pre}/{len(wallets)} · "
          f"hyperactifs non mesurables : {n_hyper}")
    print(f"  rentrees ecartees comme produits de vente : {n_sales}")
    print(f"  VERDICT : {verdict}\n")
    print(f"  A. financements dans une MEME transaction : {len(same_tx)}")
    for c in same_tx[:6]:
        print(f"     {c['utc']}  {c['n_wallets']} portefeuilles  {c['amounts_sol']}  "
              f"depuis {str(c['source'])[:16]}…  [{','.join(c['calibres'])}]")
    print(f"  B. meme montant / meme moment (>= {MIN_CLUSTER} portefeuilles) : {len(clusters)}")
    for c in clusters[:6]:
        print(f"     {c['utc_first']}  {c['amount_sol']:.9f} SOL x{c['n_wallets']} "
              f"({c['span_seconds']}s) [{c['calibre']}]")
    print(f"  C. bailleurs PRIVES finançant >= 2 premiers acheteurs : {len(common_prive)}")
    for c in common_prive[:8]:
        print(f"     {c['funder']}  {c['n_early_buyers_funded']} acheteurs, "
              f"{c['total_sol']} SOL  premier le {c['first_utc']}")
    print(f"  (infrastructure, sans valeur de signature : {len(common_infra)})")
    for c in common_infra[:6]:
        print(f"     {c['funder'][:20]}…  {c['n_early_buyers_funded']} acheteurs  <== {c['known']}")
    print(f"\n  -> {out}")


if __name__ == "__main__":
    main()
