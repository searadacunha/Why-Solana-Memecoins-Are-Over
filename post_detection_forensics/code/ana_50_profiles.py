#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 5 of analysis_plan.md: six launch profiles defined in advance, never ranked.

Thresholds are TRAIN medians. Profiles may overlap. For each, TRAIN and
VALIDATION separately: N, confirmed 2x within 5 min / 15 min / 1 h, median time
to the confirmed 2x, and the MFE distribution at 15 min (touched, not cashed).
"""
from __future__ import annotations

from typing import Any, Callable

import ana_lib as L


def main() -> None:
    rows = L.load()
    tr = [r["fA"] for r in rows if r["split"] == "train"]
    m = {f: L.q([x.get(f) for x in tr], 0.5) for f in ("b_top1", "b_ticket_cv", "w_early_log_prior_n",
                                                           "w_early_fresh")}

    def g(x: dict[str, Any], f: str) -> float:
        v = x.get(f)
        return float("nan") if v is None else v
    prof: dict[str, Callable[[dict[str, Any]], bool]] = {
        "1 concentrated bundle (b_top1 > TRAIN median)": lambda x: g(x, "b_top1") > m["b_top1"],
        "2 distributed bundle (independent share 1, ticket CV < median)":
            lambda x: g(x, "f_indep_share") == 1 and g(x, "b_ticket_cv") < m["b_ticket_cv"],
        "3 common funding (one funder >= 2 core wallets)": lambda x: g(x, "f_same_funder_multi") == 1,
        "4 distributed funding (>= 3 distinct funders)": lambda x: g(x, "f_n_funders") >= 3,
        "5 experienced early wallets (history > median)":
            lambda x: g(x, "w_early_log_prior_n") > m["w_early_log_prior_n"],
        "6 fresh early wallets (fresh share > median)": lambda x: g(x, "w_early_fresh") > m["w_early_fresh"],
        "all alerts": lambda x: True}
    lines = ["# D5. Profiles (defined in advance, TRAIN-median thresholds %s; not ranked)" % {
        k: round(v, 4) if v is not None else None for k, v in m.items()}, "",
             "| profile | split | N | 2x 5 min | 2x 15 min | 2x 1 h | median time to 2x (s) | MFE 15 min q25 / median "
             "/ q75 / q90 |", "|---|---|---:|---|---|---|---:|---|"]
    for name, fn in prof.items():
        for sp in ("train", "val"):
            sel = [r for r in rows if r["split"] == sp and fn(r["fA"])]
            cells = []
            for lab in ("A_conf_2x_5m", "A_conf_2x_15m", "A_conf_2x_1h"):
                ys = [r["y"][lab] for r in sel if r["y"].get(lab) is not None]
                cells.append(L.rate(sum(ys), len(ys)))
            tt = [r["y"]["A_t_conf_2x_s"] for r in sel if r["y"].get("A_t_conf_2x_s")]
            mfe = [r["y"]["A_mfe_900s"] for r in sel if r["y"].get("A_mfe_900s") is not None]
            lines.append("| %s | %s | %d | %s | %.0f | %s |" % (
                name, sp.upper(), len(sel), " | ".join(cells), L.q(tt, 0.5) or float("nan"),
                " / ".join("%.2f" % (L.q(mfe, p) or float("nan")) for p in (0.25, 0.5, 0.75, 0.9))))
    L.write("D5_profiles.md", lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
