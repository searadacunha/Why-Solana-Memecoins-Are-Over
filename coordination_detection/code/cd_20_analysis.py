#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steps 7 to 10 of the protocol on the frozen coordination table: TRAIN, VALIDATION once, the five null
models, robustness, then the classification. No price outcome is computed anywhere; the premium and the
market cap are measured after the labels, as the plan says.

Writes tables/C1_measures.md, C2_nulls.md, C3_labels.md, C4_structure.md, C5_robustness.md,
C6_price.md, C7_exits.md, C8_classification.md and derived/C_results.json.
"""

from __future__ import annotations

import bisect
import json
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Optional, Sequence

import cd_lib as L

sys.path.insert(0, os.path.join(L.ROOT, "post_detection_forensics", "code"))
import fml

N_PERM, SEED = 200, 20261001
SPLITS = ("train", "val")
LABELS = ["SHARED_FUNDER", "HIGH_SYNCHRONIZATION", "FUNDING_CLUSTER", "RECURRING_WALLET_CLUSTER"]


def q(v: Sequence[float], p: float) -> Optional[float]:
    s = sorted(x for x in v if x is not None)
    return s[int(p * (len(s) - 1))] if s else None


def med3(v: Sequence[Optional[float]]) -> str:
    s = [x for x in v if x is not None]
    if not s:
        return "n/a"
    return "%.3g (%.3g-%.3g)" % (statistics.median(s), q(s, 0.25), q(s, 0.75))


# --------------------------------------------------------------- raw criteria #
def shared_stat(sn: list[dict[str, Any]]) -> Optional[int]:
    """Most snipers on one shareable funder, genesis or last (None when neither is observed for all)."""
    vals = [f["shared"] for f in (L.funding(sn, "gen"), L.funding(sn, "last")) if f["observed"]]
    return max(vals) if vals else None


def cluster_stat(r: dict[str, Any], sn: list[dict[str, Any]]) -> int:
    return L.graph(r, sn)["largest_component_snipers"]


def spread_stat(ages: list[float]) -> float:
    return max(ages) - min(ages)


def ages_of(sn: list[dict[str, Any]]) -> Optional[list[float]]:
    a = [s["bt"] - s["last_bt"] for s in sn if s.get("last_bt") is not None and s.get("bt") is not None]
    return a if len(a) == len(sn) else None


# ------------------------------------------------------------ per-launch nulls #
def launch_labels(rows: list[dict[str, Any]], reuse: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Labels of every launch, its nulls drawn from the sniper records of its own split."""
    out: dict[str, dict[str, Any]] = {}
    for sp in SPLITS:
        rr = [r for r in rows if r["split"] == sp]
        pool = [s for r in rr for s in r["snipers"]]
        age_pool = [s["bt"] - s["last_bt"] for s in pool if s.get("last_bt") is not None and s.get("bt") is not None]
        rng = random.Random(SEED)
        for r in rr:
            n = len(r["snipers"])
            d: dict[str, Any] = {}
            obs = shared_stat(r["snipers"])
            if obs is not None:
                null = [shared_stat(rng.sample(pool, n)) or 1 for _ in range(N_PERM)]
                p = (1 + sum(1 for x in null if x >= obs)) / (1 + N_PERM)
                d["SHARED_FUNDER"] = obs >= 2 and p < 0.05
                d["shared_p"] = p
            a = ages_of(r["snipers"])
            if a is not None:
                o = spread_stat(a)
                null = [spread_stat(rng.sample(age_pool, n)) for _ in range(N_PERM)]
                p = (1 + sum(1 for x in null if x <= o)) / (1 + N_PERM)
                d["HIGH_SYNCHRONIZATION"] = p < 0.05
                d["sync_p"] = p
            o = cluster_stat(r, r["snipers"])
            null = [cluster_stat(r, rng.sample(pool, n)) for _ in range(N_PERM)]
            p = (1 + sum(1 for x in null if x >= o)) / (1 + N_PERM)
            d["FUNDING_CLUSTER"] = (o >= 3 or o > n / 2) and p < 0.05
            d["cluster_p"] = p
            d["RECURRING_WALLET_CLUSTER"] = reuse[r["mint"]]["pairs_seen_before"] >= 1
            k = sum(1 for lab in LABELS if d.get(lab))
            d["score"] = k
            d["MULTI-SIGNAL_COORDINATION"] = k >= 2
            d["NO_SHARED_STRUCTURE"] = k == 0
            out[r["mint"]] = d
    return out


# --------------------------------------------------------- population nulls --- #
def perm_records(rr: list[dict[str, Any]], rng: random.Random) -> list[list[dict[str, Any]]]:
    """N1: sniper records reassigned across the launches, sizes kept."""
    pool = [s for r in rr for s in r["snipers"]]
    rng.shuffle(pool)
    out, i = [], 0
    for r in rr:
        out.append(pool[i : i + len(r["snipers"])])
        i += len(r["snipers"])
    return out


FUND_FIELDS = (
    "gen_funder",
    "gen_funder_hub",
    "gen_received",
    "source",
    "last_funder",
    "last_funder_hub",
    "last_amount",
    "last_bt_age",
)


def perm_funders(rr: list[dict[str, Any]], rng: random.Random) -> list[list[dict[str, Any]]]:
    """N2: snipers stay, their funding attributes are reassigned among the split's sniper records."""
    attrs = [{k: s.get(k) for k in FUND_FIELDS if k != "last_bt_age"} for r in rr for s in r["snipers"]]
    rng.shuffle(attrs)
    out, i = [], 0
    for r in rr:
        g = []
        for s in r["snipers"]:
            g.append({**s, **attrs[i]})
            i += 1
        out.append(g)
    return out


def pop_null(
    rr: list[dict[str, Any]],
    stat: Callable[[list[dict[str, Any]], list[list[dict[str, Any]]]], float],
    perm: Callable[[list[dict[str, Any]], random.Random], Any],
    higher: bool = True,
) -> dict[str, Any]:
    obs = stat(rr, [r["snipers"] for r in rr])
    rng = random.Random(SEED)
    null = sorted(stat(rr, perm(rr, rng)) for _ in range(N_PERM))
    p = (1 + sum(1 for x in null if (x >= obs if higher else x <= obs))) / (1 + N_PERM)
    pct = sum(1 for x in null if x < obs) / N_PERM
    return {
        "obs": obs,
        "null_mean": statistics.mean(null),
        "pct": pct,
        "p": p,
        "ci": [null[int(0.025 * (N_PERM - 1))], null[int(0.975 * (N_PERM - 1))]],
    }


def stat_shared(rr: list[dict[str, Any]], groups: list[list[dict[str, Any]]]) -> float:
    return float(sum(1 for g in groups if (shared_stat(g) or 0) >= 2))


def stat_cluster(rr: list[dict[str, Any]], groups: list[list[dict[str, Any]]]) -> float:
    return float(sum(1 for r, g in zip(rr, groups) if (lambda o: o >= 3 or o > len(g) / 2)(cluster_stat(r, g))))


def null_spread(rr: list[dict[str, Any]], rng_seed: int = SEED) -> dict[str, Any]:
    """N3 for the snipers: their funding-to-buy delays shuffled across the split's sniper records."""
    known = [r for r in rr if ages_of(r["snipers"]) is not None]
    obs = statistics.mean(spread_stat(ages_of(r["snipers"])) for r in known)
    pool = [a for r in known for a in ages_of(r["snipers"])]
    rng = random.Random(rng_seed)
    null = []
    for _ in range(N_PERM):
        rng.shuffle(pool)
        i, vals = 0, []
        for r in known:
            n = len(r["snipers"])
            vals.append(spread_stat(pool[i : i + n]))
            i += n
        null.append(statistics.mean(vals))
    null.sort()
    return {
        "obs": obs,
        "null_mean": statistics.mean(null),
        "pct": sum(1 for x in null if x < obs) / N_PERM,
        "p": (1 + sum(1 for x in null if x <= obs)) / (1 + N_PERM),
        "ci": [null[int(0.025 * (N_PERM - 1))], null[int(0.975 * (N_PERM - 1))]],
        "launches": len(known),
    }


def null_early(rr: list[dict[str, Any]]) -> dict[str, Any]:
    """N3 for the early buyers: their delays from the creation (slots) redrawn from the split's pool,
    within each launch's own pre-alert window, counts kept. Statistic: mean same-slot share."""
    per = []
    for r in rr:
        sl = sorted(e["slot"] - r["slot0"] for e in r["early"] if e["pre_alert"])
        if len(sl) >= 2:
            per.append((sl, int((r["t"] - 1 - r["t_create"]) / L.SLOT_S) + 1))
    pool = sorted(x for sl, _ in per for x in sl)

    def same_slot(sl: list[int]) -> float:
        c = Counter(sl)
        return sum(1 for x in sl if c[x] >= 2) / len(sl)

    obs = statistics.mean(same_slot(sl) for sl, _ in per)
    rng = random.Random(SEED)
    null = []
    for _ in range(N_PERM):
        vals = []
        for sl, mx in per:
            hi = bisect.bisect_right(pool, mx)
            draw = sorted(pool[rng.randrange(hi)] for _ in sl) if hi else sl
            c = Counter(draw)
            vals.append(sum(1 for x in draw if c[x] >= 2) / len(draw))
        null.append(statistics.mean(vals))
    null.sort()
    return {
        "obs": obs,
        "null_mean": statistics.mean(null),
        "pct": sum(1 for x in null if x < obs) / N_PERM,
        "p": (1 + sum(1 for x in null if x >= obs)) / (1 + N_PERM),
        "ci": [null[int(0.025 * (N_PERM - 1))], null[int(0.975 * (N_PERM - 1))]],
        "launches": len(per),
    }


def null_tickets(rr: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """N4: tickets redistributed across launches, sizes kept. Statistic: launches with two tickets or more
    that are identical / near-identical / round."""

    def stat(groups: list[list[float]]) -> float:
        if key == "round":
            return float(sum(1 for g in groups if L.tickets(g)["round"] >= 2))
        return float(sum(1 for g in groups if L.tickets(g)[key] >= 1))

    groups = [[s["ticket"] for s in r["snipers"]] for r in rr]
    obs = stat(groups)
    pool = [x for g in groups for x in g]
    rng = random.Random(SEED)
    null = []
    for _ in range(N_PERM):
        rng.shuffle(pool)
        i, gg = 0, []
        for g in groups:
            gg.append(pool[i : i + len(g)])
            i += len(g)
        null.append(stat(gg))
    null.sort()
    return {
        "obs": obs,
        "null_mean": statistics.mean(null),
        "pct": sum(1 for x in null if x < obs) / N_PERM,
        "p": (1 + sum(1 for x in null if x >= obs)) / (1 + N_PERM),
        "ci": [null[int(0.025 * (N_PERM - 1))], null[int(0.975 * (N_PERM - 1))]],
    }


def null_reuse(rr: list[dict[str, Any]]) -> dict[str, Any]:
    """N5: the wallet-launch bipartite graph rewired by swaps (each wallet's launches and each launch's
    snipers kept). Statistic: sniper pairs that co-occur in two launches or more."""
    groups = [[s["wallet"] for s in r["snipers"]] for r in rr]
    obs_c = L.co_occurrence(groups)
    obs = float(sum(1 for v in obs_c.values() if v >= 2))
    edges = [(w, i) for i, g in enumerate(groups) for w in g]
    rng = random.Random(SEED)
    null = []
    for _ in range(N_PERM):
        gs = [set(g) for g in groups]
        e = list(edges)
        for _ in range(5 * len(e)):
            a, b = rng.randrange(len(e)), rng.randrange(len(e))
            (w1, l1), (w2, l2) = e[a], e[b]
            if l1 == l2 or w1 == w2 or w2 in gs[l1] or w1 in gs[l2]:
                continue
            gs[l1].remove(w1)
            gs[l1].add(w2)
            gs[l2].remove(w2)
            gs[l2].add(w1)
            e[a], e[b] = (w2, l1), (w1, l2)
        c = L.co_occurrence([sorted(g) for g in gs])
        null.append(float(sum(1 for v in c.values() if v >= 2)))
    null.sort()
    return {
        "obs": obs,
        "null_mean": statistics.mean(null),
        "pct": sum(1 for x in null if x < obs) / N_PERM,
        "p": (1 + sum(1 for x in null if x >= obs)) / (1 + N_PERM),
        "ci": [null[int(0.025 * (N_PERM - 1))], null[int(0.975 * (N_PERM - 1))]],
        "wallets_in_recurring_pairs": len({w for p, v in obs_c.items() if v >= 2 for w in p}),
    }


def nulls_for(rr: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "shared funder, N1 wallets shuffled": pop_null(rr, stat_shared, perm_records),
        "shared funder, N2 funders shuffled": pop_null(rr, stat_shared, perm_funders),
        "funding cluster, N2 funders shuffled": pop_null(rr, stat_cluster, perm_funders),
        "funding spread, N3 timing shuffled": null_spread(rr),
        "early same-slot share, N3": null_early(rr),
        "identical tickets, N4": null_tickets(rr, "identical_pairs"),
        "near-identical tickets, N4": null_tickets(rr, "near_identical_pairs"),
        "round tickets, N4": null_tickets(rr, "round"),
        "recurring sniper pairs, N5": null_reuse(rr),
    }


LABEL_NULL = {
    "SHARED_FUNDER": "shared funder, N1 wallets shuffled",
    "HIGH_SYNCHRONIZATION": "funding spread, N3 timing shuffled",
    "FUNDING_CLUSTER": "funding cluster, N2 funders shuffled",
    "RECURRING_WALLET_CLUSTER": "recurring sniper pairs, N5",
}


def label_nulls(rr: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "SHARED_FUNDER": pop_null(rr, stat_shared, perm_records),
        "HIGH_SYNCHRONIZATION": null_spread(rr),
        "FUNDING_CLUSTER": pop_null(rr, stat_cluster, perm_funders),
        "RECURRING_WALLET_CLUSTER": null_reuse(rr),
    }


def fmt_null(d: dict[str, Any]) -> str:
    return "%.4g | %.4g | %.0f %% | %.3f | [%.4g, %.4g]" % (
        d["obs"],
        d["null_mean"],
        100 * d["pct"],
        d["p"],
        d["ci"][0],
        d["ci"][1],
    )


# ----------------------------------------------------------------- main ----- #
def kappa(a: list[bool], b: list[bool]) -> Optional[float]:
    n = len(a)
    if not n:
        return None
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else None


def main() -> None:
    rows = L.load()
    reuse = L.reuse_causal(rows)
    res: dict[str, Any] = {}
    # ---- C1 measures
    meas: dict[str, dict[str, Any]] = {}
    for r in rows:
        sn = r["snipers"]
        m = {"n_snipers": len(sn)}
        for kind in ("gen", "last"):
            f = L.funding(sn, kind)
            if f["observed"]:
                for k, v in f.items():
                    if k != "observed":
                        m["%s_%s" % (kind, k)] = v
            fs = L.funding(sn, kind, strict=True)
            if fs["observed"]:
                m["%s_strict_ge2" % kind] = fs["ge2"]
        m.update(L.sync(r))
        m.update({"tk_" + k: v for k, v in L.tickets([s["ticket"] for s in sn]).items()})
        m.update({"g_" + k: v for k, v in L.graph(r).items()})
        m.update({"g_strict_arch": L.graph(r, strict=True)["architecture"]})
        m.update({"re_" + k: v for k, v in reuse[r["mint"]].items()})
        meas[r["mint"]] = m
    keys = sorted({k for m in meas.values() for k in m if k not in ("g_architecture", "g_strict_arch")})
    lines = [
        "# C1. Measures per launch (median, p25-p75 or share), TRAIN and VALIDATION",
        "",
        "| measure | TRAIN: launches with it | TRAIN | VALIDATION: launches | VALIDATION |",
        "|---|---:|---|---:|---|",
    ]
    for k in keys:
        cells = []
        for sp in SPLITS:
            v = [meas[r["mint"]].get(k) for r in rows if r["split"] == sp and meas[r["mint"]].get(k) is not None]
            if v and isinstance(v[0], bool):
                cells += [str(len(v)), "%.1f %% true" % (100 * sum(v) / len(v))]
            else:
                cells += [str(len(v)), med3([float(x) for x in v])]
        lines.append("| %s | %s |" % (k, " | ".join(cells)))
    lines += [
        "",
        "## Funding-graph architecture (hubs excluded; unknown-status last funders kept, then dropped)",
        "",
        "| architecture | TRAIN | VALIDATION | TRAIN, strict | VALIDATION, strict |",
        "|---|---:|---:|---:|---:|",
    ]
    for arch in ("A", "B", "SHARED", "INDEPENDENT", "OTHER"):
        c = []
        for key in ("g_architecture", "g_strict_arch"):
            for sp in SPLITS:
                rr = [r for r in rows if r["split"] == sp]
                k = sum(1 for r in rr if meas[r["mint"]][key] == arch)
                c.append("%d (%.0f %%)" % (k, 100 * k / len(rr)))
        lines.append("| %s | %s | %s | %s | %s |" % (arch, c[0], c[1], c[2], c[3]))
    L.write("C1_measures.md", lines)
    # ---- C2 population nulls
    nulls = {sp: nulls_for([r for r in rows if r["split"] == sp]) for sp in SPLITS}
    res["nulls"] = nulls
    lines = [
        "# C2. Null models, population level (%d permutations each, inside each split)" % N_PERM,
        "",
        "Observed | null mean | percentile of the observed in the null | empirical p (one-sided, towards "
        "coordination) | 95 % null interval.",
        "",
        "| measure | TRAIN | VALIDATION |",
        "|---|---|---|",
    ]
    for k in nulls["train"]:
        lines.append("| %s | %s | %s |" % (k, fmt_null(nulls["train"][k]), fmt_null(nulls["val"][k])))
    nr = nulls["train"]["recurring sniper pairs, N5"]
    lines += [
        "",
        "Wallets in recurring sniper pairs: TRAIN %d, VALIDATION %d."
        % (nr["wallets_in_recurring_pairs"], nulls["val"]["recurring sniper pairs, N5"]["wallets_in_recurring_pairs"]),
    ]
    L.write("C2_nulls.md", lines)
    # ---- C3 labels
    lab = launch_labels(rows, reuse)
    res["labels"] = {k: v for k, v in lab.items()}
    allabs = LABELS + ["MULTI-SIGNAL_COORDINATION", "NO_SHARED_STRUCTURE"]
    lines = [
        "# C3. Labels per launch (per-launch nulls of %d draws from the launch's own split)" % N_PERM,
        "",
        "| label | TRAIN launches | VALIDATION launches | launches where it can be decided, TRAIN / VAL |",
        "|---|---:|---:|---|",
    ]
    for lb in allabs:
        c = []
        for sp in SPLITS:
            rr = [r for r in rows if r["split"] == sp]
            dec = [r for r in rr if lb in lab[r["mint"]]]
            k = sum(1 for r in dec if lab[r["mint"]][lb])
            c.append((k, len(dec), len(rr)))
        lines.append(
            "| %s | %d (%.1f %%) | %d (%.1f %%) | %d / %d |"
            % (lb, c[0][0], 100 * c[0][0] / max(1, c[0][1]), c[1][0], 100 * c[1][0] / max(1, c[1][1]), c[0][1], c[1][1])
        )
    tr = [r for r in rows if r["split"] == "train"]
    lines += [
        "",
        "## Are the four dimensions distinct? Phi on TRAIN (launches where both are decided)",
        "",
        "| | " + " | ".join(LABELS) + " |",
        "|---|" + "---:|" * len(LABELS),
    ]
    phis = []
    for a in LABELS:
        row = []
        for b in LABELS:
            pr = [(lab[r["mint"]][a], lab[r["mint"]][b]) for r in tr if a in lab[r["mint"]] and b in lab[r["mint"]]]
            n11 = sum(1 for x, y in pr if x and y)
            n10 = sum(1 for x, y in pr if x and not y)
            n01 = sum(1 for x, y in pr if y and not x)
            n00 = len(pr) - n11 - n10 - n01
            den = ((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)) ** 0.5
            phi = (n11 * n00 - n10 * n01) / den if den else None
            row.append("n/a" if phi is None else "%.2f" % phi)
            if a < b and phi is not None:
                phis.append(abs(phi))
        lines.append("| %s | %s |" % (a, " | ".join(row)))
    score_ok = sum(1 for p in phis if p < 0.5) >= 3
    res["score_allowed"] = score_ok
    lines += [
        "",
        "Score (number of the four labels) %s."
        % (
            "allowed: at least three pairs of dimensions have |phi| below 0.5"
            if score_ok
            else "not built: the dimensions overlap"
        ),
    ]
    if score_ok:
        for sp in SPLITS:
            c = Counter(lab[r["mint"]]["score"] for r in rows if r["split"] == sp)
            lines.append("- %s: %s." % (sp.upper(), ", ".join("score %d: %d" % (k, c[k]) for k in sorted(c))))
    L.write("C3_labels.md", lines)
    # ---- C4 structure
    lines = [
        "# C4. Is coordination another name for the existing structure?",
        "",
        "| label | split | launches | snipers | bundle SOL | supply share | premium | market cap (log10 USD) "
        "| grouped |",
        "|---|---|---:|---|---|---|---|---|---:|",
    ]
    red: dict[str, Any] = {}
    names = ["b_core_n", "sol_bundle", "supply", "premium", "log_mc", "grouped"]

    def xrow(r: dict[str, Any]) -> dict[str, Any]:
        return {**{k: r["ctl"].get(k) for k in names[:-1]}, "grouped": 1.0 if r["actor"] == "grouped" else 0.0}

    for lb in allabs:
        for sp in SPLITS:
            sel = [r for r in rows if r["split"] == sp and lab[r["mint"]].get(lb)]
            if not sel:
                continue
            lines.append(
                "| %s | %s | %d | %s | %s | %s | %s | %s | %.0f %% |"
                % (
                    lb,
                    sp.upper(),
                    len(sel),
                    med3([r["ctl"]["b_core_n"] for r in sel]),
                    med3([r["ctl"]["sol_bundle"] for r in sel]),
                    med3([r["ctl"]["supply"] for r in sel]),
                    med3([r["ctl"]["premium"] for r in sel]),
                    med3([r["ctl"]["log_mc"] for r in sel]),
                    100 * sum(1 for r in sel if r["actor"] == "grouped") / len(sel),
                )
            )
        trd = [r for r in rows if r["split"] == "train" and lb in lab[r["mint"]]]
        vad = [r for r in rows if r["split"] == "val" and lb in lab[r["mint"]]]
        yt = [int(lab[r["mint"]][lb]) for r in trd]
        yv = [int(lab[r["mint"]][lb]) for r in vad]
        auc = None
        if 0 < sum(yt) < len(yt) and 0 < sum(yv) < len(yv):
            prep = fml.Prep(names).fit([xrow(r) for r in trd])
            m = fml.Boost(150).fit(prep.transform([xrow(r) for r in trd]), yt, [prep.cuts[n] for n in names])
            auc = fml.roc_auc(m.score(prep.transform([xrow(r) for r in vad])), yv)
        kp = kappa([bool(lab[r["mint"]][lb]) for r in vad], [r["actor"] == "grouped" for r in vad])
        red[lb] = {
            "auc": auc,
            "kappa_grouped": kp,
            "redundant": (auc is not None and auc >= 0.85) or (kp is not None and kp >= 0.8),
        }
    lines += [
        "",
        "## Redundancy rule (TRAIN boosting of snipers, bundle SOL, supply share, premium, market cap and "
        "grouped, measured on VALIDATION; Cohen's kappa with grouped on VALIDATION)",
        "",
        "| label | ROC-AUC | kappa with grouped | redundant |",
        "|---|---:|---:|---|",
    ]
    for lb, d in red.items():
        lines.append(
            "| %s | %s | %s | %s |"
            % (
                lb,
                "n/a" if d["auc"] is None else "%.3f" % d["auc"],
                "n/a" if d["kappa_grouped"] is None else "%.2f" % d["kappa_grouped"],
                "yes" if d["redundant"] else "no",
            )
        )
    res["redundancy"] = red
    L.write("C4_structure.md", lines)
    # ---- C5 robustness and operators
    lines = [
        "# C5. Robustness and operators",
        "",
        "Population null p of each label's raw criterion (the C2 test), and the label's prevalence, in each subset.",
        "",
    ]
    rob: dict[str, Any] = {}

    def subset_block(title: str, subsets: list[tuple[str, list[dict[str, Any]]]]) -> None:
        nonlocal lines
        lines += [
            "## " + title,
            "",
            "| subset | launches | " + " | ".join(LABELS) + " |",
            "|---|---:|" + "---|" * len(LABELS),
        ]
        for name, rr in subsets:
            if len(rr) < 20:
                lines.append("| %s | %d | %s |" % (name, len(rr), " | ".join(["too few"] * len(LABELS))))
                continue
            ln = label_nulls(rr)
            cells = []
            for lb in LABELS:
                k = sum(1 for r in rr if lab[r["mint"]].get(lb))
                cells.append("%d (%.0f %%), p %.3f" % (k, 100 * k / len(rr), ln[lb]["p"]))
            rob[(title, name).__str__()] = {lb: ln[lb]["p"] for lb in LABELS}
            lines.append("| %s | %d | %s |" % (name, len(rr), " | ".join(cells)))
        lines.append("")

    by_split = {sp: [r for r in rows if r["split"] == sp] for sp in SPLITS}
    subset_block("Splits", [(sp.upper(), by_split[sp]) for sp in SPLITS])
    wk: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        wk[int(r["t"] // (7 * 86400))].append(r)
    subset_block(
        "Weeks", [(min(r["utc"][:10] for r in v) + " " + v[0]["split"].upper(), v) for _, v in sorted(wk.items())]
    )
    subset_block(
        "Number of snipers",
        [
            ("%s, %s" % (k, sp.upper()), [r for r in by_split[sp] if f(len(r["snipers"]))])
            for sp in SPLITS
            for k, f in (("4", lambda n: n == 4), ("5", lambda n: n == 5), ("6+", lambda n: n >= 6))
        ],
    )
    trk = [statistics.median([s["ticket"] for s in r["snipers"]]) for r in by_split["train"]]
    t1, t2 = q(trk, 1 / 3), q(trk, 2 / 3)

    def tterc(r: dict[str, Any]) -> int:
        m = statistics.median([s["ticket"] for s in r["snipers"]])
        return 0 if m <= t1 else 1 if m <= t2 else 2

    subset_block(
        "Median ticket tercile (TRAIN cuts %.2f / %.2f SOL)" % (t1, t2),
        [
            ("tercile %d, %s" % (k + 1, sp.upper()), [r for r in by_split[sp] if tterc(r) == k])
            for sp in SPLITS
            for k in range(3)
        ],
    )
    top_cl = {sp: Counter(r["cluster"] for r in by_split[sp]).most_common(1)[0] for sp in SPLITS}
    cl_size = Counter(r["cluster"] for r in rows)
    subset_block(
        "Operators",
        [
            (name + ", " + sp.upper(), [r for r in by_split[sp] if f(r)])
            for sp in SPLITS
            for name, f in (
                ("all", lambda r: True),
                ("without the dominant operator", lambda r, sp=sp: r["cluster"] != top_cl[sp][0]),
                ("operators seen 2 times or more", lambda r: cl_size[r["cluster"]] >= 2),
                ("operators seen 5 times or more", lambda r: cl_size[r["cluster"]] >= 5),
                ("single launches only", lambda r: r["actor"] != "grouped"),
            )
        ],
    )
    wcount = Counter(s["wallet"] for r in rows for s in r["snipers"])
    top10 = {w for w, _ in wcount.most_common(10)}
    strip = []
    for sp in SPLITS:
        rr = []
        for r in by_split[sp]:
            sn = [s for s in r["snipers"] if s["wallet"] not in top10]
            if len(sn) >= 2:
                rr.append({**r, "snipers": sn})
        strip.append(("without the 10 most frequent sniper wallets, " + sp.upper(), rr))
    subset_block("Dominant wallets (their records removed; labels as computed on the full launches)", strip)
    lines += [
        "Dominant operator: %s." % "; ".join("%s %d launches" % (sp.upper(), top_cl[sp][1]) for sp in SPLITS),
        "The 10 most frequent sniper wallets appear in %d launches together."
        % len({r["mint"] for r in rows for s in r["snipers"] if s["wallet"] in top10}),
    ]
    L.write("C5_robustness.md", lines)
    res["robustness"] = rob
    # ---- C6 price, measured after
    lines = [
        "# C6. Premium and market cap, measured after the labels (never used to define them)",
        "",
        "| label | split | bundle SOL tercile | launches | premium | market cap (log10 USD) |",
        "|---|---|---|---:|---|---|",
    ]
    bs = [r["ctl"]["sol_bundle"] for r in by_split["train"]]
    b1, b2 = q(bs, 1 / 3), q(bs, 2 / 3)
    for lb in allabs:
        for sp in SPLITS:
            for k, f in ((1, lambda x: x <= b1), (2, lambda x: b1 < x <= b2), (3, lambda x: x > b2)):
                for yes in (True, False):
                    sel = [r for r in by_split[sp] if f(r["ctl"]["sol_bundle"]) and lab[r["mint"]].get(lb) is yes]
                    if sel:
                        lines.append(
                            "| %s %s | %s | %d | %d | %s | %s |"
                            % (
                                "" if yes else "not",
                                lb,
                                sp.upper(),
                                k,
                                len(sel),
                                med3([r["ctl"]["premium"] for r in sel]),
                                med3([r["ctl"]["log_mc"] for r in sel]),
                            )
                        )
    for sp in SPLITS:
        pr = [
            (r["ctl"]["premium"], r["ctl"]["sol_bundle"], r["ctl"]["supply"])
            for r in by_split[sp]
            if r["ctl"]["premium"] is not None
        ]
        lines.append("")
        lines.append(
            "%s: Spearman of the premium with bundle SOL %.2f, with the bundle's supply share %.2f."
            % (
                sp.upper(),
                spearman([a for a, _, _ in pr], [b for _, b, _ in pr]),
                spearman([a for a, _, _ in pr], [c for _, _, c in pr]),
            )
        )
    L.write("C6_price.md", lines)
    # ---- C7 exits, secondary
    lines = [
        "# C7. Exits up to alert + 30 s, secondary and descriptive (labels fixed before)",
        "",
        "| label | split | launches | snipers exiting by + 30 s | launches with two snipers exiting in one slot "
        "| buy-to-exit delay, median (s) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for lb in allabs:
        for sp in SPLITS:
            sel = [r for r in by_split[sp] if lab[r["mint"]].get(lb)]
            if not sel:
                continue
            sn = [s for r in sel for s in r["snipers"]]
            ex = [s for s in sn if s["exits"]]
            same = sum(
                1
                for r in sel
                if max(
                    Counter(min(x["slot"] for x in s["exits"]) for s in r["snipers"] if s["exits"]).values(), default=0
                )
                >= 2
            )
            dl = [
                min(x["bt"] for x in s["exits"] if x["bt"]) - s["bt"]
                for s in ex
                if s["bt"] and any(x["bt"] for x in s["exits"])
            ]
            lines.append(
                "| %s | %s | %d | %.0f %% | %.0f %% | %s |"
                % (
                    lb,
                    sp.upper(),
                    len(sel),
                    100 * len(ex) / len(sn),
                    100 * same / len(sel),
                    "%.0f" % statistics.median(dl) if dl else "n/a",
                )
            )
    L.write("C7_exits.md", lines)
    # ---- C8 classification
    lines = [
        "# C8. Classification of each discovery (rules of analysis_plan.md)",
        "",
        "| label | decided on | p TRAIN | p VAL | redundant | without dominant operator p (TRAIN / VAL) | "
        "largest cluster share | every week | without dominant wallets p (TRAIN / VAL) | class |",
        "|---|---|---:|---:|---|---|---:|---|---|---|",
    ]
    cls_out = {}
    for lb in LABELS:
        dec = sum(1 for r in rows if lb in lab[r["mint"]]) / len(rows)
        pt, pv = (nulls[sp][LABEL_NULL[lb]]["p"] for sp in SPLITS)
        wo = [rob[("Operators", "without the dominant operator, " + sp.upper()).__str__()][lb] for sp in SPLITS]
        wd = [
            rob[
                (
                    "Dominant wallets (their records removed; labels as computed on the full launches)",
                    "without the 10 most frequent sniper wallets, " + sp.upper(),
                ).__str__()
            ][lb]
            for sp in SPLITS
        ]
        labeled = [r for r in rows if lab[r["mint"]].get(lb)]
        top_share = (Counter(r["cluster"] for r in labeled).most_common(1)[0][1] / len(labeled)) if labeled else 0.0
        weeks_ok = all(any(lab[r["mint"]].get(lb) for r in v) for v in wk.values())
        if dec < 0.5:
            c = "INSUFFICIENT DATA"
        elif pt >= 0.05 or pv >= 0.05:
            c = "RANDOM / NULL-COMPATIBLE"
        elif red[lb]["redundant"]:
            c = "PRICE/STRUCTURE REDUNDANT"
        elif any(p >= 0.05 for p in wo) or top_share >= 0.5:
            c = "OPERATOR-SPECIFIC"
        elif pt < 0.01 and pv < 0.01 and weeks_ok and all(p < 0.05 for p in wd):
            c = "ROBUST COORDINATION PATTERN"
        else:
            c = "PROBABLE COORDINATION PATTERN"
        cls_out[lb] = c
        lines.append(
            "| %s | %.0f %% | %.3f | %.3f | %s | %.3f / %.3f | %.0f %% | %s | %.3f / %.3f | **%s** |"
            % (
                lb,
                100 * dec,
                pt,
                pv,
                "yes" if red[lb]["redundant"] else "no",
                wo[0],
                wo[1],
                100 * top_share,
                "yes" if weeks_ok else "no",
                wd[0],
                wd[1],
                c,
            )
        )
    res["classification"] = cls_out
    L.write("C8_classification.md", lines)
    with open(os.path.join(L.STUDY, "derived", "C_results.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("\n".join(lines))


def spearman(a: list[float], b: list[float]) -> float:
    def ranks(v: list[float]) -> list[float]:
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r

    ra, rb = ranks(a), ranks(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


if __name__ == "__main__":
    main()
