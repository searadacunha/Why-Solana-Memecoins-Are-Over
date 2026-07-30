#!/usr/bin/env python3
"""Quantify how far the phase-1 target cohort is from a random sample, and what that costs.

The phase-1 targets are tokens the author traded and screenshotted. That is a sample selected on
the outcome twice over: once because the token went somewhere worth trading, once because the trade
went well enough to be worth a screenshot. This script puts a number on the distance between that
cohort and the population, so that the reader is not left to guess how large the effect is.

It also states, explicitly, which questions the cohort can and cannot answer. A cohort selected on
the outcome supports a conditional comparison against other tokens with the same outcome. It does
not support any statement of prevalence, however carefully worded.

USAGE
    python3 code/a4_selection_bias.py
Reads only published files under ./data/. No network, no key.
"""
from __future__ import annotations
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

fam = json.load(open(os.path.join(DATA, "ancrage", "symboles.json")))["familles_temoin"]
cib = json.load(open(os.path.join(DATA, "cibles", "cibles.json")))
coh = json.load(open(os.path.join(DATA, "trace_cohorte", "t0_cohorte.json")))

# --- graduation base rate of the era, from the neutral term families -----------------------------
n_pump = sum(f["n_mints_pump"] for f in fam)
n_grad = sum(round(f["n_mints_pump"] * f["part_gradues"]) for f in fam)
p_grad = n_grad / n_pump

# --- second, independent estimate: the slot-matched creation windows -----------------------------
couv = cib["couverture_pagination"]
p_grad_win = couv["gradues_dans_les_fenetres"] / couv["mints_uniques_recoltes"]

cohorte = coh["temoins"]
n_coh = len(cohorte)
n_coh_grad = sum(1 for t in cohorte if t["gradue"])

# Probability that a sample of this size drawn at random from the era is graduated throughout.
p_all = p_grad ** n_coh_grad if n_coh_grad == n_coh else None

# --- resolution confidence of the cohort itself --------------------------------------------------
conf = {}
for t in cohorte:
    conf[t["confiance_resolution"]] = conf.get(t["confiance_resolution"], 0) + 1
n_unresolved = len(coh.get("non_resolus") or {})

res = {
    "objet": "Distance entre la cohorte de cibles de la phase 1 et un echantillon aleatoire de "
             "tokens de la meme epoque, et consequences sur ce qui peut etre affirme.",
    "taux_de_graduation_de_l_epoque": {
        "par_familles_de_termes_neutres": {
            "n_mints_pump": n_pump, "n_gradues": n_grad, "taux": round(p_grad, 5),
            "familles": [f["terme"] for f in fam],
            "note": "cinq familles de termes choisis sans rapport avec le sujet, mesurees avant "
                    "toute analyse de financement",
        },
        "par_fenetres_de_creation_appariees": {
            "n_mints": couv["mints_uniques_recoltes"],
            "n_gradues": couv["gradues_dans_les_fenetres"],
            "taux": round(p_grad_win, 5),
            "note": "tous les tokens pump.fun crees a +/- 200 slots des ancres, lus bloc par bloc",
        },
    },
    "cohorte": {
        "n_tokens": n_coh, "n_gradues": n_coh_grad,
        "taux": round(n_coh_grad / n_coh, 4) if n_coh else None,
        "confiance_de_resolution": conf,
        "n_symboles_non_resolus_laisses_ambigus": n_unresolved,
        "probabilite_si_tirage_aleatoire": p_all,
        "lecture": f"Un tirage aleatoire de {n_coh} tokens de l'epoque serait entierement gradue "
                   f"avec une probabilite de l'ordre de {p_all:.1e}. La cohorte n'est donc pas un "
                   f"echantillon : elle est selectionnee sur l'issue, et le facteur est enorme."
                   if p_all else "",
    },
    "ce_que_la_cohorte_permet": [
        "Une comparaison CONDITIONNELLE : parmi les tokens gradues de la meme fenetre, ceux que "
        "l'auteur a tradés portent-ils la signature de decoupage plus souvent que les autres ? "
        "C'est a cette question, et a elle seule, que repond le groupe temoin gradue.",
        "Un test de presence : la signature est-elle observable la ou l'auteur affirme l'avoir "
        "vue ? Un negatif y est informatif, un positif y est fragile.",
    ],
    "ce_que_la_cohorte_interdit": [
        "Toute prevalence. 'X % des tokens portent la signature' est indemontrable a partir d'un "
        "echantillon choisi sur l'issue, quelle que soit la prudence de la formulation.",
        "Toute comparaison avec les 9 temoins MORTS prise isolement : ceux-ci different des cibles "
        "par l'issue autant que par l'exposition testee. Le p qui en sort est un majorant "
        "optimiste, et il est rapporte comme tel.",
        "Toute inference de rentabilite. Les captures sont les trades gagnants ; les perdants ne "
        "sont pas dans le dossier et ne peuvent pas l'etre.",
    ],
    "correctif_applique": "Un second groupe temoin, GRADUE et de la meme fenetre, a ete constitue "
                          "avant toute mesure de financement (data/trace_gradues/t0_gradues.json). "
                          "C'est la comparaison qui fait foi ; celle contre les tokens morts est "
                          "conservee pour montrer de combien le confondant deplace le resultat.",
}

out = os.path.join(DATA, "adverse", "a4_selection_bias.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)

print("TAUX DE GRADUATION DE L'EPOQUE")
print(f"  familles de termes neutres  : {n_grad}/{n_pump} = {p_grad:.4%}")
print(f"  fenetres de creation        : {couv['gradues_dans_les_fenetres']}/"
      f"{couv['mints_uniques_recoltes']} = {p_grad_win:.4%}")
print(f"\nCOHORTE : {n_coh_grad}/{n_coh} gradues = {n_coh_grad / n_coh:.0%}")
if p_all:
    print(f"  probabilite d'un tel resultat par tirage aleatoire : {p_all:.1e}")
print(f"  confiance de resolution des mints : {conf}")
print(f"  symboles laisses AMBIGU (non resolus) : {n_unresolved}")
print(f"\n-> {out}")
