#!/usr/bin/env python3
"""lib_verif.py - socle commun des scripts de verification on-chain (v0*).

Lecture seule sur les sources. Aucune ecriture hors de data/.

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
import gzip, json, os, glob, time, urllib.request, urllib.error, statistics as st

import settings

OUT = settings.ROOT
DATA = settings.DATA
CACHE = settings.CACHE
os.makedirs(CACHE, exist_ok=True)

SOCLE = settings.data("dataset_socle.json")


def _snipe_cache_dir():
    priv = settings.private_root(required=True)
    return os.path.join(priv, "analysis_forensic", "ident_age_stack", "cache")


# ---------------------------------------------------------------- Helius
KEYS = settings.helius_keys()
_ki = [0]

def rpc(method, params, tries=5, timeout=120):
    """appel JSON-RPC Helius avec rotation de cles et backoff."""
    global KEYS
    if not KEYS:
        KEYS = settings.require_helius()
    last = None
    for a in range(tries):
        k = KEYS[_ki[0] % len(KEYS)]
        _ki[0] += 1
        url = f"https://mainnet.helius-rpc.com/?api-key={k}"
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                           "params": params}).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
            if "error" in d:
                last = d["error"]
                if d["error"].get("code") in (-32601, -32602):
                    return None
                time.sleep(1.0 + a)
                continue
            return d.get("result")
        except Exception as e:
            last = e
            time.sleep(1.0 + 1.5 * a)
    raise RuntimeError(f"rpc {method} echec: {last}")

def cached(name, fn):
    """cache disque simple : data/cache/<name>.json"""
    p = f"{CACHE}/{name}.json"
    if os.path.exists(p):
        return json.load(open(p))
    v = fn()
    json.dump(v, open(p, "w"))
    return v

def get_tx(sig):
    return cached("tx_" + sig[:24], lambda: rpc(
        "getTransaction", [sig, {"encoding": "jsonParsed",
                                 "maxSupportedTransactionVersion": 0}]))

def get_sigs(addr, limit=1000, before=None):
    p = {"limit": limit}
    if before:
        p["before"] = before
    return rpc("getSignaturesForAddress", [addr, p])

def first_signature(addr):
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
def load_floor():
    """Toutes les captures non vides, indexees par mint (lecture seule).

    Source publiee par defaut ; corpus brut si $PUMP_PRIVATE_ROOT est monte.
    """
    priv = settings.private_root()
    out = {}
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

def load_snipe():
    """cache snipe_*.json : geometrie de la fenetre de creation (<=+12s).

    Seule entree de ce dossier qui n'est pas publiee : 913 fichiers derives de
    Helius, conserves tels quels pour ne pas re-interroger l'API a chaque
    execution. Les SORTIES qui en derivent (data/v0*.json) sont publiees, donc
    v03 a v08 restent verifiables sans elle.
    """
    d0 = _snipe_cache_dir()
    out = {}
    for f in sorted(glob.glob(os.path.join(d0, "snipe_*.json"))):
        d = json.load(open(f))
        out[d["mint"]] = d
    if not out:
        raise SystemExit("cache snipe_*.json introuvable dans %s" % d0)
    return out

def load_socle():
    return json.load(open(SOCLE))

def med(x):
    return st.median(x) if x else None

def cv(x):
    if len(x) < 2:
        return 0.0
    m = st.mean(x)
    return (st.pstdev(x) / m) if m else 0.0

def save(name, obj):
    """Ecriture unique des sorties v0*. La pseudonymisation (redact) est
    appliquee ICI : une re-execution depuis le cache reseau brut, qui contient
    les identifiants d'origine, ne peut pas la defaire."""
    import redact
    p = f"{DATA}/{name}"
    json.dump(redact.scrub(obj), open(p, "w"), indent=1, default=str)
    print(f"  -> {os.path.relpath(p, settings.ROOT)}")
