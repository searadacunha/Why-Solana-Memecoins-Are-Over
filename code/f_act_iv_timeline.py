#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
f_act_iv_timeline.py -- Figure F5 for Act IV: where the information sits, 2024 against 2026.

Reads committed artefacts only, no network, no key:
  docs/out/a9_g2y_prelaunch.json                 the 2024 reference case (9 wallets, one amount, 343 s)
  data/v05_creation_block.json                    the 42 verified 2026 launches (SOL in the creation slot)
  data/v07_exit.json                              the same 42 launches (first transfer out of the sniper wallets)
  alpha_patterns/tables/team_absorption.json      the 1,015 alerts of 2026-08-21 -> 09-14: medians of the
                                                  456 launches of the 33 teams, GOOD against BAD
  alpha_patterns/tables/x2_timing_summary.json    when the confirmed x2 arrives, counted from the entry
Writes figures/f5_act_iv_information_timing.png. matplotlib only (declared optional in run_all.py
--deps); the standard library for everything else.

  python3 code/f_act_iv_timeline.py
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs", "out")
AP = os.path.join(ROOT, "alpha_patterns", "tables")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

INK = "#1b1b1b"
GRID = "#d8d8d8"
GOOD = "#2f6f4e"
BAD = "#b5423a"
NEUTRE = "#4a6d8c"
ACCENT = "#c98a2b"
SHADE = "#f3e6cf"

plt.rcParams.update({
    "figure.dpi": 160, "savefig.dpi": 160, "font.size": 8.5,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
})


def jload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def pct(x):
    return "%.1f %%" % (100.0 * x)


def main():
    a9 = jload(os.path.join(OUT, "a9_g2y_prelaunch.json"))["cas_reference"]
    v05 = jload(os.path.join(DATA, "v05_creation_block.json"))["agregats"]
    v07 = jload(os.path.join(DATA, "v07_exit.json"))["agregats"]
    ta = jload(os.path.join(AP, "team_absorption.json"))
    x2 = jload(os.path.join(AP, "x2_timing_summary.json"))
    d = ta["mechanism"]["descriptive"]
    price = ta["mechanism"]["price_after_entry"]
    tl = ta["mechanism"]["timeline_medians"]
    n_good, n_bad = ta["mechanism"]["good"], ta["mechanism"]["bad"]

    fig = plt.figure(figsize=(9.6, 9.2))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.8, 2.3], hspace=0.62)

    # ------------------------------------------------------------- row 1: 2024
    ax = fig.add_subplot(gs[0])
    h_first = -a9["delai_creation_h_depuis_premier_credit"]
    h_last = -a9["delai_creation_h_depuis_dernier_credit"]
    ax.set_xlim(-8.6, 1.3)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.axhline(0.35, color=NEUTRE, lw=1.2, zorder=1)
    ax.axvspan(h_first, 0, color=SHADE, zorder=0)
    ax.plot([h_first, h_last], [0.35, 0.35], color=ACCENT, lw=7, solid_capstyle="butt", zorder=3)
    ax.plot([0], [0.35], marker="|", ms=18, mew=2.2, color=INK, zorder=4)
    ax.annotate("%d fresh wallets funded, %.9f SOL each,\nall within %d s (one swap-service hot wallet)"
                % (a9["n_portefeuilles"], a9["montant_sol"], a9["etendue_s"]),
                xy=(h_last, 0.35), xytext=(h_last + 0.25, 0.78), fontsize=8,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
    ax.text((h_first + 0) / 2, 0.14, "public signal %.1f h before the launch: time to see it, time to act"
            % a9["delai_creation_h_depuis_dernier_credit"], ha="center", fontsize=8, color=INK)
    ax.annotate("token created", xy=(0, 0.35), xytext=(0.08, 0.72), fontsize=8,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
    ax.text(0.12, 0.12, "then the funded wallets buy,\none after another, in public", fontsize=7.5,
            va="bottom", ha="left", color=NEUTRE)
    ax.set_xlabel("hours relative to the token creation (2024 reference case, docs/out/a9_g2y_prelaunch.json)")
    ax.set_title("2024: the signal arrives hours before the launch, and the accumulation it announces is itself public",
                 fontsize=9.5, loc="left")

    # ------------------------------------------------------------- row 2: 2026, creation -> alert + 30 s
    ax = fig.add_subplot(gs[1])
    t_tr_g, t_tr_b = d["first_transfer_from_create"]["good_median"], d["first_transfer_from_create"]["bad_median"]
    t_al_g, t_al_b = d["age_alert"]["good_median"], d["age_alert"]["bad_median"]
    t_alert = (t_al_g + t_al_b) / 2          # ticks after the alert sit at the GOOD / BAD midpoint
    t_entry = t_alert + x2["entry_dt_after_alert_s_median"]
    t_sell_g, t_sell_b = d["first_team_sell_from_create"]["good_median"], d["first_team_sell_from_create"]["bad_median"]
    t_end = t_alert + 30.0
    n_tr = (d["first_transfer_from_create"]["good_n"], d["first_transfer_from_create"]["bad_n"])
    n_sell = (d["first_team_sell_from_alert"]["good_n"], d["first_team_sell_from_alert"]["bad_n"])
    n_c40 = (d["team_sold_share_c40"]["good_n"], d["team_sold_share_c40"]["bad_n"])
    ax.set_xlim(-1.5, 49)
    ax.set_ylim(0, 1.32)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.axvspan(t_alert, t_end, color=SHADE, zorder=0)
    ax.text((t_alert + t_end) / 2, 1.22, "what an entrant can observe: alert to alert + 30 s", ha="center",
            fontsize=8, color=INK)
    ax.axhline(0.30, color=NEUTRE, lw=1.2, zorder=1)
    events = [
        (0.0, "creation slot\nsnipers hold %s / %s of the supply\n(%.0f SOL on the 42 verified launches)"
         % (pct(d["inventory_supply"]["good_median"]), pct(d["inventory_supply"]["bad_median"]),
            v05["sol_bloc_med"]), 0.52, ACCENT),
        ((t_tr_g + t_tr_b) / 2,
         "first transfer sniper -> exit wallet\n%.0f s / %.0f s (%d / %d launches)\n"
         "(%.1f s per wallet, %d wallets,\n42 launches of June-July)"
         % (t_tr_g, t_tr_b, n_tr[0], n_tr[1], v07["delai_transfert_s_med"], v07["n_delais"]), 0.74, NEUTRE),
        ((t_al_g + t_al_b) / 2, "detector alert\n%.1f s / %.1f s" % (t_al_g, t_al_b), 0.52, INK),
        (t_entry, "entry read\n(alert + %.1f s, median\nof the 612 eligible)"
         % x2["entry_dt_after_alert_s_median"], 0.74, INK),
        ((t_sell_g + t_sell_b) / 2, "first sale by the team\n%.0f s / %.0f s (%d / %d launches)"
         % (t_sell_g, t_sell_b, n_sell[0], n_sell[1]), 0.52, NEUTRE),
        (30.0, "team has sold\n%s / %s" % (pct(d["team_sold_share_c30"]["good_median"]),
                                           pct(d["team_sold_share_c30"]["bad_median"])), 0.74, NEUTRE),
        (40.0, "team has sold %s / %s (creation + 40 s; %d / %d launches)\n"
         "external buyers have paid %s / %s\nof the inventory value (alert + 27 s)"
         % (pct(d["team_sold_share_c40"]["good_median"]), pct(d["team_sold_share_c40"]["bad_median"]),
            n_c40[0], n_c40[1],
            pct(tl["27"]["M7_demand_over_inventory"]["good_median"]),
            pct(tl["27"]["M7_demand_over_inventory"]["bad_median"])), 0.52, NEUTRE),
    ]
    for x, label, y, col in events:
        ax.plot([x], [0.30], marker="|", ms=16, mew=2.0, color=col, zorder=4)
        ax.annotate(label, xy=(x, 0.30), xytext=(x, y), fontsize=7.2, ha="center", va="bottom",
                    arrowprops=dict(arrowstyle="-", color=col, lw=0.6))
    ax.text(-1.2, 0.04, "medians, GOOD / BAD (GOOD = confirmed x2 within 1 h of the entry); %d launches of 33 teams, "
            "2026-08-21 -> 09-14;\nticks after the alert sit at the GOOD / BAD alert midpoint plus the stated delay"
            % (n_good + n_bad), fontsize=7.2, color=INK)
    ax.set_xlabel("seconds after the token creation (alpha_patterns/tables/team_absorption.json; data/v05, data/v07)")
    ax.set_title("2026: the structural signal is on chain within about 12 s, and GOOD and BAD launches look the same",
                 fontsize=9.5, loc="left")

    # ------------------------------------------------------------- row 3: after the entry
    ax = fig.add_subplot(gs[2])
    ts = [10, 20, 30, 60, 120, 300]
    good = [price["at_%d" % t]["good_median"] for t in ts]
    bad = [price["at_%d" % t]["bad_median"] for t in ts]
    ax.set_xscale("log")
    ax.set_xlim(8, 4000)
    ax.set_ylim(0.5, 2.35)
    ax.axhline(1.0, color=GRID, lw=1.0)
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.plot(ts, good, color=GOOD, lw=2.2, marker="o", ms=4,
            label="GOOD, median multiple of the entry price (n = %d)" % n_good)
    ax.plot(ts, bad, color=BAD, lw=2.2, marker="o", ms=4,
            label="BAD, median multiple of the entry price (n = %d)" % n_bad)
    for t, g, b in zip(ts, good, bad):
        if t in (30, 120, 300):
            ax.text(t, g + 0.05, "x%.2f" % g, color=GOOD, fontsize=7.5, ha="center")
            ax.text(t, b - 0.09, "x%.2f" % b, color=BAD, fontsize=7.5, ha="center")
    t_obs = 30.0 - x2["entry_dt_after_alert_s_median"]
    ax.axvline(t_obs, color=INK, lw=0.9, ls=":")
    ax.text(t_obs * 1.06, 1.78, "last observed\ntransaction\n(alert + 30 s)", ha="left", va="top", fontsize=7.5)
    ax.axvspan(8, t_obs, color=SHADE, zorder=0)
    h = x2["t_hit_2x_s"]
    yb = 2.0
    ax.plot([h["p10"], h["p90"]], [yb, yb], color=GOOD, lw=1.4)
    for xq in (h["p10"], h["p90"]):
        ax.plot([xq, xq], [yb - 0.04, yb + 0.04], color=GOOD, lw=1.4)
    ax.plot([h["p50"]], [yb], marker="D", ms=7, color=GOOD)
    ax.annotate("x2 confirmed (two reads): median %.0f s after the entry\n"
                "p10 %.0f s, p90 %.0f s; %s of the GOOD within 30 s, %s within 5 min (n = %d)"
                % (h["p50"], h["p10"], h["p90"], pct(x2["share_of_good_confirmed_within_s"]["30"]),
                   pct(x2["share_of_good_confirmed_within_s"]["300"]), h["n"]),
                xy=(h["p50"], yb), xytext=(60, 2.17), fontsize=7.6, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=GOOD, lw=0.6))
    ax.text(45, 0.56, "the information that separates GOOD from BAD arrives here,\nafter the entry, not in the bundle",
            fontsize=8, color=INK, ha="left")
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.50), frameon=False, fontsize=7.6)
    ax.set_xlabel("seconds after the entry, log scale "
                  "(alpha_patterns/tables/team_absorption.json, x2_timing_summary.json)")
    ax.set_ylabel("multiple of the entry price (median)")
    ax.set_title("After the entry: the outcome separates minutes later",
                 fontsize=9.5, loc="left")

    fig.suptitle("F5. Where the information sits: 2024 announced the move hours ahead; "
                 "2026 shows the coordination at once and the outcome too late",
                 fontsize=10.5, x=0.01, ha="left", y=0.995)
    path = os.path.join(FIG, "f5_act_iv_information_timing.png")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
