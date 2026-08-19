#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figures for the RESULTATS section (docs/RESULTATS.md).

Regenerates the 4 PNG files of figures/ from data/ and docs/out/ only.
No network call, no key, no absolute path: the repository root is derived
from this file's own location.

  python3 code/f_figures_resultats.py

Privacy note: one infrastructure address of the corpus carries a slur prefix.
It is never rendered in the clear: figures and tables refer to it by the
neutral identifier W1 (see docs/RESULTATS.md, note 2).
"""

import json
import os
import statistics as st

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs", "out")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

# Sober palette, readable in greyscale.
INK = "#1b1b1b"
GRID = "#d8d8d8"
NEG = "#b5423a"
POS = "#2f6f4e"
NEUTRE = "#4a6d8c"
ACCENT = "#c98a2b"

plt.rcParams.update({
    "figure.dpi": 160,
    "savefig.dpi": 160,
    "font.size": 9,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def jload(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def finish(fig, name):
    fig.tight_layout()
    path = os.path.join(FIG, name)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))


# --------------------------------------------------------------------------
# F1. The capitalisation staircase of a launch (n = 42 quad launches)
# --------------------------------------------------------------------------
def fig1():
    v5 = jload(os.path.join(DATA, "v05_creation_block.json"))["agregats"]
    v6 = jload(os.path.join(DATA, "v06_curve_ladder.json"))["agregats"]

    m2 = jload(os.path.join(OUT, "m2_entry_price.json"))
    sol_usd = v6["sol_usd_reference"]

    # Four steps, all in USD capitalisation (no mixing with a purchase
    # amount: the dev-buy is a ticket, not a capitalisation).
    #
    # Careful: the AMM open comes from v06, not from v05. Both scripts
    # compute the same quantity and disagree on 42/42 launches (medians
    # $46,147 vs $53,985, unit-level gaps up to x100). v06 is the corrected
    # implementation: it takes the median of the PUMP_AMM swaps >= 0.1 SOL of
    # the first 60 seconds, where v05 kept whatever swap came first and was
    # steered by ~0.002 SOL dust trades. See docs/RESULTATS.md, §1.7.
    steps = [
        ("Launch\n(virgin curve)", m2["launch_mc_sol"] * sol_usd),
        ("End of the\ncreation block", v5["mc_bloc_usd_med"]),
        ("Last ticket\nof the block", v5["mc_dernier_ticket_usd_med"]),
        ("AMM open\n(1st outside buyer)", v6["mc_amm_ouverture_usd_med"]),
    ]
    labels = [e[0] for e in steps]
    vals = [e[1] for e in steps]

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    colors = [NEUTRE, NEUTRE, NEUTRE, ACCENT]
    bars = ax.bar(range(len(vals)), vals, color=colors, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.06,
                f"${v:,.0f}", ha="center", va="bottom",
                fontsize=8.5, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylim(800, vals[-1] * 9)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Median capitalisation (USD, log scale)")
    ax.set_title("F1. The price staircase is already climbed when the market opens\n"
                 "n = 42 launches verified on-chain (4 fleets)", fontsize=9.5, loc="left")
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)

    r_tot = vals[3] / vals[0]
    ax.annotate("", xy=(3, vals[3] * 1.9), xytext=(0, vals[3] * 1.9),
                arrowprops=dict(arrowstyle="<->", color=NEG, lw=1.3))
    ax.text(1.5, vals[3] * 2.2, f"x{r_tot:.0f} between launch and the first outside buyer",
            ha="center", va="bottom", fontsize=8.5, color=NEG, fontweight="bold")
    finish(fig, "f1_escalier_capitalisation.png")


# --------------------------------------------------------------------------
# F2. The buyer's cost: 15 exit policies (T1)
# --------------------------------------------------------------------------
def fig2():
    m5 = jload(os.path.join(OUT, "m5_roundtrip.json"))["matrice"]
    order = ["time_1m", "time_3m", "time_5m", "time_10m", "trail_30", "trail_40",
             "tp50", "tp50_sl35", "tp2x", "tp2x_sl35"]
    names = {"time_1m": "1 min exit", "time_3m": "3 min exit", "time_5m": "5 min exit",
             "time_10m": "10 min exit", "trail_30": "trailing -30 %", "trail_40": "trailing -40 %",
             "tp50": "TP +50 %", "tp50_sl35": "TP +50 % / SL -35 %",
             "tp2x": "TP x2", "tp2x_sl35": "TP x2 / SL -35 %"}

    med = [m5[k]["med"] for k in order]
    moy = [m5[k]["moy"] for k in order]
    y = list(range(len(order)))

    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    h = 0.38
    ax.barh([v + h / 2 for v in y], med, height=h, color=NEUTRE, label="median %")
    ax.barh([v - h / 2 for v in y], moy, height=h, color=NEG, label="mean %")
    ax.axvline(0, color=INK, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([names[k] for k in order], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("Net PnL per round-trip (%), 5.82 % costs already deducted")
    ax.set_title("F2. No exit policy has a positive expectation\n"
                 "n = 196 tokens, 20 clusters, systematic entry at t0+120 s",
                 fontsize=9.5, loc="left")
    ax.set_xlim(-32, 14)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    # Annotation attached to the TP +50 % row, the only clearly positive median.
    i_tp50 = order.index("tp50")
    ax.annotate("median +3.3 % but mean -12.9 %:\noften win a little,\nrarely lose a lot",
                xy=(med[i_tp50], i_tp50 + h / 2), xytext=(6.5, i_tp50 - 2.4),
                fontsize=7.5, style="italic", color=NEG, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=NEG, lw=1))
    finish(fig, "f2_politiques_sortie.png")


# --------------------------------------------------------------------------
# F3. The decay: median multiple at 1 h / 2 h / 4 h / 24 h (T5)
# --------------------------------------------------------------------------
def fig3():
    # Read from the committed T5 artefact, never hardcoded here: an earlier
    # version of this figure asserted stale values (n = 128, 0.45x/0.22x).
    t5 = jload(os.path.join(DATA, "cout_acheteur", "t5_horizon_1h_24h.json"))
    hs = ["1", "2", "4", "24"]
    hz = [f"+{h} h" for h in hs]
    rows = [t5["horizons"][h] for h in hs]
    med = [r["mult_median"] for r in rows]
    lo = [r["mult_ic95"][0] for r in rows]
    hi = [r["mult_ic95"][1] for r in rows]
    pop = [r["mult_median_pop_entiere"] for r in rows]
    n_tot, nclu = t5["n_tokens"], t5["n_clusters"]
    last = rows[-1]
    x = list(range(len(hz)))

    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.errorbar(x, med, yerr=[[m - l for m, l in zip(med, lo)],
                              [h - m for m, h in zip(med, hi)]],
                fmt="o-", color=NEUTRE, capsize=4, linewidth=1.8, markersize=6,
                label="median multiple (tokens still trading)")
    ax.plot(x, pop, "s--", color=NEG, linewidth=1.6, markersize=6,
            label="whole population (no candle = 0.00x)")
    ax.axhline(1.0, color=INK, linewidth=1, linestyle=":")
    ax.text(-0.08, 1.01, "break-even line (1.00x)", fontsize=7.5, va="bottom", ha="left")
    ax.set_xticks(x)
    ax.set_xticklabels(hz)
    ax.set_ylim(0, 1.32)
    ax.set_ylabel("Median multiple of the entry price")
    ax.set_title("F3. Buying at ~t0+20 min: what is left after N hours\n"
                 f"n = {n_tot} tokens, {nclu} clusters; bootstrap 95% CI",
                 fontsize=9.5, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 0.93))
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.text(0.02, 0.06,
            f"At +24 h, {last['sans_bougie']} tokens out of {n_tot} "
            f"({last['sans_bougie_pct']:.0f} %) have\nno candle left: no trading at all.",
            transform=ax.transAxes, fontsize=7.5, style="italic", color=NEG)
    finish(fig, "f3_horizon_decroissance.png")


# --------------------------------------------------------------------------
# F4. The operator graph and its trap: collapse of the giant component
# --------------------------------------------------------------------------
def fig4():
    m4 = jload(os.path.join(OUT, "m4_infra.json"))
    n = m4["n_tokens"]
    brut = m4["composante_geante_brute"]
    net = m4["composante_geante_nettoyee"]

    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.6),
                             gridspec_kw={"width_ratios": [1, 1.35]})

    ax = axes[0]
    bars = ax.bar([0, 1], [100 * brut / n, 100 * net / n],
                  color=[NEG, POS], width=0.55)
    for b, v in zip(bars, [brut, net]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5,
                f"{v}/{n}\n{100*v/n:.1f} %", ha="center", va="bottom",
                fontsize=8.5, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["raw graph", "infra removed"], fontsize=8.5)
    ax.set_ylim(0, 85)
    ax.set_ylabel("Giant connected component (% of 282 tokens)")
    ax.set_title("F4a. The 'giant network' is an artefact", fontsize=9, loc="left")
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)

    # F4b: ubiquity of the infra addresses (anonymised W1..W5)
    ax = axes[1]
    top = m4["top_ubiquite"][:5]
    names = [f"W{i+1}" for i in range(len(top))]
    parts = [100 * t["part"] for t in top]
    b2 = ax.barh(range(len(top)), parts, color=NEUTRE, height=0.55)
    for b, t in zip(b2, top):
        ax.text(b.get_width() + 1, b.get_y() + b.get_height() / 2,
                f"{t['tokens']} tokens", va="center", fontsize=8)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(names, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 72)
    ax.set_xlabel("Share of the 282 tokens sniped by the address (%)")
    ax.set_title("F4b. Ubiquity marks a shared service, not an operator", fontsize=9, loc="left")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)

    fig.suptitle("F4. Clean the graph before interpreting it (n = 282 tokens, edge = >= 3 shared snipers)",
                 fontsize=9.5, x=0.01, ha="left")
    finish(fig, "f4_graphe_infra.png")


def main():
    fig1()
    fig2()
    fig3()
    fig4()


if __name__ == "__main__":
    main()
