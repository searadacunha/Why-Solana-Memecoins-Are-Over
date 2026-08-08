#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r1lib.py -- adapter pour la verification du "regime 1" (financement de flottes
de wallets vierges via dispatchers, avant juin 2026).

Le client robuste que ce module portait est devenu rpc_client.py, le client
unique du depot : meme rotation de cles, meme cooldown 429, meme regle "on LEVE
sur echec, jamais de page vide silencieuse". Ce fichier n'en garde que :
  - son cache propre (data/cache_r1/), separe de data/cache/ ;
  - l'ecriture atomique + pseudonymisee des sorties (save) ;
  - les constantes pump.fun utilisees par r1_*.

Cles : lues dans l'environnement ($HELIUS_API_KEYS, ou .env non versionne a la
racine du depot -- voir settings.py). Lecture seule.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

import rpc_client
import settings
from rpc_client import (  # noqa: F401  (re-exported for r1_* importers)
    HeliusError,
    STATS,
    block,
    enhanced,
    rpc,
    tx,
    walk_sigs,
)

DATA = settings.DATA
CACHE = settings.CACHE_R1
os.makedirs(CACHE, exist_ok=True)


def sig_page(addr: str, limit: int = 1000, before: Optional[str] = None) -> list[Any]:
    """Une page de signatures ; leve si l'appel renvoie null (== rpc_client.sigs)."""
    return rpc_client.sigs(addr, limit, before)


def cached(name: str, fn: Any) -> Any:
    """cache disque : data/cache_r1/<name>.json (ecriture atomique)."""
    return rpc_client.cached(name, fn, CACHE)


def save(name: str, obj: Any) -> str:
    """Ecriture atomique + pseudonymisation a l'ecriture (voir redact.py)."""
    import redact
    p = os.path.join(DATA, name)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(redact.scrub(obj), f, indent=1)
    os.replace(tmp, p)
    sys.stderr.write("ecrit %s\n" % os.path.relpath(p, settings.ROOT))
    return p


# ---------------------------------------------------------------- pump.fun
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_AMM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
SYS_PROGRAM = "11111111111111111111111111111111"
LAMPORT = 1e-9
# minimum de rente d'un compte systeme vide (0.00089088 SOL) : en dessous, un
# wallet ne peut meme pas exister durablement, a fortiori signer un achat.
RENT_MIN_SOL = 0.00089088
# frais de base d'une transaction Solana : 5000 lamports.
TX_FEE_SOL = 0.000005
