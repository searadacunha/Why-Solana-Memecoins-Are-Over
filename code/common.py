#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Primitives partagees du volet << cout pour l'acheteur >> (tableaux T1 a T5).

SOURCE PAR DEFAUT : data/floor_capture_public.jsonl.gz, publie avec le depot.
Aucun reseau, aucune cle, aucun chemin absolu. Le corpus brut non publie
(645 fichiers, 171 Mo) reste utilisable en posant $PUMP_PRIVATE_ROOT ; les deux
chemins de lecture donnent les memes tableaux (cf. code/README.md, section
"Reproductibilite"), le corpus publie etant simplement arrondi (6 chiffres
significatifs sur `sol`, 8 sur `tokens`/`price`).

Conventions d'unites (VERIFIEES) :
  - captures : champ `price` et `sol/tokens` = SOL par token.
  - captures : champ `detect_mc`             = USD.
  - GeckoTerminal OHLCV : prix               = USD par token.
  => tout ratio qui melange les deux SANS conversion est faux d'un facteur
     egal au prix du SOL (~73 USD sur la fenetre). Voir sol_usd().
"""
import bisect
import glob
import gzip
import json
import os
import statistics as st
from collections import defaultdict

import redact
import settings

ROOT = settings.ROOT
DATA = settings.DATA
DOCS = settings.DOCS

# Socle de features par token (populations A / B / C), publie dans data/.
SOCLE = settings.data("dataset_socle.json")

# --- parametres de simulation (identiques au socle canonique reconcilie) -----
MIN_SOL_PRICE = 0.3     # taille mini d'un swap pour compter dans le prix robuste
DEPTH_MIN_SOL = 0.05    # taille mini d'un ordre pour compter dans le carnet
POS_SOL = 0.5           # taille de la position simulee
FEE_SIDE = 0.01         # frais par jambe
SLIP_SIDE = 0.02        # slippage adverse par jambe
FEE_IN = (1 + SLIP_SIDE) * (1 + FEE_SIDE)
FEE_OUT = (1 - SLIP_SIDE) * (1 - FEE_SIDE)
DRAG = 1 - FEE_OUT / FEE_IN          # = 5.8241 % aller-retour
MIN_USEFUL = 120        # duree utile minimale d'une capture
CLUSTER_GAP = 1800      # 30 min : deux lancements separes de plus = 2 clusters


# --------------------------------------------------------------- captures ---
def _raw_captures():
    """Itere les captures brutes + (n_fichiers_source, n_vides_deja_ecartees).

    Deux sources possibles, interchangeables :
      1. data/floor_capture_public.jsonl.gz  (defaut, publie)
      2. $PUMP_PRIVATE_ROOT/state/floor_capture/*.json  (corpus brut)
    Le corpus publie a deja perdu les 352 captures sans aucun swap ; on relit
    leur nombre dans data/MANIFEST.json pour que les comptes de rejets affiches
    soient identiques quelle que soit la source.
    """
    priv = settings.private_root()
    if priv:
        capdir = os.path.join(priv, "state", "floor_capture")
        files = sorted(glob.glob(os.path.join(capdir, "*.json")))
        if not files:
            raise SystemExit("aucune capture dans %s" % capdir)
        def gen():
            for fp in files:
                try:
                    yield json.load(open(fp))
                except Exception:
                    yield None
        return gen(), len(files), 0

    path = settings.PUBLIC_CORPUS
    if not os.path.exists(path):
        raise SystemExit(
            "corpus absent : %s\n"
            "Il est publie avec le depot ; sinon le reconstruire avec\n"
            "  python3 code/make_public_data.py --private /chemin/pump_bundle_detector"
            % os.path.relpath(path, ROOT))
    n_src, n_empty = 0, 0
    mf = settings.data("MANIFEST.json")
    if os.path.exists(mf):
        m = json.load(open(mf))
        n_src = m.get("n_fichiers_source", 0)
        n_empty = m.get("n_captures_vides_ecartees", 0)

    def gen():
        with gzip.open(path, "rt") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
    return gen(), n_src, n_empty


def load_captures(verbose=False):
    """Charge les captures exploitables.

    Filtres (union des rejets des deux socles, cf. merge.py X11) :
      capture vide ; span des swaps < 120 s ; (dernier swap - created) < 120 s ;
      aucun buy ; aucun swap >= 0.3 SOL.
    Retourne (liste, dict_rejets, n_fichiers).
    """
    stream, n_files, n_empty = _raw_captures()
    kept, rej = [], defaultdict(int)
    if n_empty:
        rej["capture_vide"] += n_empty
    for d in stream:
        if d is None:
            rej["json_illisible"] += 1
            continue
        raw = d.get("swaps") or []
        if not raw:
            rej["capture_vide"] += 1
            continue
        cl = []
        for s in raw:
            tok = s.get("tokens") or 0.0
            sol = s.get("sol") or 0.0
            ts = s.get("ts")
            if ts is None or tok <= 0 or sol <= 0:
                continue
            if s.get("side") not in ("buy", "sell"):
                continue
            cl.append({"ts": int(ts), "side": s["side"], "sol": float(sol),
                       "tokens": float(tok), "trader": s.get("trader"),
                       "p": float(sol) / float(tok)})
        if not cl:
            rej["aucun_swap_exploitable"] += 1
            continue
        cl.sort(key=lambda x: x["ts"])
        created = d.get("created") or cl[0]["ts"]
        if cl[-1]["ts"] - cl[0]["ts"] < MIN_USEFUL:
            rej["span_swaps_lt_2min"] += 1
            continue
        if cl[-1]["ts"] - created < MIN_USEFUL:
            rej["duree_depuis_created_lt_2min"] += 1
            continue
        if not any(x["side"] == "buy" for x in cl):
            rej["aucun_buy"] += 1
            continue
        if not any(x["sol"] >= MIN_SOL_PRICE for x in cl):
            rej["aucun_swap_ge_0.3sol"] += 1
            continue
        d["_sw"] = cl
        d["_created"] = created
        kept.append(d)
    kept.sort(key=lambda d: (d["_created"], d["mint"]))
    n_files = n_files or (len(kept) + sum(rej.values()))
    # tri des cles : le dict de rejets finit imprime dans les tableaux publies,
    # et l'ordre d'insertion dependait de la source. Sortie reproductible.
    rej = dict(sorted(rej.items()))
    if verbose:
        print(f"fichiers={n_files}  exploitables={len(kept)}  rejets={rej}")
    return kept, rej, n_files


# Nom de la source cite dans les notes de bas de tableau.
def source_label():
    return ("$PUMP_PRIVATE_ROOT/state/floor_capture/*.json"
            if settings.private_root() else "data/floor_capture_public.jsonl.gz")


def clusters(caps, gap=CLUSTER_GAP):
    """Numerote les captures en clusters (gap > 30 min sur `created`)."""
    out, cid, prev = {}, 0, None
    for d in sorted(caps, key=lambda x: x["_created"]):
        if prev is not None and d["_created"] - prev > gap:
            cid += 1
        out[d["mint"]] = cid
        prev = d["_created"]
    return out


def robust_price(sw, t0, t1, min_sol=MIN_SOL_PRICE):
    """Prix robuste = mediane des prix des swaps >= min_sol sur [t0, t1).
    Aucune interpolation : None se propage."""
    p = [s["p"] for s in sw if t0 <= s["ts"] < t1 and s["sol"] >= min_sol]
    return st.median(p) if p else None


# --------------------------------------------------------------- SOL / USD --
_SOL = None


def sol_usd(ts=None):
    """Prix du SOL en USD (serie horaire GeckoTerminal, pool SOL/USDC Raydium).

    Fichier data/sol_usd_hourly.json produit par code/fetch_sol_usd.py.
    Sans argument : retourne (mediane, n, ts_min, ts_max).
    """
    global _SOL
    if _SOL is None:
        p = os.path.join(DATA, "sol_usd_hourly.json")
        if not os.path.exists(p):
            raise SystemExit("data/sol_usd_hourly.json absent : lancer code/fetch_sol_usd.py")
        j = json.load(open(p))
        _SOL = sorted((int(t), float(c)) for t, c in j["hourly_close"])
    if ts is None:
        v = [c for _, c in _SOL]
        return st.median(v), len(_SOL), _SOL[0][0], _SOL[-1][0]
    keys = [t for t, _ in _SOL]
    i = bisect.bisect_right(keys, ts) - 1
    i = max(0, min(i, len(_SOL) - 1))
    return _SOL[i][1]


# --------------------------------------------------------------- stats ------
def med(v):
    return st.median(v) if v else None


def q(v, p):
    if not v:
        return None
    s = sorted(v)
    i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
    return s[i]


def boot_ci_median(v, B=4000, seed=12345):
    """IC95 bootstrap de la mediane (percentile). Retourne (lo, hi)."""
    import random
    if len(v) < 5:
        return (None, None)
    rnd = random.Random(seed)
    n = len(v)
    out = []
    for _ in range(B):
        out.append(st.median([v[rnd.randrange(n)] for _ in range(n)]))
    out.sort()
    return out[int(0.025 * B)], out[int(0.975 * B)]


def wilson(k, n, z=1.96):
    """IC95 de Wilson pour une proportion."""
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def load_socle():
    return json.load(open(SOCLE))


def write_table(name, header, rows, notes=()):
    """Ecrit un tableau Markdown dans docs/tables/NAME.md et le renvoie."""
    d = os.path.join(DOCS, "tables")
    os.makedirs(d, exist_ok=True)
    w = [max(len(str(header[i])), *(len(str(r[i])) for r in rows)) if rows
         else len(str(header[i])) for i in range(len(header))]
    L = ["| " + " | ".join(str(header[i]).ljust(w[i]) for i in range(len(header))) + " |",
         "|" + "|".join("-" * (w[i] + 2) for i in range(len(header))) + "|"]
    for r in rows:
        L.append("| " + " | ".join(str(r[i]).ljust(w[i]) for i in range(len(header))) + " |")
    txt = "\n".join(L)
    if notes:
        txt += "\n\n" + "\n".join(notes)
    open(os.path.join(d, name + ".md"), "w").write(redact.scrub_text(txt) + "\n")
    return txt


def dump_json(obj, path, **kw):
    """Unique point d'ecriture JSON des mesures.

    Passe par redact.scrub : la pseudonymisation des quelques identifiants a
    prefixe vanity injurieux est appliquee A L'ECRITURE, pas apres coup. Une
    re-execution depuis le cache reseau brut ne peut donc pas la defaire.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    kw.setdefault("indent", 1)
    with open(path, "w") as f:
        json.dump(redact.scrub(obj), f, **kw)
    return path
