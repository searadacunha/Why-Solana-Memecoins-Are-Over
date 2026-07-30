#!/usr/bin/env python3
"""Enrichit les mints recoltes via l'API pump + mesure d'activite on-chain.

Deux mesures independantes de la performance :
  - pump API : complete (= courbe terminee -> Raydium), king_of_the_hill, reply_count,
    usd_market_cap actuel. NB: ath_market_cap de l'API est un maximum RECENT, pas l'ATH
    historique de 2024 (verifie : tous les ath_market_cap_timestamp tombent en 2026).
  - on-chain : nombre TOTAL de transactions sur le compte bonding_curve, pagine
    JUSQU'A LA GENESE (une page incomplete). C'est la mesure d'activite reelle du token
    sur toute sa vie, et elle dit si le token a assez d'acheteurs pour etre analysable.
"""
from __future__ import annotations
import json, os, sys, time, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor

RPC = os.environ.get("SOLANA_RPC_URL", "")
UA = "Mozilla/5.0"


def http_json(url, timeout=30, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            time.sleep(0.8 * (i + 1))
    return None


def rpc(method, params, retries=4, timeout=45):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    for i in range(retries):
        try:
            req = urllib.request.Request(RPC, data=body, headers={
                "Content-Type": "application/json", "User-Agent": "enrich/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = json.load(r)
            if "result" in out:
                return out["result"]
        except Exception:
            pass
        time.sleep(0.8 * (i + 1))
    return None


def count_txs(addr, cap_pages=30):
    """Nombre total de tx d'un compte, pagine jusqu'a la genese.

    Renvoie (n, genese_atteinte). genese_atteinte=False => plafond de pagination
    touche, le compte est TROP ACTIF pour etre compte ici (donc pas un token mort).
    """
    n, before, pages = 0, None, 0
    first_ts = None
    while pages < cap_pages:
        p = {"limit": 1000}
        if before:
            p["before"] = before
        res = rpc("getSignaturesForAddress", [addr, p])
        if res is None:
            return n, False, first_ts
        n += len(res)
        pages += 1
        if res:
            before = res[-1]["signature"]
            first_ts = res[-1].get("blockTime")
        if len(res) < 1000:          # page incomplete = genese atteinte
            return n, True, first_ts
    return n, False, first_ts


def enrich(mint):
    c = http_json(f"https://frontend-api-v3.pump.fun/coins/{mint}")
    if not c or "mint" not in c:
        return {"mint": mint, "pump_api": None}
    bc = c.get("bonding_curve")
    ntx, genese, first_ts = (None, None, None)
    if bc:
        ntx, genese, first_ts = count_txs(bc)
    return {
        "mint": mint,
        "name": c.get("name"), "symbol": c.get("symbol"),
        "creator": c.get("creator"),
        "created_timestamp": c.get("created_timestamp"),
        "created_utc": dt.datetime.fromtimestamp(
            c["created_timestamp"] / 1000, dt.timezone.utc).isoformat().replace("+00:00", "Z")
        if c.get("created_timestamp") else None,
        "bonding_curve": bc,
        "complete": c.get("complete"),
        "raydium_pool": c.get("raydium_pool"),
        "koth": bool(c.get("king_of_the_hill_timestamp")),
        "reply_count": c.get("reply_count"),
        "usd_market_cap": c.get("usd_market_cap"),
        "ath_market_cap_api": c.get("ath_market_cap"),
        "ath_ts_api": c.get("ath_market_cap_timestamp"),
        "bc_tx_total": ntx,
        "bc_tx_genese_atteinte": genese,
        "bc_first_tx_ts": first_ts,
    }


if __name__ == "__main__":
    mints = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(enrich, mints))
    json.dump(rows, open(sys.argv[2], "w"), indent=1)
    print("enrichis:", len(rows), file=sys.stderr)
