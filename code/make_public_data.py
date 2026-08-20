#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_public_data.py -- build data/ from the private corpus, read-only.

Published so the reduction can be audited: it documents what was kept, dropped
and rounded between the working corpus and the published one. It is not needed
to reproduce the measurements, since data/ is already in the repository. It is
here to check that data/ does derive from the private corpus, and to put another
corpus into the same format for whoever holds one.

Source, never published as such, read-only:
    <PRIVATE>/state/floor_capture/*.json      645 files, 171 MB
    <PRIVATE>/analysis_fullsnipe/socle/dataset.json
    <PRIVATE>/analysis_supervision/horizon.json
    <PRIVATE>/state/snipe_log.json

Output, published:
    data/floor_capture_public.jsonl.gz
    data/dataset_socle.json
    data/horizon.json
    data/snipe_log.json
    data/sample/floor_capture_sample.jsonl
    data/MANIFEST.json

The transformations applied, exhaustively:
  1. The 352 files holding no swap at all are dropped. An empty capture is a
     collector outage, not a market phenomenon. 293 files are kept.
  2. The `fees` field, a list of fee-paying wallets, is removed: unused by the
     published measurements, and worth about 40 MB.
  3. The `sig` field, a transaction signature, is kept only for the swaps at
     t <= created + 30 s, the ones serving as on-chain verification anchors.
     Removed beyond that, some 500 000 useless signatures.
  4. `sol` is rounded to 6 significant figures, `tokens` and `price` to 8. The
     effect on the results had been measured at under 1e-6 of cell-to-cell
     difference in relative PnL. The script for that check is not in the
     dossier: the figure is reported, it is not reproducible here.
  5. No address is anonymised. Mints, wallets and signatures are public Solana
     data, and masking them would make the dossier uncheckable. An accepted
     choice: the dossier therefore speaks only of addresses, never of people.
  6. No local path, no key and no account identifier goes through: checked by
     check_no_secrets.py, which fails if anything does.

Usage:
    python3 make_public_data.py --private /path/to/pump_bundle_detector
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
        except (OSError, ValueError):
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

    # A readable sample: 20 tokens spread across the window, swaps truncated at
    # created + 300 s, uncompressed. It serves the cold test (m*.py --data ...)
    # and lets the format be inspected by eye. No published measurement uses it.
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
