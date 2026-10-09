#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""san_28_pumpgold.py -- sanity tests of the Pump-Gold inspired features (DISCOVERY labels only).

Per feature: observations, missing share per block (features only), distribution, share of zeros,
temporal stability (median per block, features only; DISCOVERY halves), redundancy with the
existing matrix (max |Spearman| with any kept feature, on DISCOVERY rows), trivial relation with
the labels (AUC against Y2 / Y3 / Y5 on DISCOVERY rows only, cluster-capped lift of the top
quintile), and observability: share of alerts whose value changes when the cut moves from
alert - 1 s to alert - 2 s. No VALIDATION / OOS label is read.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

import ap_data as D
import ap_lib as A
import ap_mine as M
from feat_27_pumpgold import DICT


def auc(x, y):
    ok = ~np.isnan(x)
    x, y = x[ok], y[ok]
    if y.sum() == 0 or (1 - y).sum() == 0 or len(x) < 20:
        return None
    r = pd.Series(x).rank().to_numpy()
    n1 = y.sum()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1)))


def main() -> None:
    mx = D.load_matrix()
    lab = D.label_arrays("discovery", mx["mints"])
    rows_d = np.flatnonzero(lab["elig"])
    assert set(mx["blocks"][rows_d]) == {"DISC"}
    pg = {r["mint"]: r for r in A.jl(os.path.join(A.DERIVED, "feat_pumpgold.jsonl.gz"))}
    pg2 = {r["mint"]: r for r in A.jl(os.path.join(A.DERIVED, "feat_pumpgold_cut2.jsonl.gz"))}
    names = list(DICT)
    P = np.array([[np.nan if pg[m].get(k) is None else pg[m][k] for k in names] for m in mx["mints"]], dtype=float)
    P2 = np.array([[np.nan if pg2[m].get(k) is None else pg2[m][k] for k in names] for m in mx["mints"]], dtype=float)
    X = mx["X"].astype(float)
    excl = D.excluded_features()
    kept = [j for j, n in enumerate(mx["names"]) if n not in excl]
    Xd = pd.DataFrame(X[np.ix_(rows_d, kept)], columns=[mx["names"][j] for j in kept])
    Kd = M.cluster_onehot(mx["clusters"][rows_d])
    out = []
    n_tests = 0
    for j, k in enumerate(names):
        v = P[:, j]
        rec = {"feature": k, "definition": DICT[k], "n_nonnull": int((~np.isnan(v)).sum()),
               "missing_share_by_block": {b: float(np.isnan(v[mx["blocks"] == b]).mean()) for b in A.BLOCKS},
               "zero_share": float((v[~np.isnan(v)] == 0).mean()) if (~np.isnan(v)).sum() else None,
               "quantiles_all": {q: float(np.nanquantile(v, q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)} if (~np.isnan(v)).sum() else None,
               "median_by_block": {b: float(np.nanmedian(v[mx["blocks"] == b])) if (~np.isnan(v[mx["blocks"] == b])).sum() else None for b in A.BLOCKS},
               "n_distinct": int(len(np.unique(v[~np.isnan(v)])))}
        vd = v[rows_d]
        h = len(rows_d) // 2
        rec["disc_half_medians"] = [float(np.nanmedian(vd[:h])) if (~np.isnan(vd[:h])).sum() else None,
                                    float(np.nanmedian(vd[h:])) if (~np.isnan(vd[h:])).sum() else None]
        # observability: value change between cut -1 s and -2 s
        v2 = P2[:, j]
        both = ~np.isnan(v) & ~np.isnan(v2)
        rec["cut2_change_share"] = float((np.abs(v[both] - v2[both]) > 1e-9).mean()) if both.sum() else None
        rec["cut2_missing_diff"] = int(np.isnan(v2).sum() - np.isnan(v).sum())
        # redundancy with the existing matrix (DISCOVERY rows, features only)
        s = pd.Series(vd, name="__pg")
        okv = ~np.isnan(vd)
        cols = [c for c in Xd.columns if (okv & ~Xd[c].isna().to_numpy()).sum() >= 30]
        corr = pd.concat([s, Xd[cols]], axis=1).corr(method="spearman", min_periods=30)["__pg"].drop("__pg").dropna()
        if len(corr):
            top = corr.abs().sort_values(ascending=False).head(3)
            rec["max_abs_spearman_existing"] = float(top.iloc[0])
            rec["closest_existing"] = [(n, round(float(corr[n]), 3)) for n in top.index]
        # trivial relation with the labels, DISCOVERY only
        rec["disc"] = {}
        for tg in A.TARGETS:
            y = lab["y"][tg][rows_d]
            a = auc(vd, y)
            n_tests += 1
            ok = ~np.isnan(vd)
            if ok.sum() >= 50:
                q80 = np.nanquantile(vd, 0.8)
                q20 = np.nanquantile(vd, 0.2)
                top_m = ok & (vd >= q80)
                bot_m = ok & (vd <= q20)
                F = np.array([top_m, bot_m], dtype=np.float32)
                ne, he, pe = M.capped(F, y.astype(np.float32), Kd, M.CFG["CAP"])
                base_e = float(M.capped(np.ones((1, len(rows_d)), dtype=np.float32), y.astype(np.float32), Kd, M.CFG["CAP"])[2][0])
                rec["disc"][tg] = {"auc": a, "top_quintile_rate": float(y[top_m].mean()), "bottom_quintile_rate": float(y[bot_m].mean()),
                                   "base": float(y.mean()), "top_capped_lift": float(pe[0] / base_e), "bottom_capped_lift": float(pe[1] / base_e)}
                n_tests += 2
            else:
                rec["disc"][tg] = {"auc": a}
        out.append(rec)
    A.registre("sanity_pumpgold", n_tests, "Pump-Gold features: AUC and quintile rates on DISCOVERY only",
               n=int(len(rows_d)), declare=False, sortie="tables/pumpgold_sanity.json")
    A.write_json(os.path.join(A.TABLES, "pumpgold_sanity.json"), out)
    for r in out:
        d2 = r["disc"].get("Y2", {})
        print("%-28s n %4d miss %.2f zero %s cut2chg %s rho_max %s (%s) AUC2 %s top20 %s bottom20 %s base %s" % (
            r["feature"], r["n_nonnull"], 1 - r["n_nonnull"] / len(mx["mints"]),
            "%.2f" % r["zero_share"] if r["zero_share"] is not None else "n/a",
            "%.2f" % r["cut2_change_share"] if r["cut2_change_share"] is not None else "n/a",
            "%.2f" % r.get("max_abs_spearman_existing", 0), (r.get("closest_existing") or [("", 0)])[0][0],
            "%.2f" % d2["auc"] if d2.get("auc") is not None else "n/a",
            "%.2f" % d2["top_quintile_rate"] if "top_quintile_rate" in d2 else "n/a",
            "%.2f" % d2["bottom_quintile_rate"] if "bottom_quintile_rate" in d2 else "n/a",
            "%.2f" % d2["base"] if "base" in d2 else "n/a"))


if __name__ == "__main__":
    main()
