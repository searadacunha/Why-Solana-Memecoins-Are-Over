#!/usr/bin/env python3
"""Enrichit les mints recoltes via l'API pump + mesure d'activite on-chain.

Deux mesures independantes de la performance :
  - pump API : complete (= courbe terminee -> Raydium), king_of_the_hill, reply_count,
    usd_market_cap actuel. NB: ath_market_cap de l'API est un maximum RECENT, pas l'ATH
    historique de 2024 (verifie : tous les ath_market_cap_timestamp tombent en 2026).
  - on-chain : nombre TOTAL de transactions sur le compte bonding_curve, pagine
    JUSQU'A LA GENESE (une page incomplete). C'est la mesure d'activite reelle du token
    sur toute sa vie, et elle dit si le token a assez d'acheteurs pour etre analysable.

CLIENT
------
Le comptage on-chain passe par le client Helius unique (rpc_client.py) : les clés
viennent de l'environnement ($HELIUS_API_KEYS, ou .env non versionné, voir
settings.py) et **un échec réseau LÈVE** au lieu de se déguiser en « compte trop
actif » (docs/PITFALLS.md, règle n°2). L'API frontend pump.fun n'est PAS Helius :
elle garde un petit GET local, qui lève lui aussi à l'épuisement des essais.
"""
from __future__ import annotations
import datetime as dt, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpc_client  # noqa: E402

UA = "Mozilla/5.0"


class PumpError(RuntimeError):
    """Échec de l'API frontend pump.fun (endpoint non-Helius). Levée, jamais rendue
    en None : une panne réseau doit interrompre la mesure, pas la vider en silence."""


def pump_get(url: str, timeout: int = 30, retries: int = 4) -> Any:
    """GET JSON sur le frontend pump.fun (endpoint NON-Helius, hors rpc_client).
    Retourne le JSON décodé, ou LÈVE PumpError une fois les essais épuisés."""
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
    """Nombre total de tx d'un compte, pagine jusqu'a la genese.

    Renvoie (n, genese_atteinte, first_ts). genese_atteinte=False => plafond de
    pagination touche, le compte est TROP ACTIF pour etre compte ici (donc pas un
    token mort). Un echec reseau LEVE (rpc_client) au lieu de se faire passer pour
    ce plafond.
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
