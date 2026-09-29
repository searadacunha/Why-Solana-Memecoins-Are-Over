#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trade simulation on the frozen spot series: entry, exit rule, estimated costs.

What is simulated and what is not
  entry     the first price read at or after the latency L (pde.entry_point);
            L = 0 is P0 itself. A spot price, not a fill.
  exit      reads are scanned in order after the entry. TP: the first read at
            or above TP x entry; "touch" fills at exactly TP (a resting order,
            the optimistic reading), "next" fills at the following read (a
            bot that polls, then sells). SL: the first read at or below
            SL x entry, filled at that read (gaps through the stop are paid).
            TIMEOUT: the first read at or after entry + T, at that read.
            A trade counts only if its whole holding window [entry, entry + T]
            is observed under the coverage rule of pde.py, decided before the
            exit is looked at; otherwise it is CENSORED: excluded and counted,
            never scored.
  costs     estimated, not measured. A fee per leg (router + DEX), a fixed SOL
            amount per transaction (priority fee + tip), and constant-product
            price impact on both legs. Pool depth is not in the data: the SOL
            reserve is derived from the price as sqrt(K x price), with K taken
            from one migration read directly on chain by the detector's audit
            (67.4 SOL against 206.9 M tokens, K ~ 1.39e10), and from pump.fun's
            virtual reserves (30 SOL x 1.073e9 tokens) for an entry priced on
            the bonding curve. K is varied x0.5 and x2 as a sensitivity.
            Front-running, failed transactions and MEV are not modelled; all
            three only lower the result.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import pde

SOLUSD = {int(k): v for k, v in json.load(open(os.path.join(pde.DATA, "sol_usd_hourly.json")))
          ["close_by_hour"].items()}


def sol_usd(t: float) -> float:
    return SOLUSD[int(t) // 3600 * 3600]


def simulate(pts: list[tuple[float, float]], fine: bool, lat: float, tp: float, sl: Optional[float],
             timeout: float, exit_mode: str = "touch") -> dict[str, Any]:
    ent = pde.entry_point(pts, lat) if pts else None
    if ent is None:
        return {"status": "no_entry"}
    dt_e, m_e = ent
    # Eligibility is decided on coverage of the whole holding window, before
    # looking at the exit: otherwise a trade that takes profit early escapes a
    # later outage while a losing one does not, and the sample leans to winners.
    if not pde.window(pts, dt_e, timeout, fine)[1]:
        return {"status": "censored", "entry_mult": m_e}
    prev = dt_e
    after = [(dt, m) for dt, m in pts if dt > dt_e]
    for i, (dt, m) in enumerate(after):
        g = pde.GAP_FINE if (fine and dt <= pde.FINE_WINDOW) else pde.GAP_COARSE
        if dt - prev > g:
            return {"status": "censored", "entry_mult": m_e}
        prev = dt
        r = m / m_e
        if r >= tp:
            if exit_mode == "touch":
                return {"status": "ok", "reason": "tp", "gross": tp, "dt": dt - dt_e, "entry_mult": m_e}
            if i + 1 < len(after) and after[i + 1][0] - dt <= g:
                return {"status": "ok", "reason": "tp", "gross": after[i + 1][1] / m_e,
                        "dt": after[i + 1][0] - dt_e, "entry_mult": m_e}
            return {"status": "censored", "entry_mult": m_e}
        if sl is not None and r <= sl:
            return {"status": "ok", "reason": "sl", "gross": r, "dt": dt - dt_e, "entry_mult": m_e}
        if dt - dt_e >= timeout:
            return {"status": "ok", "reason": "timeout", "gross": r, "dt": dt - dt_e, "entry_mult": m_e}
    return {"status": "censored", "entry_mult": m_e}


def net_return(gross: float, entry_mult: float, p0: float, source: str, t: float, size_usd: float,
               cost: dict[str, Any], k_scale: float = 1.0) -> float:
    s = size_usd / sol_usd(t)
    p_in = p0 * entry_mult
    k_in = (cost["k_curve"] if source == "courbe" else cost["k_pool"]) * k_scale
    r_in = (k_in * p_in) ** 0.5
    s_eff = s * (1 - cost["fee_per_leg"])
    q = s_eff / (p_in * (1 + s_eff / r_in))
    p_out = p_in * gross
    r_out = (cost["k_pool"] * k_scale * p_out) ** 0.5
    v = q * p_out
    recv = v / (1 + v / r_out) * (1 - cost["fee_per_leg"])
    return (recv - s - 2 * cost["fixed_sol_per_tx"]) / s


def summarise(res: list[tuple[str, dict[str, Any], Optional[float]]]) -> dict[str, Any]:
    """res = [(cluster, sim, net or None)] -> counts, gross and net means, cluster CI of the net mean."""
    ok = [(c, s, n) for c, s, n in res if s["status"] == "ok"]
    out: dict[str, Any] = {"n": len(res), "n_ok": len(ok),
                           "n_censored": sum(1 for _, s, _ in res if s["status"] == "censored"),
                           "n_no_entry": sum(1 for _, s, _ in res if s["status"] == "no_entry")}
    if not ok:
        return out
    g = [s["gross"] - 1 for _, s, _ in ok]
    out["gross_mean"] = sum(g) / len(g)
    out["gross_median"] = pde.median(g)
    out["tp_rate"] = sum(1 for _, s, _ in ok if s["reason"] == "tp") / len(ok)
    nets = [(c, n) for c, _, n in ok if n is not None]
    if nets:
        out["net_mean"] = sum(n for _, n in nets) / len(nets)
        out["net_median"] = pde.median([n for _, n in nets])
        out["net_win"] = sum(1 for _, n in nets if n > 0) / len(nets)
        out["net_ci"] = pde.cluster_boot_mean(nets)
    return out


if __name__ == "__main__":
    # dev check on VALIDATION only: every alert, the user's S2 and a hold-to-2x at 1 h
    lock_cost = {"fee_per_leg": 0.01, "fixed_sol_per_tx": 0.005, "k_pool": 1.39e10, "k_curve": 30 * 1.073e9}
    S = pde.load_series()
    rows = [r for r in pde.read_rows("dataset_dev.jsonl.gz") if r["split"] == "val"]
    for name, tp, sl, to in (("S2 TP2 SL-20% 5m", 2.0, 0.8, 300), ("HOLD_1h TP2", 2.0, None, 3600)):
        for lat in (0, 10):
            res = []
            for r in rows:
                sim = simulate(S.get(r["mint"]) or [], r["fine"], lat, tp, sl, to)
                n = (net_return(sim["gross"], sim["entry_mult"], r["p0"], r["f"]["p0_source"], r["t"], 500, lock_cost)
                     if sim["status"] == "ok" else None)
                res.append((r["cluster"], sim, n))
            s = summarise(res)
            print(name, "L=%d" % lat, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()})
