#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Freeze the live detector's corpus into post_detection_edge/data/, once.

The detector (a separate, unpublished project that alerts on bundle-sniped
pump.fun launches) keeps writing to its own journal and price series. This
script copies both, cuts everything at a single timestamp T_SNAP, drops what the
study does not need, and writes a manifest with a sha256 per file. The copy is
then the reference dataset of the study: nothing downstream reads the live
files, and this script refuses to run a second time (--force exists for a
deliberate, documented re-freeze, never to add data to an experiment already
run).

What is kept, and why:
  journal  launch alerts, rejected candidates (for the definition comparison),
           the late actor relabelling ("outil"), follow-up closures, and the
           detector's own outage lines (machine freezes, WebSocket gaps,
           restarts, price-read failures). Message texts are dropped; the one
           thing taken from them is the token symbol, public at creation and
           needed by the pre-registered protocol's copied-name hypothesis.
           Palier and verdict messages are dropped: they are outcomes.
  series   every price point (mint, seconds since alert, multiple of p0, price)
           of an alert made before T_SNAP, cut at T_SNAP in absolute time.
  caches   the five caches the pre-registered protocol of 2026-08-29 reads
           (funding lineage, copied names, pool density, exit destinations,
           core exit).

Every byte written goes through code/redact.py, the repository's write-time
redaction of slur-vanity identifiers (injective, so every count and every
lineage match is unchanged). A re-freeze with --force reuses the T_SNAP already
recorded, so it can only change the representation, never the content.

Usage:
    DETECTOR_DIR=/path/to/detector python3 post_detection_edge/code/snap_00_freeze.py
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(STUDY), "code"))
import redact  # noqa: E402
DATA = os.path.join(STUDY, "data")
MANIFEST = os.path.join(DATA, "SNAPSHOT.json")

KEEP = {
    "alerte_lancement", "outil", "cloture", "rejete", "gel_machine", "trou_ws",
    "demarrage", "echec_suivi", "prix_incoherent", "courbe_introuvable",
    "pagination_non_atteinte", "echec_confirmation", "echec_filtre",
    "verdict8_renonce",
}
CACHES = ("financeurs_cache.json", "protocole_400_copies.json", "protocole_400_n60.json",
          "destinations_cache.json", "sortie_noyau_cache.json")
SYMBOL = re.compile(r"<b>(.*?)</b> \((.*?)\)")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def reduce_journal(src: str, t_snap: float) -> tuple[list[dict], dict]:
    rows, counts, bad = [], {}, 0
    with open(src, encoding="utf8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                bad += 1           # the detector's log can end on a half-written line
                continue
            if r.get("t", 0) > t_snap or r.get("genre") not in KEEP:
                continue
            if r["genre"] == "alerte_lancement":
                m = SYMBOL.search(r.get("texte") or "")
                r["sym"] = m.group(2).strip() if m else ""
            if r["genre"] == "demarrage":
                r = {"t": r["t"], "utc": r["utc"], "genre": "demarrage"}
            r.pop("texte", None)
            rows.append(redact.scrub(r))
            counts[r["genre"]] = counts.get(r["genre"], 0) + 1
    counts["_unparsable_lines"] = bad
    return rows, counts


def reduce_series(srcs: list[str], alert_t: dict[str, float], t_snap: float, out: str) -> dict:
    kept = dropped_mint = dropped_time = 0
    with gzip.open(out, "wt", encoding="utf8", compresslevel=9) as g:
        for src in srcs:
            opener = gzip.open if src.endswith(".gz") else open
            with opener(src, "rt", encoding="utf8") as f:
                for line in f:
                    if not line.strip() or line.startswith("#"):
                        continue
                    p = line.split()
                    if len(p) != 4:
                        raise ValueError("unreadable series line in %s: %r" % (src, line[:80]))
                    t_a = alert_t.get(p[0])
                    if t_a is None:
                        dropped_mint += 1
                        continue
                    if t_a + float(p[1]) > t_snap:
                        dropped_time += 1
                        continue
                    line = redact.scrub_text(line)
                    g.write(line if line.endswith("\n") else line + "\n")
                    kept += 1
    return {"points_kept": kept, "points_dropped_unknown_mint": dropped_mint,
            "points_dropped_after_t_snap": dropped_time}


def main() -> None:
    root = os.environ.get("DETECTOR_DIR")
    if not root:
        sys.exit("set DETECTOR_DIR to the detector project (it holds etat/ and analyse/)")
    if os.path.exists(MANIFEST) and "--force" not in sys.argv:
        sys.exit("snapshot already frozen (%s); it is immutable. --force re-freezes on purpose."
                 % os.path.relpath(MANIFEST, STUDY))
    os.makedirs(DATA, exist_ok=True)
    etat = os.path.join(root, "etat")
    t_snap = float(int(time.time()) // 60 * 60)
    history = []
    if os.path.exists(MANIFEST):
        old = json.load(open(MANIFEST, encoding="utf8"))
        t_snap = old["t_snap"]
        history = old.get("history", []) + [{"frozen_at_utc": old["frozen_at_utc"],
                                             "files": old["files"]}]
        for dirpath, _, names in os.walk(DATA):
            for n in names:
                os.chmod(os.path.join(dirpath, n), 0o644)

    # 1. copy the live files first, so the cut is applied to a stable copy
    tmp = os.path.join(DATA, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    shutil.copyfile(os.path.join(etat, "journal.jsonl"), os.path.join(tmp, "journal.jsonl"))
    series_src = sorted(x for x in os.listdir(etat) if re.fullmatch(r"prix-\d{8}-\d{6}\.jsonl(\.gz)?", x))
    series_src = [os.path.join(etat, x) for x in series_src] + [os.path.join(etat, "prix.jsonl")]
    copies = []
    for s in series_src:
        d = os.path.join(tmp, os.path.basename(s))
        shutil.copyfile(s, d)
        copies.append(d)

    # 2. journal
    rows, jcounts = reduce_journal(os.path.join(tmp, "journal.jsonl"), t_snap)
    jpath = os.path.join(DATA, "journal.jsonl.gz")
    with gzip.open(jpath, "wt", encoding="utf8", compresslevel=9) as g:
        for r in rows:
            g.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    # 3. series, keyed on the alert time of each mint
    alert_t = {r["mint"]: r["t"] for r in rows if r["genre"] == "alerte_lancement"}
    spath = os.path.join(DATA, "series.txt.gz")
    scounts = reduce_series(copies, alert_t, t_snap, spath)

    # 4. protocol caches, byte for byte
    cdir = os.path.join(DATA, "protocol400_caches")
    os.makedirs(cdir, exist_ok=True)
    for c in CACHES:
        with open(os.path.join(root, "analyse", c), encoding="utf8") as f:
            text = redact.scrub_text(f.read())
        with open(os.path.join(cdir, c), "w", encoding="utf8") as f:
            f.write(text)
    shutil.copyfile(os.path.join(root, "analyse", "PROTOCOLE_400.md"), os.path.join(cdir, "PROTOCOLE_400.md"))
    shutil.rmtree(tmp)

    files = [jpath, spath] + [os.path.join(cdir, c) for c in CACHES + ("PROTOCOLE_400.md",)]
    manifest = {
        "t_snap": t_snap,
        "t_snap_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t_snap)),
        "frozen_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "source": "live detector project: etat/journal.jsonl, etat/prix*.jsonl, analyse/<protocol caches>",
        "series_files_read": [os.path.basename(s) for s in series_src],
        "journal_rows_kept_by_type": dict(sorted(jcounts.items())),
        "series": scounts,
        "n_alerts": len(alert_t),
        "files": {os.path.relpath(p, DATA): {"bytes": os.path.getsize(p), "sha256": sha256(p)} for p in files},
        "redaction": "code/redact.py applied at write time (%d identifiers in the map)"
                     % redact.stats()["n_redacted_identifiers"],
        "rule": "immutable reference dataset of the study; future data goes to a separate test",
        "history": history,
    }
    with open(MANIFEST, "w", encoding="utf8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
        f.write("\n")
    for p in files + [MANIFEST]:
        os.chmod(p, 0o444)
    print(json.dumps({k: manifest[k] for k in ("t_snap_utc", "n_alerts", "series", "journal_rows_kept_by_type")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
