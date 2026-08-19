#!/usr/bin/env python3
"""v02 - re-derivation independante des flottes d'operateurs.

On ne reprend pas une seule liste de wallets de l'analyse anterieure. On repart
de la geometrie brute de la fenetre de creation (cache snipe_*.json, derive de
Helius, 1 ligne par wallet ayant achete <=12s apres le mint) et on reconstruit
les flottes par co-occurrence.

Definitions (arbitraires mais fixees a l'avance et explicites) :
  noyau d'un token   = wallets ayant engage >= 5 SOL dans la fenetre de creation
  infra (a exclure)  = wallet present dans >= 25 tokens sur 282 (>8.9%) : bot
                       ubiquitaire, ne peut pas etre la flotte d'un operateur
  arete flotte       = paire de wallets de noyau co-presentes sur >= 3 tokens
                       et Jaccard >= 0.50
  flotte             = composante connexe >= 3 wallets

Sortie: data/v02_fleets.json
"""
import sys, os, json, itertools, statistics as st
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import load_snipe, save, cv, med

MIN_SOL   = 5.0
INFRA_N   = 25
MIN_CO    = 3
MIN_JAC   = 0.50

S = load_snipe()
N = len(S)

# --- noyaux bruts -----------------------------------------------------------
core_raw = {}
for m, d in S.items():
    core_raw[m] = {w: (v.get("sol") or 0.0) for w, v in (d.get("rows") or {}).items()
                   if (v.get("sol") or 0.0) >= MIN_SOL}

freq = Counter()
for m, c in core_raw.items():
    for w in c:
        freq[w] += 1
INFRA = {w for w, n in freq.items() if n >= INFRA_N}

core = {m: {w: s for w, s in c.items() if w not in INFRA} for m, c in core_raw.items()}
w2t = defaultdict(set)
for m, c in core.items():
    for w in c:
        w2t[w].add(m)

# --- graphe de co-occurrence ------------------------------------------------
pair = Counter()
for m, c in core.items():
    for a, b in itertools.combinations(sorted(c), 2):
        pair[(a, b)] += 1

adj = defaultdict(set)
edges = []
for (a, b), n in pair.items():
    jac = n / len(w2t[a] | w2t[b])
    if n >= MIN_CO and jac >= MIN_JAC:
        adj[a].add(b); adj[b].add(a)
        edges.append({"a": a, "b": b, "co": n, "jaccard": round(jac, 3)})

seen, fleets = set(), []
for w in list(adj):
    if w in seen:
        continue
    comp, stack = set(), [w]
    while stack:
        x = stack.pop()
        if x in comp:
            continue
        comp.add(x); seen.add(x)
        stack += list(adj[x] - comp)
    if len(comp) >= 3:
        fleets.append(sorted(comp))

# --- profil par flotte ------------------------------------------------------
out = []
for wl in sorted(fleets, key=lambda x: -len({m for w in x for m in w2t[w]})):
    toks = sorted({m for w in wl for m in w2t[w]}, key=lambda m: S[m]["created"])
    launches = []
    for m in toks:
        c = core[m]
        mem = {w: s for w, s in c.items() if w in wl}
        if not mem:
            continue
        rows = S[m].get("rows") or {}
        ts = [rows[w]["ts"] for w in mem if rows[w].get("ts")]
        tickets = sorted(mem.values(), reverse=True)
        launches.append({
            "mint": m, "created": S[m]["created"],
            "n_membres": len(mem),
            "sol_flotte": round(sum(mem.values()), 4),
            "sol_noyau_total": round(sum(c.values()), 4),
            "sol_fenetre_total": round(sum((v.get("sol") or 0.0)
                                           for v in rows.values()), 4),
            "ticket_med": round(med(tickets), 4),
            "ticket_cv": round(cv(list(mem.values())), 4),
            "ts_span_s": (max(ts) - min(ts)) if ts else None,
            "tickets": [round(x, 4) for x in tickets],
        })
    if not launches:
        continue
    memb_n = [l["n_membres"] for l in launches]
    out.append({
        "lead": wl[0],
        "n_wallets": len(wl),
        "wallets": wl,
        "n_tokens": len(launches),
        "n_membres_mode": Counter(memb_n).most_common(1)[0],
        "sol_flotte_med": round(med([l["sol_flotte"] for l in launches]), 3),
        "sol_flotte_min_max": [min(l["sol_flotte"] for l in launches),
                               max(l["sol_flotte"] for l in launches)],
        "cv_inter_lancements": round(cv([l["sol_flotte"] for l in launches]), 4),
        "ticket_cv_intra_med": round(med([l["ticket_cv"] for l in launches]), 4),
        "ts_span_s_max": max([l["ts_span_s"] for l in launches if l["ts_span_s"] is not None] or [None]),
        "part_sol_fenetre_med": round(med([l["sol_flotte"] / l["sol_fenetre_total"]
                                           for l in launches if l["sol_fenetre_total"] > 0]), 4),
        "span_h": round((launches[-1]["created"] - launches[0]["created"]) / 3600, 1),
        "launches": launches,
    })

r = {
 "parametres": {"MIN_SOL": MIN_SOL, "INFRA_N": INFRA_N, "MIN_CO": MIN_CO,
                "MIN_JAC": MIN_JAC, "n_tokens_corpus": N},
 "infra_exclue": sorted([{"wallet": w, "n_tokens": freq[w]} for w in INFRA],
                        key=lambda x: -x["n_tokens"]),
 "n_flottes": len(out),
 "n_tokens_couverts": len({l["mint"] for f in out for l in f["launches"]}),
 "flottes": out,
}
save("v02_fleets.json", r)
for f in out:
    print(f"{f['lead'][:12]:14s} nw={f['n_wallets']} ntok={f['n_tokens']:3d} "
          f"SOL_med={f['sol_flotte_med']:7.2f} [{f['sol_flotte_min_max'][0]:.1f};"
          f"{f['sol_flotte_min_max'][1]:.1f}] CV_inter={f['cv_inter_lancements']:.3f} "
          f"CVintra={f['ticket_cv_intra_med']:.3f} span_ts_max={f['ts_span_s_max']}s "
          f"part_SOL={f['part_sol_fenetre_med']:.3f}")
print("n_flottes", len(out), "tokens couverts", r["n_tokens_couverts"], "/", N)
