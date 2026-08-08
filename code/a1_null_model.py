#!/usr/bin/env python3
"""Adversarial null model: how often does the split detector fire on a random group of wallets?

WHY THIS EXISTS
---------------
The detector flags a token when its early buyers share a funding transaction (A), receive the same
amount within an hour (B), or share a private funder (C). Reporting "the detector fired on the
targets" means nothing until we know how often it fires on wallets that were never coordinated.

The control tokens supply that population: 136 early-buyer wallets drawn from tokens selected on
creation slot alone, with their funding events already measured by the exact same code. We pool
those wallets, draw random groups of the same size as a target's buyer set, and re-run the three
criteria unchanged. The share of draws that fire is the false-positive rate of the detector on this
era's wallet population.

Resampling deliberately destroys within-token co-occurrence. A hit in a resampled group is
therefore a genuine coincidence: two unrelated wallets that happen to share a funder, or to have
received near-identical amounts within the same hour.

WHAT IT DOES NOT DO
-------------------
It does not correct the selection bias of the target cohort (tokens picked by the author because
they were profitable). That is a separate defect, quantified in the same output and discussed in
docs/PITFALLS.md. A low false-positive rate makes a positive harder to dismiss; it does not make a
selected sample representative.

USAGE
    python3 code/a1_null_model.py [--draws 5000] [--seed 12345]
Reads only files already published under ./data/. No network access, no key.
"""
from __future__ import annotations
import argparse, glob, json, os, random, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

REL_TOL = 1e-4      # identical to splitlib.py
WINDOW_S = 3600     # identical
MIN_CLUSTER = 3     # identical

# Infrastructure terminals: a shared exchange hot wallet is a deposit, not a coordination.
# Same list as lib_trace.KNOWN, kept here so this script stays runnable from published data alone.
KNOWN = {
    "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t", "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9",
    "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6", "2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS",
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w", "is6MTRHEgyFLNTfYcuV4QBWLjrZBfmhVNYR6ccgr8KV",
}


def load_wallets(pattern):
    """Every early-buyer wallet of the matching tokens, with its FUNDING events only."""
    out = []
    for path in sorted(glob.glob(pattern)):
        d = json.load(open(path))
        for w in d.get("wallets", []):
            ev = [(f["amount_sol"], f["ts"], f.get("source"), f.get("signature"))
                  for f in w.get("inflows", [])
                  if f.get("nature") != "produit_de_vente" and f.get("amount_sol", 0) > 0]
            out.append({"wallet": w["wallet"], "token": d["label"], "events": ev,
                        "genesis": bool(w.get("genesis_reached"))})
    return out


def detect(group):
    """Criteria A / B / C of splitlib.py, unchanged, applied to an arbitrary wallet group."""
    rows = [(g["wallet"], a, t, s, sig) for g in group for a, t, s, sig in g["events"]]
    rows.sort(key=lambda r: (r[1], r[2]))

    by_sig = defaultdict(set)
    for w, a, t, s, sig in rows:
        by_sig[sig].add(w)
    A = any(len(ws) >= 2 for ws in by_sig.values())

    B, used = False, set()
    for i, (w, amt, ts, s, sig) in enumerate(rows):
        if i in used:
            continue
        ws = {w}
        for j in range(i + 1, len(rows)):
            w2, a2, t2, _, _ = rows[j]
            if abs(a2 - amt) > amt * REL_TOL:
                break
            if w2 != w and abs(t2 - ts) <= WINDOW_S:
                ws.add(w2)
                used.add(j)
        if len(ws) >= MIN_CLUSTER:
            B = True
            break

    funders = defaultdict(set)
    for w, a, t, s, sig in rows:
        if s and s not in KNOWN:
            funders[s].add(w)
    C = any(len(ws) >= 2 for ws in funders.values())
    return A, B, C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--out", default=os.path.join(DATA, "adverse", "a1_null_model.json"))
    a = ap.parse_args()
    rng = random.Random(a.seed)

    pool = load_wallets(os.path.join(DATA, "trace_temoins", "e2_funding_*.json"))
    if not pool:
        sys.exit("Aucun portefeuille temoin trouve. Lancer d'abord le groupe temoin.")
    sizes = defaultdict(int)
    for w in pool:
        sizes[w["token"]] += 1

    print(f"Population nulle : {len(pool)} portefeuilles issus de {len(sizes)} tokens temoins")
    print(f"  evenements de financement : {sum(len(w['events']) for w in pool)}")

    # The draw size is the one the detector actually faces on a target: 40 buyers per token.
    results = {}
    for k in (10, 20, 40):
        if k > len(pool):
            continue
        nA = nB = nC = nAny = 0
        for _ in range(a.draws):
            grp = rng.sample(pool, k)
            A, B, C = detect(grp)
            nA += A; nB += B; nC += C; nAny += (A or B or C)
        results[k] = {"n_draws": a.draws,
                      "P_A_meme_transaction": nA / a.draws,
                      "P_B_meme_montant_1h": nB / a.draws,
                      "P_C_bailleur_prive_commun": nC / a.draws,
                      "P_au_moins_un_critere": nAny / a.draws}
        r = results[k]
        print(f"\n  groupe de {k} portefeuilles tires au hasard ({a.draws} tirages) :")
        print(f"    A  meme transaction de financement : {r['P_A_meme_transaction']:.4f}")
        print(f"    B  meme montant en moins d'1 h     : {r['P_B_meme_montant_1h']:.4f}")
        print(f"    C  bailleur prive commun           : {r['P_C_bailleur_prive_commun']:.4f}")
        print(f"    au moins un critere                : {r['P_au_moins_un_critere']:.4f}")

    # Same measurement restricted to wallets whose genesis was actually reached: a negative on a
    # wallet we could not page back to birth is a measurement failure, not an observation.
    pool_g = [w for w in pool if w["genesis"]]
    res_g = None
    if len(pool_g) >= 40:
        nAny = 0
        for _ in range(a.draws):
            A, B, C = detect(rng.sample(pool_g, 40))
            nAny += (A or B or C)
        res_g = {"n_portefeuilles": len(pool_g), "P_au_moins_un_critere": nAny / a.draws}
        print(f"\n  restreint aux {len(pool_g)} portefeuilles a genese atteinte : "
              f"{res_g['P_au_moins_un_critere']:.4f}")

    # Why does C fail? Two explanations have different lessons. Either funders are simply too few
    # for 40 wallets to avoid a collision — a birthday problem, irreducible — or a handful of
    # unlabelled infrastructure addresses fund half the population, in which case the fix is to
    # extend the KNOWN list rather than to retire the criterion. Rank them and see.
    fund_wallets = defaultdict(set)
    for w in pool:
        for amt, ts, s, sig in w["events"]:
            if s and s not in KNOWN:
                fund_wallets[s].add(w["wallet"])
    ranked = sorted(fund_wallets.items(), key=lambda kv: -len(kv[1]))
    n_multi = sum(1 for s, ws in ranked if len(ws) >= 2)
    top = [{"funder": s, "n_wallets_finances": len(ws),
            "part_de_la_population": round(len(ws) / len(pool), 4)} for s, ws in ranked[:10]]
    ubiquity = {
        "n_bailleurs_prives_distincts": len(ranked),
        "n_bailleurs_finançant_2_portefeuilles_ou_plus": n_multi,
        "top_bailleurs": top,
        "lecture": "Si le premier bailleur ne couvre qu'une part marginale de la population, le "
                   "taux de declenchement de C ne vient pas d'une poignee d'adresses "
                   "d'infrastructure oubliees : il vient du nombre de PAIRES que forment 40 "
                   "portefeuilles. C'est alors un probleme d'anniversaire, et allonger la liste "
                   "des terminaux connus n'y changerait rien.",
    }
    print(f"\n  bailleurs prives distincts dans la population : {len(ranked)}")
    print(f"  dont finançant au moins 2 portefeuilles       : {n_multi}")
    for t in top[:5]:
        print(f"    {t['funder'][:16]}… {t['n_wallets_finances']} portefeuilles "
              f"({t['part_de_la_population']:.1%} de la population)")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({
        "objet": "Taux de faux positifs du detecteur de decoupage sur des groupes de portefeuilles "
                 "tires au hasard dans la population temoin.",
        "methode": "Les portefeuilles des tokens temoins sont mis en commun, puis des groupes de "
                   "taille k sont tires sans remise. Les criteres A/B/C sont ceux de "
                   "splitlib.py, sans modification (REL_TOL=1e-4, fenetre=3600 s, "
                   "cluster minimal=3). Le tirage detruit la co-occurrence interne a un token : "
                   "toute detection dans un groupe tire est donc une coincidence.",
        "population": {"n_portefeuilles": len(pool), "n_tokens": len(sizes),
                       "n_evenements_financement": sum(len(w["events"]) for w in pool),
                       "par_token": dict(sizes)},
        "graine": a.seed, "par_taille_de_groupe": results,
        "genese_atteinte_seulement": res_g,
        "ubiquite_des_bailleurs": ubiquity,
        "portee": "Ce taux mesure la propension du detecteur a se declencher par hasard sur la "
                  "population de portefeuilles de l'epoque. Il ne corrige pas le biais de "
                  "selection de la cohorte de cibles, qui est un defaut distinct.",
    }, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
