#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figures de la section RESULTATS (docs/RESULTATS.md).

Regenere les 4 PNG de figures/ a partir de data/ et docs/out/ uniquement.
Aucun appel reseau, aucune cle, aucun chemin absolu : le repertoire du depot
est deduit de l'emplacement de ce fichier.

  python3 code/f_figures_resultats.py

Note de confidentialite : une adresse d'infrastructure du corpus porte un
prefixe injurieux. Elle n'est jamais rendue en clair : les figures et les
tables la designent par l'identifiant neutre W1 (cf. docs/RESULTATS.md, note 2).
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

# Palette sobre, lisible en niveaux de gris.
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
    print("ecrit", os.path.relpath(path, ROOT))


# --------------------------------------------------------------------------
# F1 — L'escalier de capitalisation d'un lancement (n = 42 lancements quad)
# --------------------------------------------------------------------------
def fig1():
    v5 = jload(os.path.join(DATA, "v05_creation_block.json"))["agregats"]
    v6 = jload(os.path.join(DATA, "v06_curve_ladder.json"))["agregats"]

    m2 = jload(os.path.join(OUT, "m2_entry_price.json"))
    sol_usd = v6["sol_usd_reference"]

    # Quatre etapes, TOUTES en capitalisation USD (pas de melange avec un
    # montant d'achat : le dev-buy est un ticket, pas une capitalisation).
    #
    # ATTENTION — l'ouverture AMM est prise dans v06, PAS dans v05. Les deux
    # scripts calculent la meme grandeur et divergent sur 42/42 lancements
    # (medianes 46 147 $ vs 53 985 $, ecarts unitaires jusqu'a x100). v06 est
    # l'implementation corrigee : elle prend la mediane des swaps PUMP_AMM
    # >= 0,1 SOL des 60 premieres secondes, la ou v05 retenait le premier swap
    # venu et se faisait piloter par des echanges poussiere de 0,002 SOL.
    # Cf. docs/RESULTATS.md, §1.6.
    etapes = [
        ("Lancement\n(courbe vierge)", m2["launch_mc_sol"] * sol_usd),
        ("Fin du bloc\nde creation", v5["mc_bloc_usd_med"]),
        ("Dernier ticket\ndu bloc", v5["mc_dernier_ticket_usd_med"]),
        ("Ouverture AMM\n(1er acheteur externe)", v6["mc_amm_ouverture_usd_med"]),
    ]
    labels = [e[0] for e in etapes]
    vals = [e[1] for e in etapes]

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    couleurs = [NEUTRE, NEUTRE, NEUTRE, ACCENT]
    bars = ax.bar(range(len(vals)), vals, color=couleurs, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.06,
                f"{v:,.0f} $".replace(",", " "), ha="center", va="bottom",
                fontsize=8.5, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylim(800, vals[-1] * 9)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Capitalisation mediane (USD, echelle log)")
    ax.set_title("F1 — L'escalier de prix est deja monte quand le marche s'ouvre\n"
                 "n = 42 lancements verifies on-chain (4 flottes)", fontsize=9.5, loc="left")
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)

    r_tot = vals[3] / vals[0]
    ax.annotate("", xy=(3, vals[3] * 1.9), xytext=(0, vals[3] * 1.9),
                arrowprops=dict(arrowstyle="<->", color=NEG, lw=1.3))
    ax.text(1.5, vals[3] * 2.2, f"x{r_tot:.0f} entre le lancement et le premier acheteur externe",
            ha="center", va="bottom", fontsize=8.5, color=NEG, fontweight="bold")
    finish(fig, "f1_escalier_capitalisation.png")


# --------------------------------------------------------------------------
# F2 — Le cout pour l'acheteur : 15 politiques de sortie (T1)
# --------------------------------------------------------------------------
def fig2():
    m5 = jload(os.path.join(OUT, "m5_roundtrip.json"))["matrice"]
    ordre = ["time_1m", "time_3m", "time_5m", "time_10m", "trail_30", "trail_40",
             "tp50", "tp50_sl35", "tp2x", "tp2x_sl35"]
    noms = {"time_1m": "sortie 1 min", "time_3m": "sortie 3 min", "time_5m": "sortie 5 min",
            "time_10m": "sortie 10 min", "trail_30": "trailing -30 %", "trail_40": "trailing -40 %",
            "tp50": "TP +50 %", "tp50_sl35": "TP +50 % / SL -35 %",
            "tp2x": "TP x2", "tp2x_sl35": "TP x2 / SL -35 %"}

    med = [m5[k]["med"] for k in ordre]
    moy = [m5[k]["moy"] for k in ordre]
    y = list(range(len(ordre)))

    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    h = 0.38
    ax.barh([v + h / 2 for v in y], med, height=h, color=NEUTRE, label="mediane %")
    ax.barh([v - h / 2 for v in y], moy, height=h, color=NEG, label="moyenne %")
    ax.axvline(0, color=INK, linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels([noms[k] for k in ordre], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("PnL net par aller-retour (%), couts 5,82 % deja retranches")
    ax.set_title("F2 — Aucune politique de sortie n'a une esperance positive\n"
                 "n = 196 tokens, 20 clusters, entree systematique a t0+120 s",
                 fontsize=9.5, loc="left")
    ax.set_xlim(-32, 14)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    # Annotation attachee a la ligne TP +50 %, seule mediane franchement positive.
    i_tp50 = ordre.index("tp50")
    ax.annotate("mediane +3,3 % mais moyenne -12,9 % :\ngagner souvent un peu,\nperdre rarement beaucoup",
                xy=(med[i_tp50], i_tp50 + h / 2), xytext=(6.5, i_tp50 - 2.4),
                fontsize=7.5, style="italic", color=NEG, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=NEG, lw=1))
    finish(fig, "f2_politiques_sortie.png")


# --------------------------------------------------------------------------
# F3 — La decroissance : multiple median a 1 h / 2 h / 4 h / 24 h (T5)
# --------------------------------------------------------------------------
def fig3():
    # Valeurs de docs/tables/T5_horizon_1h_24h.md (regenerable par t5_horizon_1h_24h.py).
    hz = ["+1 h", "+2 h", "+4 h", "+24 h"]
    med = [0.45, 0.42, 0.38, 0.22]
    lo = [0.30, 0.28, 0.26, 0.06]
    hi = [0.60, 0.59, 0.51, 0.35]
    pop = [0.45, 0.41, 0.31, 0.03]
    x = list(range(len(hz)))

    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.errorbar(x, med, yerr=[[m - l for m, l in zip(med, lo)],
                              [h - m for m, h in zip(med, hi)]],
                fmt="o-", color=NEUTRE, capsize=4, linewidth=1.8, markersize=6,
                label="multiple median (tokens encore cotes)")
    ax.plot(x, pop, "s--", color=NEG, linewidth=1.6, markersize=6,
            label="population entiere (sans bougie = 0,00x)")
    ax.axhline(1.0, color=INK, linewidth=1, linestyle=":")
    ax.text(-0.08, 1.01, "seuil de non-perte (1,00x)", fontsize=7.5, va="bottom", ha="left")
    ax.set_xticks(x)
    ax.set_xticklabels(hz)
    ax.set_ylim(0, 1.32)
    ax.set_ylabel("Multiple median du prix d'achat")
    ax.set_title("F3 — Achat a ~t0+20 min : ce qu'il reste apres N heures\n"
                 "n = 128 tokens, 18 clusters ; IC95 bootstrap",
                 fontsize=9.5, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 0.93))
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.text(0.02, 0.06, "A +24 h, 31 tokens sur 128 (24 %) n'ont plus\naucune bougie : plus aucun echange.",
            transform=ax.transAxes, fontsize=7.5, style="italic", color=NEG)
    finish(fig, "f3_horizon_decroissance.png")


# --------------------------------------------------------------------------
# F4 — Le graphe d'operateurs et son piege : effondrement de la composante
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
    for b, v, lab in zip(bars, [brut, net], ["graphe brut", "9 adresses\nd'infra retirees"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5,
                f"{v}/{n}\n{100*v/n:.1f} %", ha="center", va="bottom",
                fontsize=8.5, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["graphe brut", "infra retiree"], fontsize=8.5)
    ax.set_ylim(0, 85)
    ax.set_ylabel("Composante connexe geante (% des 282 tokens)")
    ax.set_title("F4a — Le 'reseau geant' est un artefact", fontsize=9, loc="left")
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)

    # F4b : ubiquite des adresses d'infra (anonymisees W1..W5)
    ax = axes[1]
    top = m4["top_ubiquite"][:5]
    noms = [f"W{i+1}" for i in range(len(top))]
    parts = [100 * t["part"] for t in top]
    b2 = ax.barh(range(len(top)), parts, color=NEUTRE, height=0.55)
    for b, t in zip(b2, top):
        ax.text(b.get_width() + 1, b.get_y() + b.get_height() / 2,
                f"{t['tokens']} tokens", va="center", fontsize=8)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(noms, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 72)
    ax.set_xlabel("Part des 282 tokens snipes par l'adresse (%)")
    ax.set_title("F4b — Ubiquite : un service, pas un operateur", fontsize=9, loc="left")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)

    fig.suptitle("F4 — Nettoyer le graphe avant de l'interpreter (n = 282 tokens, arete = >= 3 snipeurs communs)",
                 fontsize=9.5, x=0.01, ha="left")
    finish(fig, "f4_graphe_infra.png")


def main():
    fig1()
    fig2()
    fig3()
    fig4()


if __name__ == "__main__":
    main()
