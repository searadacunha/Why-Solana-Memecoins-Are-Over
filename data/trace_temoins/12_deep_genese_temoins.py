#!/usr/bin/env python3
"""Deuxieme passe : forcer la genese des portefeuilles restes non resolus a la passe 1.

Dans `11_temoins_split.py`, le plafond de pagination est celui de 04 (60 pages = 60 000
signatures). 54 occurrences de portefeuilles (32 adresses distinctes) ont touche ce plafond : pour
elles, les "40 premieres transactions" inspectees ne sont pas les vraies premieres, donc leur
absence de decoupage n'est pas un negatif mais un echec de mesure.

Cette passe repousse le plafond a MAX_PAGES_DEEP = 600 (600 000 signatures) pour ces seules
adresses. Ce n'est pas un ajustement de seuil de detection : aucune des constantes du detecteur
(MIN_SOL, MAX_SOL, REL_TOL, WINDOW_S, MIN_CLUSTER) ne change. On corrige le piege n.1 (pagination
silencieuse), rien d'autre.

Lit temoins_split.json, ecrit temoins_deep_genese.json, tous deux a cote du script.

Deux issues possibles par adresse :
  - genese atteinte : ses 40 premieres vraies tx sont inspectees, le negatif devient valide ;
  - plafond touche : le nombre de signatures parcourues est declare comme borne inferieure de son
    activite. C'est une adresse industrielle, pas un portefeuille de flotte.
"""
from __future__ import annotations
import json, os, sys, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "p1", os.path.join(os.path.dirname(os.path.abspath(__file__)), "11_temoins_split.py"))
p1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p1)

MAX_PAGES_DEEP = 600
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temoins_deep_genese.json")
IN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temoins_split.json")


def deep(w: str) -> dict:
    t = time.time()
    sigs, genesis, _, pages = p1.paginate(w, MAX_PAGES_DEEP)
    first = sigs[:p1.FIRST_TX_PER_WALLET]

    def one(s):
        tx = p1.rpc("getTransaction", [s["signature"],
                    {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            return None
        try:
            keys = [k["pubkey"] if isinstance(k, dict) else k
                    for k in tx["transaction"]["message"]["accountKeys"]]
            i = keys.index(w)
            pre, post = tx["meta"]["preBalances"], tx["meta"]["postBalances"]
            d = (post[i] - pre[i]) / p1.LAMPORTS
        except Exception:
            return None
        if not (p1.MIN_SOL <= d <= p1.MAX_SOL):
            return None
        src, worst = None, 0.0
        for j, k in enumerate(keys):
            if j == i:
                continue
            dj = (post[j] - pre[j]) / p1.LAMPORTS
            if dj < worst:
                worst, src = dj, k
        return {"sol": round(d, 9), "ts": tx.get("blockTime") or 0, "sig": s["signature"],
                "source_probable": src}

    with ThreadPoolExecutor(max_workers=8) as ex:
        ev = [r for r in ex.map(one, first) if r]
    old = sigs[0].get("blockTime") if sigs else None
    r = {"wallet": w, "genese_atteinte": genesis, "pages_paginees": pages,
         "n_sigs_vues": len(sigs),
         "plus_ancienne_vue_utc": dt.datetime.fromtimestamp(old, dt.UTC).isoformat() if old else None,
         "entrees": ev, "duree_s": round(time.time() - t, 1)}
    print(f"  {w[:14]}… {len(sigs):>7} sigs, {pages} pages, genese "
          f"{'ATTEINTE' if genesis else 'NON ATTEINTE (plafond 600 pages)'} | "
          f"{len(ev)} entrees | plus ancienne {r['plus_ancienne_vue_utc']}", flush=True)
    return r


def main():
    d = json.load(open(IN))
    todo, where = [], {}
    for t in d["tokens"]:
        for w in t["portefeuilles"]:
            if not w["genese_atteinte"]:
                where.setdefault(w["wallet"], []).append(t["symbole"])
                if w["wallet"] not in todo:
                    todo.append(w["wallet"])
    print(f"{len(todo)} adresses distinctes non resolues a la passe 1 | plafond porte a "
          f"{MAX_PAGES_DEEP} pages | {len(p1.URLS)} cles RPC", flush=True)

    res = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for r in ex.map(deep, todo):
            r["tokens_temoins"] = where[r["wallet"]]
            res.append(r)
            json.dump({"genere_le": dt.datetime.now(dt.UTC).isoformat(),
                       "max_pages": MAX_PAGES_DEEP, "adresses": res}, open(OUT, "w"), indent=1)

    ok = [r for r in res if r["genese_atteinte"]]
    print(f"\n=== {len(ok)}/{len(res)} geneses desormais ATTEINTES ===")
    for r in res:
        if not r["genese_atteinte"]:
            print(f"  PLAFOND : {r['wallet']} > {r['n_sigs_vues']} tx "
                  f"(adresse industrielle) — presente dans {len(r['tokens_temoins'])} temoin(s)")
    print(f"\nEcrit dans {OUT}")


if __name__ == "__main__":
    main()
