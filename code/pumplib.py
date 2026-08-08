#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pumplib.py — bibliotheque commune. Stdlib uniquement (json, gzip, math,
bisect, statistics). Aucune dependance externe, aucun reseau, aucune cle.

Conventions partagees par toutes les mesures :

  t0            = `created`, l'horodatage de creation du token (secondes UNIX).
  swap          = {ts, side, trader, sol, tokens, price, src, progs[, sig]}
  prix execute  = sol / tokens  (ce que l'acheteur paie reellement, frais de
                  routeur inclus dans `sol`). On ne se sert de `price` (prix de
                  pool) que pour controle : les deux donnent le meme resultat a
                  la 3e decimale (voir m2).
  MC en SOL     = prix * supply. La supply pump.fun est constante a 1e9.
  MC de lancement = 27.96 SOL : constante de la courbe de bonding pump.fun
                  (reserve virtuelle initiale). C'est le prix auquel le token
                  demarre, avant tout achat. Verifiable hors de ce depot.

NIVEAUX DE PREUVE utilises dans les sorties :
  [MESURE]      chiffre recalcule par le script a partir de data/.
  [INFERE]      deduction a partir de mesures, explicitement signalee.
  [NON ETABLI]  hypothese, jamais chiffree comme un fait.
"""

import bisect
import datetime as _dt
import gzip
import json
import os
import statistics


def utc(ts, fmt="%Y-%m-%d"):
    """Horodatage UNIX -> chaine UTC. Centralise ici pour que toutes les
    mesures partagent exactement la meme convention de jour."""
    return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).strftime(fmt)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))

# Constante de la courbe pump.fun : market cap au lancement, en SOL.
LAUNCH_MC_SOL = 27.96
PUMP_SUPPLY = 1e9


# ------------------------------------------------------------------ chargement
def load_captures(path=None):
    """Charge le corpus de capture. Accepte .jsonl.gz ou .jsonl."""
    if path is None:
        path = os.path.join(DATA, "floor_capture_public.jsonl.gz")
    op = gzip.open if path.endswith(".gz") else open
    out = []
    with op(path, "rt") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    out.sort(key=lambda d: (d["created"], d["mint"]))
    return out


def load_json(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def clean_swaps(d):
    """Swaps exploitables, tries. Meme filtre partout : sol>0, tokens>0,
    side dans {buy,sell}. Ajoute le prix execute `p`."""
    out = []
    for s in d.get("swaps") or []:
        tok = s.get("tokens") or 0.0
        sol = s.get("sol") or 0.0
        if s.get("ts") is None or tok <= 0 or sol <= 0:
            continue
        if s.get("side") not in ("buy", "sell"):
            continue
        out.append({"ts": int(s["ts"]), "side": s["side"], "sol": float(sol),
                    "tokens": float(tok), "p": float(sol) / float(tok),
                    "price": s.get("price"), "src": s.get("src"),
                    "progs": s.get("progs") or [], "trader": s.get("trader")})
    out.sort(key=lambda x: x["ts"])
    return out


MIN_SOL_PRICE = 0.3   # taille minimale d'un swap pour compter dans un prix
BUCKET = 30           # granularite de la grille de prix, en secondes


def robust_series(sw, bucket=BUCKET, min_sol=MIN_SOL_PRICE, t0=None):
    """Serie de prix ROBUSTE : pour chaque bucket de `bucket` secondes, la
    mediane des prix executes des swaps d'au moins `min_sol`.

    Pourquoi pas simplement max(prix) : les swaps de poussiere (0,002 SOL) ont
    un prix implicite domine par les arrondis d'unites et produisent des
    valeurs aberrantes de plusieurs ordres de grandeur (mesure : le max brut
    donne une MC de 8,9e8 SOL, physiquement impossible). La mediane par bucket
    sur les swaps >= 0,3 SOL elimine l'artefact sans choisir a la main.
    Cette definition est celle du moteur d'aller-retour (M5) : les deux
    mesures partagent donc exactement la meme notion de prix.
    Retourne [(t_debut_bucket, prix), ...] tries."""
    big = [s for s in sw if s["sol"] >= min_sol]
    if not big:
        return []
    base = big[0]["ts"] if t0 is None else t0
    buckets = {}
    for s in big:
        k = (s["ts"] - base) // bucket
        buckets.setdefault(k, []).append(s["p"])
    return [(base + k * bucket, statistics.median(v))
            for k, v in sorted(buckets.items())]


def clusters(caps, gap_s=1800):
    """Assigne un id de grappe temporelle. Deux tokens crees a moins de
    `gap_s` l'un de l'autre sont dans la meme grappe. Sert d'unite de
    re-echantillonnage : les tokens d'une meme grappe partagent le regime de
    marche, les compter comme independants surestime la puissance."""
    cid, prev, out = 0, None, {}
    for d in sorted(caps, key=lambda x: x["created"]):
        c = d["created"]
        if prev is None or (c - prev) > gap_s:
            cid += 1
        prev = c
        out[d["mint"]] = cid
    return out


# ------------------------------------------------------------------ stats
# median / quantile / wilson are defined once in statlib.py and re-exported here
# so the m-series can keep calling P.median / P.wilson unchanged.
from statlib import median, quantile, wilson  # noqa: E402,F401


def bootstrap_median_ci(xs, n_boot=2000, seed=12345, alpha=0.05):
    """IC de la mediane par bootstrap. Generateur congruentiel explicite pour
    que le resultat soit identique sur toute machine et toute version de
    Python (random.seed ne le garantit pas entre versions)."""
    xs = [x for x in xs if x is not None]
    if len(xs) < 3:
        return (None, None)
    n = len(xs)
    state = seed
    meds = []
    for _ in range(n_boot):
        s = []
        for _ in range(n):
            state = (1103515245 * state + 12345) % (1 << 31)
            s.append(xs[state % n])
        s.sort()
        meds.append(s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2]))
    meds.sort()
    lo = meds[int(alpha / 2 * (n_boot - 1))]
    hi = meds[int((1 - alpha / 2) * (n_boot - 1))]
    return (lo, hi)


def cluster_bootstrap_mean_ci(values_by_cluster, n_boot=2000, seed=999, alpha=0.05):
    """IC en re-echantillonnant les GRAPPES, pas les tokens. Les tokens d'une
    meme grappe partagent le regime de marche : les traiter comme independants
    surestimerait la precision.

    L'estimateur re-echantillonne est la MOYENNE DES MOYENNES DE GRAPPE, le
    meme que le point estime rapporte a cote. Re-echantillonner les grappes
    puis moyenner les tokens mis en commun donnerait un autre estimateur (une
    moyenne ponderee par la taille des grappes) et produirait un IC qui ne
    contient pas son propre point estime."""
    keys = sorted(values_by_cluster)
    if len(keys) < 3:
        return (None, None)
    cmeans = {k: sum(v) / len(v) for k, v in values_by_cluster.items() if v}
    keys = [k for k in keys if k in cmeans]
    state = seed
    out = []
    for _ in range(n_boot):
        acc = []
        for _ in range(len(keys)):
            state = (1103515245 * state + 12345) % (1 << 31)
            acc.append(cmeans[keys[state % len(keys)]])
        out.append(sum(acc) / len(acc))
    out.sort()
    return (out[int(alpha / 2 * (len(out) - 1))],
            out[int((1 - alpha / 2) * (len(out) - 1))])


# ------------------------------------------------------------------ affichage
def head(title, level=None):
    bar = "=" * 78
    print(bar)
    print(title + ("   [%s]" % level if level else ""))
    print(bar)


def kv(label, value, unit="", n=None, note=""):
    s = "  %-52s %s%s" % (label, value, unit)
    if n is not None:
        s += "   (n=%s)" % n
    if note:
        s += "   %s" % note
    print(s)


def emit(obj, path):
    """Ecrit le resultat machine-lisible a cote du texte."""
    import redact
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(redact.scrub(obj), f, indent=1, sort_keys=True)
    print("\n  -> %s" % os.path.relpath(path, os.path.dirname(HERE)))
