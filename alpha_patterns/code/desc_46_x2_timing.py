#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""desc_46_x2_timing.py -- when does the confirmed x2 arrive, counted from the entry?

Descriptive only, no test, no outcome used for any selection. Reads the frozen label file
(derived/labels.jsonl.gz, sha256 recorded in SELECTION_FREEZE.json; not published, 1 MB) and writes
tables/x2_timing_summary.json: for the eligible launches of DISCOVERY + SELECTION (fine sampling, an
entry read in [5, 15] s after the alert, 1 h window observed), the distribution of t_hit_2x, the delay
from the entry to the SECOND of the two consecutive reads at or above 2 x the entry price. Also the
median entry delay after the alert. These are the figures quoted in section 2 of
tables/TEAM_ABSORPTION_MECHANISM_2026-10-07.md and in the repository's Act IV.

Usage:  python3 desc_46_x2_timing.py [--labels PATH] [--out PATH]
The input's sha256 is checked against SELECTION_FREEZE.json before anything is read: the summary is
tied to the frozen file, not to whatever file sits at that path.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
BLOCKS = ("DISC", "SEL")
CUTS = (30, 60, 120, 300, 600, 900, 1800)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def quantile(sorted_values: list, p: float) -> float:
    """Linear interpolation between order statistics (numpy's default)."""
    k = (len(sorted_values) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (k - lo)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=os.path.join(STUDY, "derived", "labels.jsonl.gz"))
    ap.add_argument("--out", default=os.path.join(STUDY, "tables", "x2_timing_summary.json"))
    a = ap.parse_args()

    freeze = json.load(open(os.path.join(STUDY, "SELECTION_FREEZE.json"), encoding="utf-8"))
    expected = freeze["files"]["derived/labels.jsonl.gz"]
    if not os.path.exists(a.labels):
        raise SystemExit("labels file not found: %s (not published; sha256 %s in SELECTION_FREEZE.json)"
                         % (a.labels, expected))
    got = sha256_file(a.labels)
    if got != expected:
        raise SystemExit("labels file sha256 %s differs from the frozen %s: refusing to summarise it"
                         % (got, expected))

    rows = [json.loads(line) for line in gzip.open(a.labels, "rt", encoding="utf-8")]
    eligible = [r for r in rows
                if r.get("fine") and r.get("entry") and r.get("obs_3600") and r["block"] in BLOCKS]
    good = [r for r in eligible if r.get("conf_2x_3600") == 1]
    hits = sorted(r["t_hit_2x"] for r in good)
    if len(hits) != len(good):
        raise SystemExit("a confirmed x2 without a hit time: inconsistent label file")

    out = {
        "input": {"path": "derived/labels.jsonl.gz", "sha256": got, "rows": len(rows)},
        "definition": "t_hit_2x = seconds from the entry read to the second of two consecutive price "
                      "reads >= 2 x the entry price, within 1 h; eligible = fine sampling, entry read "
                      "in [5, 15] s after the alert, 1 h window observed, blocks DISCOVERY + SELECTION",
        "eligible": len(eligible),
        "eligible_by_block": {b: sum(1 for r in eligible if r["block"] == b) for b in BLOCKS},
        "good": len(good),
        "good_by_block": {b: sum(1 for r in good if r["block"] == b) for b in BLOCKS},
        "rate_x2": len(good) / len(eligible),
        "entry_dt_after_alert_s_median": statistics.median(r["entry"]["dt"] for r in eligible),
        "t_hit_2x_s": {
            "n": len(hits),
            "min": hits[0],
            "p10": quantile(hits, 0.10),
            "p25": quantile(hits, 0.25),
            "p50": quantile(hits, 0.50),
            "p75": quantile(hits, 0.75),
            "p90": quantile(hits, 0.90),
            "max": hits[-1],
        },
        "share_of_good_confirmed_within_s": {
            str(c): sum(1 for t in hits if t <= c) / len(hits) for c in CUTS},
        "share_of_eligible_confirmed_within_s": {
            str(c): sum(1 for t in hits if t <= c) / len(eligible) for c in CUTS},
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print("eligible %d, confirmed x2 %d (%.1f %%); t_hit_2x p10/p50/p90 = %.0f / %.0f / %.0f s; "
          "within 30 s %.1f %% of the GOOD" % (
              out["eligible"], out["good"], 100 * out["rate_x2"], out["t_hit_2x_s"]["p10"],
              out["t_hit_2x_s"]["p50"], out["t_hit_2x_s"]["p90"],
              100 * out["share_of_good_confirmed_within_s"]["30"]))
    print("wrote", os.path.relpath(a.out, STUDY))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
