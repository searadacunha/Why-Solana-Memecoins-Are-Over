#!/usr/bin/env python3
"""Troisieme passe : corriger le PIEGE DE LA PAGE VIDE.

CE QU'ON A DECOUVERT
--------------------
La condition d'arret "une page revient incomplete = genese atteinte", utilisee dans 04 et dans les
passes 1 et 2, admet un cas faux : sous charge, Helius renvoie parfois `result: []` SANS erreur au
milieu de l'historique. Le paginateur conclut alors a la genese, en silence, sur une adresse qui a
encore des centaines de milliers de transactions plus anciennes. C'est le piege n.1 sous une forme
nouvelle : non plus un plafond de pages, mais une reponse vide mensongere.

COMMENT ON LES REPERE SANS RIEN RE-PAGINER
------------------------------------------
Une pagination qui s'acheve normalement finit sur une page PARTIELLE (1 a 999 signatures), donc son
total n'est pas un multiple de 1000. Un total exactement multiple de 1000 signifie que la derniere
page etait PLEINE et que l'arret vient d'une page VIDE : c'est le seul arret non fiable.
3 adresses sur 111 marquees "genese atteinte" a la passe 1 sont dans ce cas.

LE PAGINATEUR CORRIGE
---------------------
Sur page vide, on re-interroge 3 fois la MEME page. On ne conclut a la genese que si les 3
confirmations sont vides. Verdict des 3 adresses :
    ARsCio3NSiKWop…  genese reellement atteinte a 65 619 tx (la passe 1 s'arretait a 30 000)
    6UEprdYLQpgdgg…  genese reellement atteinte a 11 247 tx (la passe 1 s'arretait a  9 000)
    X1C2Qt6NZc7Epn…  genese NON atteinte a 900 000 tx — adresse industrielle, elle etait comptee
                     a tort comme resolue dans 6 temoins
Les deux premieres voient leur financement RE-MESURE sur leurs vraies 40 premieres transactions.
Aucune constante du detecteur n'est touchee.
"""
from __future__ import annotations
import importlib.util, json, os, datetime as dt
from concurrent.futures import ThreadPoolExecutor

D = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("p1", f"{D}/11_temoins_split.py")
p1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p1)

MAX_PAGES = 900


def paginate_confirme(addr: str):
    """Comme p1.paginate, mais une page vide doit etre confirmee 3 fois."""
    out, before, gen, pages = [], None, False, 0
    while pages < MAX_PAGES:
        pg = p1.rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}]) or []
        pages += 1
        if not pg:
            if all(not (p1.rpc("getSignaturesForAddress",
                               [addr, {"limit": 1000, "before": before}]) or []) for _ in range(3)):
                gen = True
                break
            continue
        out.extend(pg)
        if len(pg) < 1000:
            gen = True
            break
        before = pg[-1]["signature"]
    return sorted(out, key=lambda s: s.get("blockTime") or 0), gen, pages


def funding(wallet: str, sigs: list) -> list:
    def one(s):
        tx = p1.rpc("getTransaction", [s["signature"],
                    {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            return None
        try:
            keys = [k["pubkey"] if isinstance(k, dict) else k
                    for k in tx["transaction"]["message"]["accountKeys"]]
            i = keys.index(wallet)
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
        return [r for r in ex.map(one, sigs[:p1.FIRST_TX_PER_WALLET]) if r]


def suspects() -> list[str]:
    d = json.load(open(f"{D}/temoins_split.json"))
    seen = {}
    for t in d["tokens"]:
        for w in t["portefeuilles"]:
            seen[w["wallet"]] = (w["genese_atteinte"], w["n_sigs_vues"])
    return [w for w, (g, n) in seen.items() if g and n > 0 and n % 1000 == 0]


def main():
    sus = suspects()
    print(f"{len(sus)} adresses au total exactement multiple de 1000 signatures "
          f"(= arret sur page VIDE, non fiable)", flush=True)
    res = []
    for w in sus:
        sg, gen, pages = paginate_confirme(w)
        ev = funding(w, sg) if gen else funding(w, sg)
        old = sg[0].get("blockTime") if sg else None
        r = {"wallet": w, "genese_atteinte": gen, "pages_paginees": pages, "n_sigs_vues": len(sg),
             "plus_ancienne_vue_utc": dt.datetime.fromtimestamp(old, dt.UTC).isoformat() if old else None,
             "entrees": ev, "paginateur": "confirme (page vide re-interrogee 3 fois)"}
        res.append(r)
        print(f"  {w[:14]}… {len(sg)} sigs / {pages} pages | genese "
              f"{'ATTEINTE' if gen else f'NON ATTEINTE (plafond {MAX_PAGES})'} | "
              f"{len(ev)} entrees | plus ancienne {r['plus_ancienne_vue_utc']}", flush=True)
        json.dump({"genere_le": dt.datetime.now(dt.UTC).isoformat(), "max_pages": MAX_PAGES,
                   "adresses": res}, open(f"{D}/temoins_corrections.json", "w"), indent=1)
    print(f"\nEcrit dans {D}/temoins_corrections.json")


if __name__ == "__main__":
    main()
