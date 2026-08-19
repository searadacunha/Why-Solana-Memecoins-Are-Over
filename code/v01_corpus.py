#!/usr/bin/env python3
"""v01 - inventaire du corpus. Aucune interpretation, que des comptages.

Sortie: data/v01_corpus.json
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import load_floor, load_snipe, load_socle, save

F = load_floor()
S = load_snipe()
D = load_socle()

with_sn = {m: d for m, d in F.items() if d.get("snipers")}
with_sw = {m: d for m, d in F.items() if d.get("swaps")}
cr = [d["created"] for d in F.values() if d.get("created")]
cr_sn = [d["created"] for d in with_sn.values()]

r = {
 "floor_capture": {
   "n_fichiers": len(F),
   "n_avec_snipers": len(with_sn),
   "n_avec_swaps": len(with_sw),
   "n_swaps_total": sum(len(d.get("swaps") or []) for d in F.values()),
   "fenetre_created_min_max": [min(cr), max(cr)],
   "fenetre_jours": round((max(cr) - min(cr)) / 86400, 2),
   "fenetre_snipers_jours": round((max(cr_sn) - min(cr_sn)) / 86400, 2),
   "n_wallets_snipeurs_distincts": len({w for d in with_sn.values() for w in d["snipers"]}),
   "n_occurrences_snipe": sum(len(d["snipers"]) for d in with_sn.values()),
 },
 "snipe_cache_onchain": {
   "n_tokens": len(S),
   "n_avec_rows": sum(1 for d in S.values() if d.get("rows")),
   "recouvrement_avec_floor_snipers": len(set(S) & set(with_sn)),
 },
 "socle_dataset": {p: len(D[p]) for p in D if isinstance(D[p], list)},
}
save("v01_corpus.json", r)
print(json.dumps(r, indent=1))
