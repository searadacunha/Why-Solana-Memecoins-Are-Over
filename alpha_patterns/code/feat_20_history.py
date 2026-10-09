#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feat_20_history.py -- causal 1 h track records of the actors behind a launch (families D, E, F, G).

Decision time t_i = the alert. Identity keys of alert i come from its own detector record (sniper
wallets, creator, ticket configuration) and from cd_table (funders funded before t_i - 1 s, early
buyers with block time <= t_i - 1 s). An earlier alert j is
  - a PRIOR   if t_j + 60 <= t_i (counts, recency: no outcome involved);
  - RESOLVED  if t_j + RESOLVE_1H <= t_i - 1 and its 1 h window was observed: only then may its
    outcome (Y2 / Y3 / Y5 at 1 h from the +5 s entry, MFE, trade net) enter a feature of alert i.
RESOLVE_1H = 3600 s horizon + 15 s entry tolerance + 135 s coverage gap + 60 s margin = 3810 s.
Hub flags: a funder flagged hub is dropped only if that flag was knowable (the address was already
a genesis funder of an alert with t_j <= t_i); otherwise it is kept as unknown.
Keys stay separate; "any" is the direct union w | c | k | f, never a transitive closure.

Outcomes of every block feed the history of LATER alerts only; no rate is printed.
"""
from __future__ import annotations

import math
import os
from collections import Counter, defaultdict

import ap_lib as A

M_SHRINK = 10.0
MIN_GLOBAL = 30
MIN_REG = 5
KS = (2, 3, 5)


def config_key(tickets):
    return "+".join("%.2f" % x for x in sorted(tickets, reverse=True)) if tickets else None


def load_keys(base):
    t_of = {b["mint"]: b["t"] for b in base}
    first_gen_t: dict[str, float] = {}
    cd = {}
    for r in A.jl(A.CD_TABLE):
        cd[r["mint"]] = r
        for s in r["snipers"] + [r["creator"]]:
            g = s.get("gen_funder")
            if g:
                first_gen_t[g] = min(first_gen_t.get(g, math.inf), r["t"])
    alerts = {}
    for r in A.jl(A.JOURNAL):
        if r.get("genre") == "alerte_lancement":
            if r["mint"] in alerts:
                raise ValueError("duplicate alert " + r["mint"])
            alerts[r["mint"]] = r
    if set(alerts) != set(t_of) or set(cd) != set(t_of):
        raise ValueError("journal / cd_table do not cover the base")
    keys = {}
    rep: Counter = Counter()
    for m, a in alerts.items():
        t = t_of[m]
        if abs(a["t"] - t) > 1e-3 or abs(cd[m]["t"] - t) > 1e-3:
            raise ValueError("t mismatch " + m)
        w = {"w:" + x for x in (a.get("snipers") or [])}
        c = {"c:" + a["createur"]} if a.get("createur") else set()
        ck = config_key(a.get("tickets") or a["bloc"].get("tickets"))
        k = {"k:" + ck} if ck else set()
        cnt: Counter = Counter()
        for s in cd[m]["snipers"]:
            cand = set()
            for fk, bk, hk in (("last_funder", "last_bt", "last_funder_hub"), ("gen_funder", "gen_bt", "gen_funder_hub")):
                fu = s.get(fk)
                if not fu:
                    continue
                if s.get(bk) is None:
                    raise ValueError("funder without block time " + m)
                if s[bk] >= t - 1:
                    rep["funder_after_cut_dropped"] += 1
                    continue
                h = s.get(hk)
                if h is True and not first_gen_t.get(fu, math.inf) <= t:
                    h = None
                    rep["hub_flag_not_yet_knowable"] += 1
                if h is not True:
                    cand.add(fu)
            for fu in cand:
                cnt[fu] += 1
        mx = max(cnt.values(), default=0)
        f = {"f:" + fu for fu, v in cnt.items() if v == mx} if mx >= 2 else set()
        skip = {x[2:] for x in w} | {x[2:] for x in c}
        e = set()
        for x in cd[m]["early"]:
            if x.get("pre_alert") and x["bt"] <= t - 1 and x["wallet"] not in skip:
                e.add(x["wallet"])
        keys[m] = {"w": w, "c": c, "k": k, "f": f, "any": w | c | k | f, "e": e}
        for kt in ("w", "c", "k", "f", "e"):
            rep["alerts_without_" + kt] += not keys[m][kt]
    return keys, dict(rep)


def shrunk(hits, n, p):
    return (hits + M_SHRINK * p) / (n + M_SHRINK) - p


def outcomes_from_labels(base, lab):
    """Outcome record of alert j (fine regime, entry, observed 1 h window), or None."""
    out = []
    for b in base:
        r = lab[b["mint"]]
        if r.get("fine") and r.get("entry") and r.get("obs_3600"):
            tr = r["trades"]["tp2_next"]
            out.append({"y": {k: r["conf_%gx_3600" % k] for k in KS}, "lmfe": math.log(max(r["mfe_3600"], 1e-6)),
                        "net": tr.get("net_500") if tr["status"] == "ok" else None})
        else:
            out.append(None)
    return out


def main() -> None:
    base = A.load_base()
    keys, rep = load_keys(base)
    lab = {r["mint"]: r for r in A.jl(os.path.join(A.DERIVED, "labels.jsonl.gz"))}
    out = outcomes_from_labels(base, lab)
    feats = build(base, keys, out)
    A.write_jl(os.path.join(A.DERIVED, "feat_history1h.jsonl.gz"), feats)
    names = [k for k in feats[0] if k != "mint"]
    cov = {k: sum(1 for r in feats if r[k] is not None) for k in names}
    A.write_json(os.path.join(A.DERIVED, "feat_history1h_coverage.json"), {"keys_report": rep, "non_null": cov})
    print("features", len(names), "outcome records", sum(1 for o in out if o is not None))
    print(rep)


def build(base, keys, out):
    """Causal history features of every alert from the outcome records `out` (same order as base).
    Shared by the real build and by the synthetic controls (which pass synthetic outcomes)."""
    n = len(base)
    t = [b["t"] for b in base]

    by_key: dict[str, list[int]] = defaultdict(list)     # identity key -> earlier alert indices
    by_early: dict[str, list[int]] = defaultdict(list)   # early wallet -> earlier alert indices
    feats = []
    res_ptr = 0
    g_n = 0
    g_hits = {k: 0 for k in KS}
    g_lmfe = 0.0
    g_net_n, g_net = 0, 0.0
    resolved_order = sorted(range(n), key=lambda j: t[j])   # base is chronological already
    for i, b in enumerate(base):
        ti = t[i]
        # advance the causal global means over alerts resolved before t_i - 1
        while res_ptr < n and t[resolved_order[res_ptr]] + A.RESOLVE_1H <= ti - 1:
            o = out[resolved_order[res_ptr]]
            if o is not None:
                g_n += 1
                for k in KS:
                    g_hits[k] += o["y"][k]
                g_lmfe += o["lmfe"]
                if o["net"] is not None:
                    g_net_n += 1
                    g_net += o["net"]
            res_ptr += 1
        f: dict[str, float | None] = {}
        p = {k: (g_hits[k] / g_n if g_n >= MIN_GLOBAL else None) for k in KS}
        ks = keys[b["mint"]]
        for kt in ("w", "c", "k", "f", "any"):
            pri = set()
            for key in ks[kt]:
                for j in by_key[key]:
                    if t[j] + 60 <= ti:
                        pri.add(j)
            res = [j for j in pri if t[j] + A.RESOLVE_1H <= ti - 1 and out[j] is not None]
            f["h1_npri_" + kt] = float(len(pri))
            f["h1_nres_" + kt] = float(len(res))
            for k in KS:
                f["h1_ex%d_%s" % (k, kt)] = (shrunk(sum(out[j]["y"][k] for j in res), len(res), p[k])
                                             if (res and p[k] is not None) else None)
            if kt == "any":
                if res and g_n >= MIN_GLOBAL:
                    gm = g_lmfe / g_n
                    f["h1_mfe_any"] = (sum(out[j]["lmfe"] for j in res) + M_SHRINK * gm) / (len(res) + M_SHRINK) - gm
                    f["h1_best_any"] = max(out[j]["lmfe"] for j in res)
                    last = max(res, key=lambda j: t[j])
                    f["h1_last2_any"] = float(out[last]["y"][2])
                    nets = [out[j]["net"] for j in res if out[j]["net"] is not None]
                    f["h1_net_any"] = ((sum(nets) + M_SHRINK * (g_net / g_net_n)) / (len(nets) + M_SHRINK) - g_net / g_net_n
                                       if (nets and g_net_n >= MIN_GLOBAL) else None)
                else:
                    f["h1_mfe_any"] = f["h1_best_any"] = f["h1_last2_any"] = f["h1_net_any"] = None
                f["h1_since_any"] = math.log10(max(ti - max(t[j] for j in pri), 1.0)) if pri else None
                f["h1_n24_any"] = float(sum(1 for j in pri if t[j] >= ti - 86400))
        # early buyers seen before the alert: were their earlier launches winners?
        ew = ks["e"]
        f["h1_e_n"] = float(len(ew))
        known, exs = 0, {k: [] for k in KS}
        smart = {k: 0 for k in KS}
        for wal in ew:
            pri = [j for j in by_early[wal] if t[j] + 60 <= ti]
            known += bool(pri)
            res = [j for j in pri if t[j] + A.RESOLVE_1H <= ti - 1 and out[j] is not None]
            if len(res) >= 3:
                for k in KS:
                    if p[k] is not None:
                        ex = shrunk(sum(out[j]["y"][k] for j in res), len(res), p[k])
                        exs[k].append(ex)
                        if len(res) >= 5 and ex >= 0.10:
                            smart[k] += 1
        f["h1_e_known_share"] = known / len(ew) if ew else None
        for k in KS:
            f["h1_e_ex%d_mean" % k] = sum(exs[k]) / len(exs[k]) if exs[k] else None
            f["h1_e_ex%d_max" % k] = max(exs[k]) if exs[k] else None
            f["h1_e_smart%d_n" % k] = float(smart[k]) if (ew and p[k] is not None) else None
        # regime: resolved base rate over the recent past
        for win, tag in ((21600, "6h"), (86400, "24h")):
            res = [j for j in range(i) if ti - win <= t[j] and t[j] + A.RESOLVE_1H <= ti - 1 and out[j] is not None]
            for k in KS:
                f["h1_reg%d_%s" % (k, tag)] = (sum(out[j]["y"][k] for j in res) / len(res)) if len(res) >= MIN_REG else None
        feats.append({"mint": b["mint"], **f})
        # only now does alert i become visible to later alerts
        for key in ks["any"]:
            by_key[key].append(i)
        for wal in ew:
            by_early[wal].append(i)
    return feats


if __name__ == "__main__":
    main()
