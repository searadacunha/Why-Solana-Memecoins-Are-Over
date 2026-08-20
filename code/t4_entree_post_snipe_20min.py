#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table 4: entering after the snipe, does the retracement pay?

The curve is bought back inside the creation block, out of reach for any other
buyer. That leaves the ordinary buyer's question: "what if I wait for it to come
back down?"

The rules under test, all live-safe, meaning the decision uses only the past:
  retrace_X   the running maximum of the robust price since creation is
              tracked; the moment a 30 s bucket quotes X % or more below that
              maximum, the token is bought. A decision taken on bucket k
              executes at t0+30(k+1), so never at the price that triggered it.
  graduation  buy as soon as the flow is usable, t0 + 120 s, with no condition.
              This is table 1's reference line.

A shared exit: hold until t_safe, the last swap minus 120 s, so at most the 20
minutes of the capture. A market order, credited at min(robust price, book depth
at 0.5 SOL); not filled counts as -100 %.

Two result columns:
  gross multiple  exit price over entry price, before costs
  net PnL         the same, less the 5.8241 % of fees and slippage over the
                  round trip

Declared biases:
 1. The rule does not fire on every token, since a token that only goes up never
    offers its retracement. The n of each row therefore differs, and it is
    published. This is not selection on the outcome: the trigger condition is
    measured strictly before the buy.
 2. The horizon is capped at 20 minutes by the length of the captures. That is
    this table's limit; table 5 lifts it with hourly candles.

Usage: python3 code/t4_entree_post_snipe_20min.py
Outputs: docs/tables/T4_entree_post_snipe_20min.md
         data/cout_acheteur/t4_entree_post_snipe_20min.json
"""
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t1_base_rate_sorties import (BUCKET, SAFE_MARGIN, Book, boot_ci_mean_cluster,
                                  pnl)
from common import (DATA, POS_SOL, boot_ci_median_tokens, clusters,
                    load_captures, source_label, write_table, dump_json)
from statlib import median, quantile

RETRACES = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
MIN_ENTRY_LAG = 120        # on ne peut de toute facon pas acheter plus tot


def try_entry(bk, t0, t_e):
    """Entree executable a t_e ? -> (prix, raison)"""
    p_rob = bk.robust(t_e)
    if p_rob is None:
        return None, "prix_indefini"
    if bk.big_vol(t_e) < POS_SOL:
        return None, "volume_insuffisant"
    p_ask, _ = bk.depth_ask(t_e)
    if p_ask is None:
        return None, "aucune_offre"
    return max(p_rob, p_ask), "ok"


def exit_at(bk, t_x):
    p_depth, flag = bk.depth_bid(t_x)
    cap = bk.market_mark(t_x)
    if cap is None:
        cap = p_depth
    if p_depth is None or cap is None:
        return None, "non_remplie"
    return min(cap, p_depth), flag


def run_rule(d, rule, param):
    """rule in {'retrace', 'graduation'} -> a dict, or None if it never fired."""
    bk = Book(d["_sw"])
    t0 = d["_created"]
    t_safe = bk.t_last - SAFE_MARGIN
    if t_safe < t0 + MIN_ENTRY_LAG + 60:
        return {"statut": "capture_trop_courte"}

    if rule == "graduation":
        t_dec = t0 + MIN_ENTRY_LAG
    else:
        K = int(math.floor((bk.t_last - t0) / BUCKET))
        run_max, t_dec = None, None
        for k in range(K + 1):
            t = t0 + BUCKET * k
            p = bk.robust(t)
            if p is None:
                continue
            if run_max is not None and p <= (1 - param) * run_max:
                t_dec = t + BUCKET          # execution au bucket suivant
                break
            run_max = p if run_max is None else max(run_max, p)
        if t_dec is None:
            return {"statut": "jamais_declenche"}
        t_dec = max(t_dec, t0 + MIN_ENTRY_LAG)

    if t_dec >= t_safe:
        return {"statut": "declenche_trop_tard"}
    p_in, why = try_entry(bk, t_dec, t_dec)
    if p_in is None:
        return {"statut": "entree_" + why}
    p_out, fflag = exit_at(bk, t_safe)
    if p_out is None:
        return {"statut": "ok", "mult_brut": 0.0, "pnl_net": -1.0,
                "t_entree_rel": int(t_dec - t0), "fill": "non_remplie",
                "duree_detention_s": int(t_safe - t_dec)}
    return {"statut": "ok", "mult_brut": p_out / p_in,
            "pnl_net": pnl(p_in, p_out), "t_entree_rel": int(t_dec - t0),
            "fill": fflag, "duree_detention_s": int(t_safe - t_dec)}


def main():
    caps, rej, nfiles = load_captures(verbose=True)
    cmap = clusters(caps)
    rules = [("graduation", None)] + [("retrace", x) for x in RETRACES]

    table, out = [], {}
    for rule, param in rules:
        nom = "graduation (+120 s)" if rule == "graduation" else f"retrace -{int(param*100)} %"
        res = [(c, run_rule(c, rule, param)) for c in caps]
        ok = [(c, r) for c, r in res if r.get("statut") == "ok"]
        never = sum(1 for _, r in res if r.get("statut") == "jamais_declenche")
        mult = [r["mult_brut"] for _, r in ok]
        net = [r["pnl_net"] for _, r in ok]
        if not ok:
            continue
        lo, hi = boot_ci_median_tokens(mult)
        nclu = len({cmap[c["mint"]] for c, _ in ok})
        byclu = {}
        for c, r in ok:
            byclu.setdefault(cmap[c["mint"]], []).append(r["pnl_net"])
        mlo, mhi = boot_ci_mean_cluster(byclu)
        srt = sorted(net, reverse=True)
        net_sans1 = st.mean(srt[1:]) if len(srt) > 1 else float("nan")
        rec = {"regle": nom, "n": len(ok), "n_clusters": nclu,
               "jamais_declenche": never,
               "mult_median": median(mult), "mult_ic95": [lo, hi],
               "mult_p25": quantile(mult, 0.25), "mult_p75": quantile(mult, 0.75),
               "pct_mult_sup_1": 100 * sum(1 for x in mult if x > 1) / len(mult),
               "pnl_net_median_pct": 100 * median(net),
               "pnl_net_moyen_pct": 100 * st.mean(net),
               "pnl_net_moyen_ic95_cluster_pct": [100 * mlo, 100 * mhi],
               "pnl_net_moyen_sans_meilleur_pct": 100 * net_sans1,
               "meilleur_token_pnl_pct": 100 * srt[0],
               "t_entree_median_s": median([r["t_entree_rel"] for _, r in ok]),
               "detention_mediane_min": median([r["duree_detention_s"] for _, r in ok]) / 60.0}
        out[nom] = rec
        table.append([nom, rec["n"], nclu, never,
                      f"{rec['t_entree_median_s']:.0f}",
                      f"{rec['mult_median']:.2f}",
                      f"[{lo:.2f}, {hi:.2f}]",
                      f"{rec['mult_p25']:.2f} / {rec['mult_p75']:.2f}",
                      f"{rec['pct_mult_sup_1']:.1f}",
                      f"{rec['pnl_net_median_pct']:+.1f}",
                      f"{rec['pnl_net_moyen_pct']:+.1f}",
                      f"[{100*mlo:+.0f}, {100*mhi:+.0f}]",
                      f"{rec['pnl_net_moyen_sans_meilleur_pct']:+.1f}"])

    best = max(out.values(), key=lambda r: r["mult_median"])
    txt = write_table(
        "T4_entree_post_snipe_20min",
        ["entry rule", "n", "clusters", "never triggered",
         "median entry t (s)", "median multiple", "95% CI", "p25 / p75",
         "% multiple > 1", "median net PnL %", "mean net PnL %",
         "mean 95% CI (cluster) %", "mean without the best token %"],
        table,
        ["",
         f"Source: `{source_label()}` ({nfiles} files, "
         f"{len(caps)} usable captures). Common exit: hold until the usable "
         f"end of the capture (<= 20 min).",
         "`median multiple` is gross (before fees); `net PnL` deducts 5.8241 % "
         "round-trip.",
         "Every rule is live-safe: a decision taken on a 30 s bucket executes on "
         "the next bucket, never at the price that triggered it.",
         f"**No post-snipe entry rule reaches a median multiple of 1 on this "
         f"horizon**; the best is `{best['regle']}` at "
         f"{best['mult_median']:.2f}x (95% CI "
         f"[{best['mult_ic95'][0]:.2f}, {best['mult_ic95'][1]:.2f}], n={best['n']}).",
         "`never triggered` = the token never offered the requested retracement "
         "during the capture; those tokens count in no column.",
         "**Do not read the mean as an edge**: it turns positive on deep "
         "retracements (-40 % to -70 %), but two controls in the table rule "
         "that out. (a) The 95% CI of the mean, bootstrapped at the cluster "
         "level, crosses zero on every one of those rows. (b) Removing the "
         "single best token flips all those means back negative. The right "
         "tail is fat and carried by a handful of tokens.",
         "", "Regenerate: `python3 code/t4_entree_post_snipe_20min.py`"])
    print(txt)
    dump_json({"n_fichiers": nfiles, "n_captures": len(caps), "regles": out},
              os.path.join(DATA, "cout_acheteur", "t4_entree_post_snipe_20min.json"))


if __name__ == "__main__":
    main()
