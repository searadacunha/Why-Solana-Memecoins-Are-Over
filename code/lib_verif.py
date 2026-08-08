#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lib_verif.py - socle commun des scripts de verification on-chain (v0*).

Lecture seule sur les sources. Aucune ecriture hors de data/.

Le client reseau est desormais rpc_client.py (un seul client pour tout le
depot, qui LEVE sur echec au lieu de renvoyer une valeur vide). Ce module ne
garde que le cache local (data/cache/), les chargeurs de sources locales et les
quelques helpers propres aux scripts v0*.

Entrees :
  - corpus de captures  : data/floor_capture_public.jsonl.gz (publie), ou
                          $PUMP_PRIVATE_ROOT/state/floor_capture/ si monte.
  - socle de features   : data/dataset_socle.json (publie).
  - geometrie de la fenetre de creation : cache derive de Helius, non publie
                          (5,5 Mo, 913 fichiers) ; requiert $PUMP_PRIVATE_ROOT.
                          Les sorties qui en derivent SONT publiees dans data/.
  - Helius              : cles lues dans l'environnement (voir settings.py).
                          Aucune cle n'est ecrite dans data/ ni dans une sortie.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import statistics as st
from typing import Any, Optional

import rpc_client
import settings

OUT = settings.ROOT
DATA = settings.DATA
CACHE = settings.CACHE
os.makedirs(CACHE, exist_ok=True)

SOCLE = settings.data("dataset_socle.json")


def _snipe_cache_dir() -> str:
    priv = settings.private_root(required=True)
    return os.path.join(priv, "analysis_forensic", "ident_age_stack", "cache")


# ---------------------------------------------------------------- Helius
def rpc(method: str, params: list[Any]) -> Any:
    """JSON-RPC Helius via le client unique. Tolere -32601/-32602 (methode
    absente / parametres invalides) en renvoyant None, comme avant ; toute
    autre defaillance leve HeliusError plutot que de se deguiser en resultat
    vide."""
    return rpc_client.rpc(method, params, tolerate_codes=(-32601, -32602))


def cached(name: str, fn: Any) -> Any:
    """cache disque : data/cache/<name>.json (ecriture atomique)."""
    return rpc_client.cached(name, fn, CACHE)


def get_tx(sig: str) -> Any:
    return cached("tx_" + sig[:24], lambda: rpc(
        "getTransaction", [sig, {"encoding": "jsonParsed",
                                 "maxSupportedTransactionVersion": 0}]))


def get_sigs(addr: str, limit: int = 1000, before: Optional[str] = None) -> Any:
    p: dict[str, Any] = {"limit": limit}
    if before:
        p["before"] = before
    return rpc("getSignaturesForAddress", [addr, p])


def first_signature(addr: str) -> tuple[Optional[str], Optional[int], int, bool]:
    """remonte a la signature la plus ancienne d'une adresse (pagination arriere).
    Retourne (sig, blockTime, n_pages, censure) ; censure=True si >CAP pages."""
    CAP = 40           # 40 * 1000 = 40 000 signatures max
    before, last, n = None, None, 0
    while n < CAP:
        r = get_sigs(addr, 1000, before)
        n += 1
        if not r:
            break
        last = r[-1]
        if len(r) < 1000:
            return last["signature"], last.get("blockTime"), n, False
        before = last["signature"]
    return (last or {}).get("signature"), (last or {}).get("blockTime"), n, True


# ---------------------------------------------------------------- sources locales
def load_floor() -> dict[str, Any]:
    """Toutes les captures non vides, indexees par mint (lecture seule).

    Source publiee par defaut ; corpus brut si $PUMP_PRIVATE_ROOT est monte.
    """
    priv = settings.private_root()
    out: dict[str, Any] = {}
    if priv:
        for f in sorted(glob.glob(os.path.join(priv, "state", "floor_capture", "*.json"))):
            d = json.load(open(f))
            if d.get("swaps"):
                out[d["mint"]] = d
        return out
    with gzip.open(settings.PUBLIC_CORPUS, "rt") as fh:
        for line in fh:
            line = line.strip()
            if line:
                d = json.loads(line)
                out[d["mint"]] = d
    return out


def load_snipe() -> dict[str, Any]:
    """cache snipe_*.json : geometrie de la fenetre de creation (<=+12s).

    Seule entree de ce dossier qui n'est pas publiee : 913 fichiers derives de
    Helius, conserves tels quels pour ne pas re-interroger l'API a chaque
    execution. Les SORTIES qui en derivent (data/v0*.json) sont publiees, donc
    v03 a v08 restent verifiables sans elle.
    """
    d0 = _snipe_cache_dir()
    out: dict[str, Any] = {}
    for f in sorted(glob.glob(os.path.join(d0, "snipe_*.json"))):
        d = json.load(open(f))
        out[d["mint"]] = d
    if not out:
        raise SystemExit("cache snipe_*.json introuvable dans %s" % d0)
    return out


def load_socle() -> Any:
    return json.load(open(SOCLE))


def med(x: list[Any]) -> Optional[float]:
    from statlib import median
    return median(x)


def cv(x: list[Any]) -> float:
    if len(x) < 2:
        return 0.0
    m = st.mean(x)
    return (st.pstdev(x) / m) if m else 0.0


def save(name: str, obj: Any) -> None:
    """Ecriture unique des sorties v0*. La pseudonymisation (redact) est
    appliquee ICI : une re-execution depuis le cache reseau brut, qui contient
    les identifiants d'origine, ne peut pas la defaire."""
    import redact
    p = f"{DATA}/{name}"
    json.dump(redact.scrub(obj), open(p, "w"), indent=1, default=str)
    print(f"  -> {os.path.relpath(p, settings.ROOT)}")
