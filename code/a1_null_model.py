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
    """Criteria A / B / C applied to an arbitrary wallet group.

    A (shared funding transaction) and C (shared private funder) are the phase-1
    detector's definitions. B is the split-grouping of splitlib.find_splits with
    the same parameters, reduced to a boolean: does at least one cluster of
    MIN_CLUSTER distinct wallets exist? For that boolean the `used` bookkeeping
    of find_splits is provably irrelevant — find_splits only marks events used
    when a cluster VALIDATES, so up to its first validated cluster the set is
    empty and every seed is scanned exactly as below. Equivalence with
    find_splits is enforced by tests/test_splitlib.py.

    An earlier version of this function marked events used while scanning, even
    for clusters below MIN_CLUSTER — a semantics find_splits does not have,
    which could hide a real cluster behind a failed seed and understate the
    false-positive rate. It also claimed to be splitlib "unchanged", which was
    not true. Both are fixed here; the committed artefact is regenerated.
    """
    rows = [(g["wallet"], a, t, s, sig) for g in group for a, t, s, sig in g["events"]]

    by_sig = defaultdict(set)
    for w, a, t, s, sig in rows:
        by_sig[sig].add(w)
    A = any(len(ws) >= 2 for ws in by_sig.values())

    # B: find_splits semantics — events sorted by amount alone (stable), every
    # seed scanned, cluster = distinct wallets within REL_TOL and WINDOW_S.
    events = [(w, a, t) for w, a, t, s, sig in rows]
    events.sort(key=lambda e: e[1])
    B = False
    for i, (w, amt, ts) in enumerate(events):
        ws = {w}
        for j in range(i + 1, len(events)):
            w2, a2, t2 = events[j]
            if abs(a2 - amt) > amt * REL_TOL:
                break                          # sorted by amount: nothing else fits
            if w2 != w and abs(t2 - ts) <= WINDOW_S:
                ws.add(w2)
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
        sys.exit("No control wallet found. Run the control group first.")
    sizes = defaultdict(int)
    for w in pool:
        sizes[w["token"]] += 1

    print(f"Null population: {len(pool)} wallets from {len(sizes)} control tokens")
    print(f"  funding events: {sum(len(w['events']) for w in pool)}")

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
        print(f"\n  group of {k} wallets drawn at random ({a.draws} draws):")
        print(f"    A  same funding transaction     : {r['P_A_meme_transaction']:.4f}")
        print(f"    B  same amount within 1 h       : {r['P_B_meme_montant_1h']:.4f}")
        print(f"    C  shared private funder        : {r['P_C_bailleur_prive_commun']:.4f}")
        print(f"    at least one criterion          : {r['P_au_moins_un_critere']:.4f}")

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
        print(f"\n  restricted to the {len(pool_g)} wallets whose genesis was reached: "
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
        "lecture": "If the top funder only covers a marginal share of the population, C's firing "
                   "rate does not come from a handful of unlabelled infrastructure addresses: it "
                   "comes from the number of PAIRS that 40 wallets form. That is a birthday "
                   "problem, and extending the list of known terminals would change nothing.",
    }
    print(f"\n  distinct private funders in the population : {len(ranked)}")
    print(f"  of which fund at least 2 wallets           : {n_multi}")
    for t in top[:5]:
        print(f"    {t['funder'][:16]}… {t['n_wallets_finances']} wallets "
              f"({t['part_de_la_population']:.1%} of the population)")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({
        "objet": "False-positive rate of the split detector on wallet groups drawn at random "
                 "from the control population.",
        "methode": "Control-token wallets are pooled, then groups of size k are drawn without "
                   "replacement. Criterion B applies the split-grouping semantics of "
                   "splitlib.find_splits, reduced to a boolean (REL_TOL=1e-4, window=3600 s, "
                   "min cluster=3; equivalence enforced by tests/test_splitlib.py). Criteria A "
                   "(shared funding transaction) and C (shared private funder) are the phase-1 "
                   "detector's definitions. Resampling destroys within-token co-occurrence: any "
                   "detection in a drawn group is therefore a coincidence.",
        "population": {"n_portefeuilles": len(pool), "n_tokens": len(sizes),
                       "n_evenements_financement": sum(len(w["events"]) for w in pool),
                       "par_token": dict(sizes)},
        "graine": a.seed, "par_taille_de_groupe": results,
        "genese_atteinte_seulement": res_g,
        "ubiquite_des_bailleurs": ubiquity,
        "portee": "This rate measures the detector's propensity to fire by chance on the era's "
                  "wallet population. It does not correct the selection bias of the target "
                  "cohort, which is a separate defect.",
    }, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
