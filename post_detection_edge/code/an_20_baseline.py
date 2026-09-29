#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base rates of the whole alert population, before any filter.

For every horizon and threshold: how many windows are observed, censored or
missing, the complete-case rate on observed windows (the primary estimator:
the observed set is defined by coverage alone, so it does not depend on the
outcome), and two bounds that bracket what censoring could hide: censored
windows scored as misses (lower) or as hits (upper). Also the MFE distribution
on observed windows. MFE is a maximum of spot reads, touched and not cashed.

By default the TEST split is not read. After tables/LOCK.json exists,
--with-test adds TEST and the full population (run once by an_60_final_test).
"""
from __future__ import annotations

import os
import sys
from typing import Any

import pde


def mfe_stats(xs: list[float]) -> str:
    if not xs:
        return "n/a | n/a | n/a | n/a"
    return "%.2f | %.2f | %.2f | %.2f" % (pde.median(xs), pde.quantile(xs, 0.75), pde.quantile(xs, 0.90),
                                          sum(xs) / len(xs))


def baseline(rows: list[dict[str, Any]], lat: int = 0) -> tuple[list[str], dict[str, Any]]:
    out = ["| horizon | observed | censored | missing | " + " | ".join(
        "P(>=%gx) observed" % k for k in pde.THRESHOLDS) + " | P(>=2x) bounds [cens.=miss ; cens.=hit] "
        "| MFE median | p75 | p90 | mean |",
        "|---|---:|---:|---:|" + "---:|" * len(pde.THRESHOLDS) + "---|---:|---:|---:|---:|"]
    res: dict[str, Any] = {}
    for h in pde.HORIZONS:
        key = "L%d_%s" % (lat, pde.H_LABEL[h])
        st = [r["targets"][key] for r in rows]
        obs = [s for s in st if s["status"] == "observed"]
        cen = [s for s in st if s["status"] == "censored"]
        mis = len(st) - len(obs) - len(cen)
        cells = []
        for k in pde.THRESHOLDS:
            hit = sum(1 for s in obs if s["mfe"] is not None and s["mfe"] >= k)
            cells.append(pde.rate_cell(hit, len(obs)))
            res["%s_%g" % (pde.H_LABEL[h], k)] = (hit, len(obs))
        hit_o = sum(1 for s in obs if s["mfe"] is not None and s["mfe"] >= 2)
        hit_c = sum(1 for s in cen if s.get("mfe") is not None and s["mfe"] >= 2)
        n = len(obs) + len(cen)
        bounds = "[%s ; %s]" % (pde.pct((hit_o + hit_c) / n if n else None),
                                pde.pct((hit_o + len(cen)) / n if n else None))
        out.append("| %s | %d | %d | %d | %s | %s | %s |" % (
            pde.H_LABEL[h], len(obs), len(cen), mis, " | ".join(cells), bounds,
            mfe_stats([s["mfe"] for s in obs if s["mfe"] is not None])))
    return out, res


def main() -> None:
    dev = pde.read_rows("dataset_dev.jsonl.gz")
    groups = [("TRAIN", [r for r in dev if r["split"] == "train"]),
              ("VALIDATION", [r for r in dev if r["split"] == "val"]),
              ("TRAIN + VALIDATION", dev)]
    name = "T1_baseline_dev.md"
    if "--with-test" in sys.argv:
        if not os.path.exists(os.path.join(pde.TABLES, "LOCK.json")):
            sys.exit("TEST is sealed until tables/LOCK.json exists")
        test = pde.read_rows("dataset_test.sealed.jsonl.gz")
        groups = [("TEST", test), ("ALL (TRAIN + VALIDATION + TEST)", dev + test)]
        name = "T1_baseline_test_and_all.md"
    text = ["# T1. Base rates, whole alert population, entry at P0 (spot, not an execution price)", "",
            "Cells: complete-case rate on observed windows (hits/observed) [Wilson 95 %%]. Bounds: censored "
            "windows scored as misses, then as hits. A hit inside a censored window is a real read; a miss "
            "needs the whole window covered. Regenerate: `python3 post_detection_edge/code/an_20_baseline.py%s`."
            % (" --with-test" if "--with-test" in sys.argv else ""), ""]
    for label, rows in groups:
        tab, _ = baseline(rows)
        text += ["## %s (%d alerts)" % (label, len(rows)), ""] + tab + [""]
    pde.write_table(name, "\n".join(text))
    print("\n".join(text))


if __name__ == "__main__":
    main()
