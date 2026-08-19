#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_public_data.py : construit data/ a partir du corpus prive (lecture seule).

Publie pour rendre la reduction auditable : il documente ce qui a ete garde,
jete et arrondi entre le corpus de travail et le corpus publie. Il n'est pas
necessaire pour reproduire les mesures, data/ est deja dans le depot. Il sert
a verifier que data/ derive bien du corpus prive, et a mettre au format un
autre corpus pour qui en possede un.

Source (jamais publiee telle quelle, lecture seule) :
    <PRIVATE>/state/floor_capture/*.json      645 fichiers, 171 Mo
    <PRIVATE>/analysis_fullsnipe/socle/dataset.json
    <PRIVATE>/analysis_supervision/horizon.json
    <PRIVATE>/state/snipe_log.json

Sortie (publiee) :
    data/floor_capture_public.jsonl.gz
    data/dataset_socle.json
    data/horizon.json
    data/snipe_log.json
    data/sample/floor_capture_sample.jsonl
    data/MANIFEST.json

Transformations appliquees, exhaustivement :
  1. Les 352 fichiers sans aucun swap sont ecartes (captures vides = pannes du
     collecteur, pas un phenomene de marche). 293 fichiers conserves.
  2. Champ `fees` (liste de wallets payeurs de frais) supprime : non utilise par
     les mesures publiees, ~40 Mo.
  3. Champ `sig` (signature de transaction) conserve pour les seuls swaps a
     t <= created + 30 s, ceux qui servent d'ancre de verification on-chain.
     Supprime au-dela (~500 000 signatures inutiles).
  4. `sol` arrondi a 6 chiffres significatifs, `tokens` et `price` a 8. Effet
     mesure sur les resultats : voir m5_roundtrip_policies.py --check-rounding
     (ecart max cellule a cellule < 1e-6 en PnL relatif).
  5. Aucune anonymisation d'adresse. Mints, wallets et signatures sont des
     donnees publiques Solana, les masquer rendrait le dossier inverifiable.
     Choix assume : le dossier ne parle donc que d'adresses, jamais de
     personnes.
  6. Aucun chemin local, aucune cle, aucun identifiant de compte ne transite :
     verifie par check_no_secrets.py, qui echoue si quoi que ce soit passe.

Usage :
    python3 make_public_data.py --private /chemin/vers/pump_bundle_detector
"""

import argparse
import glob
import gzip
import hashlib
import json
import os
import sys

KEEP_TOKEN_FIELDS = ("mint", "detect_mc", "created", "supply", "pool",
                     "snipers", "captured_at", "capture_min", "n_swaps")
SIG_KEEP_WINDOW_S = 30
SAMPLE_N = 20


def sig_round(x, digits):
    if x is None:
        return None
    try:
        return float("%.*g" % (digits, float(x)))
    except (TypeError, ValueError):
        return None


def reduce_capture(d):
    t0 = d["created"]
    swaps = []
    for w in d["swaps"]:
        o = {
            "ts": w["ts"],
            "side": w["side"],
            "trader": w["trader"],
            "sol": sig_round(w.get("sol"), 6),
            "tokens": sig_round(w.get("tokens"), 8),
            "price": sig_round(w.get("price"), 8),
            "src": w.get("src"),
            "progs": w.get("progs", []),
        }
        if w["ts"] - t0 <= SIG_KEEP_WINDOW_S and w.get("sig"):
            o["sig"] = w["sig"]
        swaps.append(o)
    rec = {k: d.get(k) for k in KEEP_TOKEN_FIELDS}
    rec["swaps"] = swaps
    return rec


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--private", required=True,
                    help="racine du corpus prive (pump_bundle_detector)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "..", "data"))
    a = ap.parse_args()
    priv = os.path.abspath(a.private)
    out = os.path.abspath(a.out)
    os.makedirs(os.path.join(out, "sample"), exist_ok=True)

    capdir = os.path.join(priv, "state", "floor_capture")
    files = sorted(glob.glob(os.path.join(capdir, "*.json")))
    if not files:
        sys.exit("aucune capture trouvee dans %s" % capdir)

    n_empty = 0
    kept = []
    for fp in files:
        try:
            d = json.load(open(fp))
        except Exception:
            n_empty += 1
            continue
        if not d.get("swaps"):
            n_empty += 1
            continue
        kept.append(reduce_capture(d))
    kept.sort(key=lambda r: (r["created"], r["mint"]))

    dst = os.path.join(out, "floor_capture_public.jsonl.gz")
    with gzip.open(dst, "wt", compresslevel=9) as g:
        for r in kept:
            g.write(json.dumps(r, separators=(",", ":"), sort_keys=True) + "\n")

    # echantillon lisible : 20 tokens espaces dans la fenetre, swaps tronques a
    # created+300 s, non compresse. Sert au test a froid (m*.py --data ...) et a
    # inspecter le format a l'oeil. Ne sert a aucune mesure publiee.
    smp = os.path.join(out, "sample", "floor_capture_sample.jsonl")
    step = max(1, len(kept) // SAMPLE_N)
    with open(smp, "w") as f:
        for r in kept[::step][:SAMPLE_N]:
            r = dict(r)
            r["swaps"] = [w for w in r["swaps"] if w["ts"] - r["created"] <= 300]
            r["_tronque_a_s"] = 300
            f.write(json.dumps(r, separators=(",", ":"), sort_keys=True) + "\n")

    copies = [
        (os.path.join(priv, "analysis_fullsnipe", "socle", "dataset.json"),
         os.path.join(out, "dataset_socle.json")),
        (os.path.join(priv, "analysis_supervision", "horizon.json"),
         os.path.join(out, "horizon.json")),
        (os.path.join(priv, "state", "snipe_log.json"),
         os.path.join(out, "snipe_log.json")),
    ]
    for src, dstp in copies:
        obj = json.load(open(src))
        with open(dstp, "w") as f:
            json.dump(obj, f, separators=(",", ":"), sort_keys=True)

    manifest = {
        "corpus": "pump.fun floor_capture — fenetre 2026-06-27 -> 2026-07-04",
        "n_fichiers_source": len(files),
        "n_captures_vides_ecartees": n_empty,
        "n_captures_publiees": len(kept),
        "transformations": [
            "captures sans swap ecartees",
            "champ `fees` supprime",
            "champ `sig` conserve pour t <= created+%ds seulement" % SIG_KEEP_WINDOW_S,
            "sol arrondi 6 chiffres significatifs, tokens/price 8",
            "aucune anonymisation d'adresse (donnees publiques Solana)",
        ],
        "fichiers": {},
    }
    for name in ("floor_capture_public.jsonl.gz", "dataset_socle.json",
                 "horizon.json", "snipe_log.json", "sample/floor_capture_sample.jsonl"):
        p = os.path.join(out, name)
        manifest["fichiers"][name] = {"sha256": sha256(p),
                                      "bytes": os.path.getsize(p)}
    with open(os.path.join(out, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)

    print("captures publiees : %d (vides ecartees : %d / %d fichiers)"
          % (len(kept), n_empty, len(files)))
    for k, v in sorted(manifest["fichiers"].items()):
        print("  %-42s %8.2f Mo  %s" % (k, v["bytes"] / 1e6, v["sha256"][:16]))


if __name__ == "__main__":
    main()
