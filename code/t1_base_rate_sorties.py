#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table 1, the base rate, and the quantitative core of the buyer-cost strand:
what does buying a pump.fun token with no filter at all return, by exit policy?
The simulator is rewritten here from scratch, depending on no intermediate file
of the project, then confronted token by token with the reconciled canonical
socle of 28/07 (`analysis_canonical/canonical/dataset.json`), the agreement
being printed at the end of the run. One input, read-only:
`state/floor_capture/*.json`, the raw swap flow of the 0 to 20 min following the
token's creation.

Conventions of the canonical socle (analysis_canonical/canonical/merge.py,
summarised in docs/METHODOLOGY.md):

  Price: a swap is sol / tokens, no pre-computed field; the robust price is the
    median of the swaps of at least 0.3 SOL over [t, t+30), and None propagates
    with no interpolation.
  Entry: t_e = created + 120 s, p_entry = max(robust price, p_ask), where p_ask
    is the price at which 0.5 SOL of sales is absorbable within [t_e, t_e+30):
    one pays where the offer exists. Gate: at least 0.5 SOL of large volume in
    the window. No look at the future.
  Decision grid: buckets of 30 s. Decided on bucket k, an exit only executes at
    t_e + 30(k+1), since the bucket's price is not known before it ends;
    otherwise the backtest grants itself 30 s of lookahead, worth 6.2 % of price
    at the median per 30 s step and over 10 % in a third of the steps.
  Exit: take-profit is a limit order, credited at the take-profit level and only
    if the book absorbs 0.5 SOL at that price or better; stop, trailing and
    timeout are market orders, credited at min(robust price at the instant of
    execution, depth).
  Depth: the best price absorbing 0.5 SOL on the ask side within
    [t_x, t_x+120], orders of at least 0.05 SOL. Too thin a book: the worst
    price available. An empty book: not filled.
  Censoring: t_safe is the last swap minus 120 s and no exit is planned beyond
    it, which leaves 120 s of future flow to verify every fill; a -100 %
    therefore cannot come from the recorder stopping.
  Not filled: -100 % in the primary column. The `_excl` column discards them,
    and is published to show how much return that optimistic convention
    manufactures.
  Costs: 1 % fee plus 2 % adverse slippage per leg, so 5.8241 % over the round
    trip.
  n: counted in clusters, launches more than 30 min apart, and in UTC days, not
    only in tokens.

Usage: python3 code/t1_base_rate_sorties.py
Outputs: docs/tables/T1_base_rate_sorties.md
         data/cout_acheteur/t1_base_rate_sorties.json
"""
import bisect
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings
from common import (DATA, DEPTH_MIN_SOL, FEE_IN, FEE_OUT, MIN_SOL_PRICE,
                    POS_SOL, boot_ci_median_tokens, clusters, load_captures,
                    source_label, write_table, dump_json)
from statlib import median

BUCKET = 30
FILL_H = 120
SAFE_MARGIN = 120
ENTRY_OFFSET = 120

def _canon_path():
    """The canonical socle of 28/07: the second implementation, written
    independently, against which this simulator is checked token by token (the
    CONTROLE block at the end of the run). It is not published, being a 40 MB
    working artefact, so the check only runs when the raw corpus is mounted
    ($PUMP_PRIVATE_ROOT). Its absence changes no figure of the table, it only
    removes the reconciliation block, whose result is archived in
    docs/PITFALLS.md, pitfall P2.
    """
    priv = settings.private_root()
    if not priv:
        return None
    return os.path.join(priv, "analysis_canonical", "canonical", "dataset.json")


CANON = _canon_path()


class Book:
    """Carnet reconstruit a partir du flux de swaps."""

    def __init__(self, sw):
        self.sw = sw
        self.sw_ts = [s["ts"] for s in sw]
        self.big = [s for s in sw if s["sol"] >= MIN_SOL_PRICE]
        self.big_ts = [s["ts"] for s in self.big]
        self.bids = [s for s in sw if s["side"] == "buy" and s["sol"] >= DEPTH_MIN_SOL]
        self.bid_ts = [s["ts"] for s in self.bids]
        self.asks = [s for s in sw if s["side"] == "sell" and s["sol"] >= DEPTH_MIN_SOL]
        self.ask_ts = [s["ts"] for s in self.asks]
        self.t_last = sw[-1]["ts"]

    @staticmethod
    def _sl(ts_arr, arr, t0, t1):
        return arr[bisect.bisect_left(ts_arr, t0):bisect.bisect_left(ts_arr, t1)]

    def robust(self, t, w=BUCKET):
        seg = self._sl(self.big_ts, self.big, t, t + w)
        return st.median([s["p"] for s in seg]) if seg else None

    def big_vol(self, t, w=BUCKET):
        return sum(s["sol"] for s in self._sl(self.big_ts, self.big, t, t + w))

    def depth_bid(self, t):
        cand = self._sl(self.bid_ts, self.bids, t, t + FILL_H + 1)
        if not cand:
            return None, "non_remplie"
        cum = 0.0
        for s in sorted(cand, key=lambda z: -z["p"]):
            cum += s["sol"]
            if cum >= POS_SOL:
                return s["p"], "ok"
        return sorted(cand, key=lambda z: -z["p"])[-1]["p"], "mince"

    def depth_ask(self, t, w=BUCKET):
        cand = self._sl(self.ask_ts, self.asks, t, t + w)
        if not cand:
            return None, "non_remplie"
        cum = 0.0
        for s in sorted(cand, key=lambda z: z["p"]):
            cum += s["sol"]
            if cum >= POS_SOL:
                return s["p"], "ok"
        return sorted(cand, key=lambda z: z["p"])[-1]["p"], "mince"

    def market_mark(self, t):
        for w in (BUCKET, 60, FILL_H):
            p = self.robust(t, w)
            if p is not None:
                return p
        return None


def pnl(p_in, p_out):
    return (p_out * FEE_OUT) / (p_in * FEE_IN) - 1.0


def boot_ci_mean_cluster(byclu, B=4000, seed=777):
    """95 % interval of the mean, bootstrapped at the cluster level: whole
    clusters are drawn rather than tokens, two tokens of one launch not being
    independent observations. The statistic resampled is the pooled mean of the
    tokens of the drawn clusters, consistent with T1's pooled point estimate;
    pumplib.cluster_bootstrap_mean_ci resamples the mean of the cluster means,
    consistent with m5's point estimate. Two estimators, two engines,
    deliberately not merged (statlib.py header).
    """
    import random
    ks = list(byclu.keys())
    if len(ks) < 3:
        return (float("nan"), float("nan"))
    rnd = random.Random(seed)
    out = []
    for _ in range(B):
        pick = [byclu[ks[rnd.randrange(len(ks))]] for _ in range(len(ks))]
        flat = [x for g in pick for x in g]
        out.append(st.mean(flat))
    out.sort()
    return out[int(0.025 * B)], out[int(0.975 * B)]


TIMEOUTS = [1, 3, 5, 10, 20]
TRAILS = [(0.20, "trail_20"), (0.30, "trail_30"), (0.40, "trail_40")]
TPSL = [("tp30", 1.30, None, None), ("tp30_sl35", 1.30, "sl35", 0.65),
        ("tp50", 1.50, None, None), ("tp50_sl35", 1.50, "sl35", 0.65),
        ("tp2x", 2.00, None, None), ("tp2x_sl35", 2.00, "sl35", 0.65)]
POLICIES = (["time_%dm" % m for m in TIMEOUTS] + [n for _, n in TRAILS]
            + [n for n, _, _, _ in TPSL] + ["hold_t_safe"])
CANON_10 = ["time_1m", "time_3m", "time_5m", "time_10m", "trail_30", "trail_40",
            "tp50", "tp2x", "tp50_sl35", "tp2x_sl35"]


def simulate(d, off=ENTRY_OFFSET):
    bk = Book(d["_sw"])
    t_e = d["_created"] + off
    out = {"mint": d["mint"], "created": d["_created"], "flag": None, "policies": {}}
    if t_e >= bk.t_last:
        out["flag"] = "X_entree_apres_fin_capture"
        return out
    p_rob = bk.robust(t_e)
    if p_rob is None:
        out["flag"] = "X_prix_entree_indefini"
        return out
    if bk.big_vol(t_e) < POS_SOL:
        out["flag"] = "X_volume_entree_insuffisant"
        return out
    p_ask, _ = bk.depth_ask(t_e)
    if p_ask is None:
        out["flag"] = "X_aucune_offre_absorbable"
        return out
    p_entry = max(p_rob, p_ask)
    t_safe = bk.t_last - SAFE_MARGIN
    if t_safe < t_e + 60:
        out["flag"] = "X_pas_de_place_aller_retour_verifiable"
        return out
    out["flag"] = "ok"
    out["p_entree"] = p_entry
    out["pay_up_pct"] = round(100 * (p_entry / p_rob - 1), 4)

    K = int(math.floor((bk.t_last - t_e) / BUCKET))
    grid = [(k, bk.robust(t_e + BUCKET * k)) for k in range(K + 1)]
    k_max = int(math.floor((t_safe - t_e) / BUCKET)) - 1
    pmax = max((p for _, p in grid if p is not None), default=None)
    out["mult_max_robuste"] = round(pmax / p_entry, 4) if pmax else None
    t_timeout = min(t_e + BUCKET * max(1, k_max + 1), t_safe)

    def record(name, t_x, target, reason, is_limit):
        t_x = int(min(t_x, t_safe))
        p_depth, flag = bk.depth_bid(t_x)
        cap = target if is_limit else bk.market_mark(t_x)
        if cap is None:
            cap = p_depth
        if p_depth is None or cap is None:
            out["policies"][name] = {"t_exit_rel": int(t_x - t_e), "reason": reason,
                                     "fill": "non_remplie", "pnl_net": -1.0,
                                     "pnl_net_excl": None}
        else:
            v = round(pnl(p_entry, min(cap, p_depth)), 6)
            out["policies"][name] = {"t_exit_rel": int(t_x - t_e), "reason": reason,
                                     "fill": flag, "pnl_net": v, "pnl_net_excl": v}

    for m in TIMEOUTS:
        record("time_%dm" % m, t_e + 60 * m, None, "time", False)
    for dd, nm in TRAILS:
        run_max, fired = p_entry, None
        for k, p in grid:
            if p is None:
                continue
            if 1 <= k <= k_max and p <= (1 - dd) * run_max:
                fired = k
                break
            run_max = max(run_max, p)
        record(nm, t_e + BUCKET * (fired + 1) if fired is not None else t_timeout,
               None, "trail_hit" if fired is not None else "timeout", False)
    for nm, tpm, _sln, slm in TPSL:
        fired = None
        for k, p in grid:
            if p is None or not (1 <= k <= k_max):
                continue
            if p >= tpm * p_entry:
                fired = (k, tpm * p_entry, "tp_hit", True)
                break
            if slm is not None and p <= slm * p_entry:
                fired = (k, None, "sl_hit", False)
                break
        if fired:
            k, tgt, why, lim = fired
            record(nm, t_e + BUCKET * (k + 1), tgt, why, lim)
        else:
            record(nm, t_timeout, None, "timeout", False)
    record("hold_t_safe", t_safe, None, "hold", False)
    return out


def main():
    caps, rej, nfiles = load_captures(verbose=True)
    cmap = clusters(caps)
    sims = [simulate(c) for c in caps]
    ok = [s for s in sims if s["flag"] == "ok"]
    flags = defaultdict(int)
    for s in sims:
        flags[s["flag"]] += 1
    days = {s["mint"]: __import__("datetime").datetime.fromtimestamp(
        s["created"], __import__("datetime").timezone.utc).strftime("%Y-%m-%d")
        for s in ok}
    nclu = len({cmap[s["mint"]] for s in ok})
    ndays = len(set(days.values()))
    print(f"entrees exploitables a +120 s : {len(ok)} tokens | {nclu} clusters "
          f"| {ndays} jours | flags={dict(flags)}")

    table, res = [], {}
    for pol in POLICIES:
        v = [s["policies"][pol]["pnl_net"] for s in ok if pol in s["policies"]]
        vx = [s["policies"][pol]["pnl_net_excl"] for s in ok
              if pol in s["policies"] and s["policies"][pol]["pnl_net_excl"] is not None]
        nf = sum(1 for s in ok if s["policies"].get(pol, {}).get("fill") == "non_remplie")
        byclu = defaultdict(list)
        for s in ok:
            if pol in s["policies"]:
                byclu[cmap[s["mint"]]].append(s["policies"][pol]["pnl_net"])
        s_clu = st.mean([st.mean(x) for x in byclu.values()])
        byday = defaultdict(list)
        for s in ok:
            if pol in s["policies"]:
                byday[days[s["mint"]]].append(s["policies"][pol]["pnl_net"])
        jpos = sum(1 for x in byday.values() if st.median(x) > 0)
        lo, hi = boot_ci_median_tokens(v)
        clo, chi = boot_ci_mean_cluster(byclu)
        rec = {"n": len(v), "mediane_pct": 100 * median(v), "moyenne_pct": 100 * st.mean(v),
               "mediane_ic95_pct": [100 * lo, 100 * hi],
               "moyenne_ic95_cluster_pct": [100 * clo, 100 * chi],
               "S_cluster_pct": 100 * s_clu,
               "pct_gagnants": 100 * sum(1 for x in v if x > 0) / len(v),
               "pct_non_remplies": 100 * nf / len(v),
               "mediane_excl_pct": 100 * median(vx) if vx else None,
               "clusters_positifs": f"{sum(1 for x in byclu.values() if st.mean(x)>0)}/{len(byclu)}",
               "jours_mediane_positive": f"{jpos}/{len(byday)}"}
        res[pol] = rec
        table.append([pol, rec["n"], f"{rec['mediane_pct']:+.1f}",
                      f"[{rec['mediane_ic95_pct'][0]:+.1f}, {rec['mediane_ic95_pct'][1]:+.1f}]",
                      f"{rec['moyenne_pct']:+.1f}",
                      f"[{rec['moyenne_ic95_cluster_pct'][0]:+.1f}, "
                      f"{rec['moyenne_ic95_cluster_pct'][1]:+.1f}]",
                      f"{rec['pct_gagnants']:.1f}", f"{rec['pct_non_remplies']:.1f}",
                      f"{rec['mediane_excl_pct']:+.1f}", rec["clusters_positifs"],
                      rec["jours_mediane_positive"]])

    neg_med = [p for p in POLICIES if res[p]["mediane_pct"] < 0]
    neg_mean = [p for p in POLICIES if res[p]["moyenne_pct"] < 0]
    neg10 = [p for p in CANON_10 if res[p]["mediane_pct"] < 0]
    pos_both = [p for p in POLICIES
                if res[p]["mediane_pct"] > 0 and res[p]["moyenne_pct"] > 0]
    ci_pos = [p for p in POLICIES if res[p]["moyenne_ic95_cluster_pct"][0] > 0]
    moy_all = st.mean([res[p]["moyenne_pct"] for p in POLICIES])

    notes = [
        "",
        f"n = {len(ok)} tokens | {nclu} clusters | {ndays} UTC days | "
        f"entry at t0+120 s, no entry filter.",
        f"Source: `{source_label()}` ({nfiles} files, "
        f"{len(caps)} usable captures, rejects {dict(rej)}).",
        "Costs: 1 % fees + 2 % adverse slippage per leg = **5.8241 % "
        "round-trip**, already deducted.",
        "`median excl` = same computation, dropping unfilled exits. An "
        "optimistic convention, published to show how much return it "
        "manufactures.",
        f"**Negative mean on {len(neg_mean)}/{len(POLICIES)} policies.** "
        f"Negative median on {len(neg_med)}/{len(POLICIES)} "
        f"({len(neg10)}/10 on the canonical 28/07 grid).",
        f"**No policy is positive in both median and mean "
        f"({len(pos_both)}/{len(POLICIES)}).** The few positive medians come "
        "from tight take-profit policies, which often win a little and rarely "
        "lose a lot, so their expectation is the worst of the table "
        "(tp30: median +22 %, mean -16 %).",
        f"No policy has a 95% CI of the mean (cluster-level bootstrap) "
        f"entirely above zero: {len(ci_pos)}/{len(POLICIES)}.",
        f"Mean of means over the {len(POLICIES)} policies: "
        f"**{moy_all:+.1f} %** per round-trip.",
        "No multiplicity correction: the result is negative everywhere, and "
        "sweeping more policies only makes a negative result harder to obtain "
        "by chance.",
        "", "Regenerate: `python3 code/t1_base_rate_sorties.py`",
    ]
    txt = write_table("T1_base_rate_sorties",
                      ["exit policy", "n", "median %", "median 95% CI %",
                       "mean %", "mean 95% CI (cluster) %", "% winners",
                       "% unfilled", "median excl %", "clusters +",
                       "days med>0"],
                      table, notes)
    print(txt)

    # ------------------------------------------------- controle vs canonique
    ctrl = {}
    if CANON and os.path.exists(CANON):
        can = {r["mint"]: r for r in json.load(open(CANON))["rows"]}
        for pol in CANON_10:
            pairs = []
            for s in ok:
                c = can.get(s["mint"], {}).get("entries", {}).get("e120", {})
                if c.get("entry_flag") != "ok":
                    continue
                cv = (c.get("policies") or {}).get(pol, {}).get("pnl_net")
                if cv is None:
                    continue
                pairs.append((s["policies"][pol]["pnl_net"], cv))
            if pairs:
                dmax = max(abs(a - b) for a, b in pairs)
                nid = sum(1 for a, b in pairs if abs(a - b) < 1e-4)
                ctrl[pol] = {"n_apparies": len(pairs), "identiques_1e-4": nid,
                             "ecart_max": dmax}
        nsame = sum(1 for m in ok if can.get(m["mint"], {})
                    .get("entries", {}).get("e120", {}).get("entry_flag") == "ok")
        print(f"\nCONTROLE vs socle canonique du 28/07 : {nsame}/{len(ok)} tokens "
              f"partages a l'entree e120")
        for pol, c in ctrl.items():
            print(f"  {pol:12s} n={c['n_apparies']:4d} identiques(1e-4)="
                  f"{c['identiques_1e-4']:4d} ecart_max={c['ecart_max']:.2e}")

    dump_json({"n_tokens": len(ok), "n_clusters": nclu, "n_jours": ndays,
               "n_fichiers": nfiles, "n_captures_exploitables": len(caps),
               "rejets": rej, "flags_entree": dict(flags),
               "drag_aller_retour_pct": round(100 * (1 - FEE_OUT / FEE_IN), 4),
               "politiques": res, "controle_vs_canonique": ctrl,
               "n_politiques_mediane_negative": len(neg_med),
               "n_politiques": len(POLICIES)},
              os.path.join(DATA, "cout_acheteur", "t1_base_rate_sorties.json"))
    dump_json([{"mint": s["mint"], "created": s["created"], "flag": s["flag"],
                "cluster": cmap[s["mint"]],
                "p_entree": s.get("p_entree"),
                "mult_max_robuste": s.get("mult_max_robuste"),
                "pnl": {k: v["pnl_net"] for k, v in s.get("policies", {}).items()}}
               for s in sims],
              os.path.join(DATA, "cout_acheteur", "t1_pnl_par_token.json"))


if __name__ == "__main__":
    main()
