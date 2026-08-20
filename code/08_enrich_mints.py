#!/usr/bin/env python3
"""Enrich the harvested mints through the pump API, and measure their on-chain
activity.

Two independent measurements of performance:
  - pump API: complete (the curve finished, so it moved to Raydium),
    king_of_the_hill, reply_count, current usd_market_cap. Note that the API's
    ath_market_cap is a RECENT maximum, not the historical 2024 high; this was
    checked, every ath_market_cap_timestamp falls in 2026.
  - on-chain: the TOTAL number of transactions on the bonding_curve account,
    paginated ALL THE WAY TO GENESIS, meaning until a page comes back
    incomplete. That is the token's real activity over its whole life, and it
    says whether the token has enough buyers to be analysable at all.

CLIENT
------
The on-chain count goes through the single Helius client (rpc_client.py): the
keys come from the environment, $HELIUS_API_KEYS or the uncommitted .env, see
settings.py, and a network failure RAISES instead of disguising itself as an
"account too active" (docs/PITFALLS.md, rule 2). The pump.fun frontend API is
NOT Helius: it keeps a small local GET, which also raises once its attempts are
exhausted.
"""
from __future__ import annotations
import datetime as dt, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client

UA = "Mozilla/5.0"


class PumpError(RuntimeError):
    """A failure of the pump.fun frontend API, a non-Helius endpoint. Raised, never
    returned as None: a network outage must interrupt the measurement, not empty
    it in silence.
    """


def pump_get(url: str, timeout: int = 30, retries: int = 4) -> Any:
    """JSON GET against the pump.fun frontend, a NON-Helius endpoint outside
    rpc_client. Returns the decoded JSON, or RAISES PumpError once the attempts
    are exhausted.
    """
    last: Optional[str] = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001  (transport / decode)
            last = repr(e)
            time.sleep(0.8 * (i + 1))
    raise PumpError("pump GET a echoue apres %d essais: %s" % (retries, last))


def count_txs(addr: str, cap_pages: int = 30) -> tuple[int, bool, Optional[int]]:
    """The total number of transactions on an account, paginated to genesis.

    Returns (n, genesis_reached, first_ts). genesis_reached=False means the
    pagination cap was hit and the account is TOO ACTIVE to be counted here, so
    it is not a dead token. A network failure RAISES (rpc_client) instead of
    passing itself off as that cap.
    """
    n, before, pages = 0, None, 0
    first_ts: Optional[int] = None
    while pages < cap_pages:
        res = rpc_client.sigs(addr, 1000, before)
        n += len(res)
        pages += 1
        if res:
            before = res[-1]["signature"]
            first_ts = res[-1].get("blockTime")
        if len(res) < 1000:          # page incomplete = genese atteinte
            return n, True, first_ts
    return n, False, first_ts


def enrich(mint: str) -> dict:
    c = pump_get(f"https://frontend-api-v3.pump.fun/coins/{mint}")
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
    if len(sys.argv) < 2:
        raise SystemExit(
            "usage: python3 code/08_enrich_mints.py <harvest_*.json>\n"
            "  le fichier de mints est produit par 07_harvest_creations.py")
    mints = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(enrich, mints))
    json.dump(rows, open(sys.argv[2], "w"), indent=1)
    print("enrichis:", len(rows), file=sys.stderr)
