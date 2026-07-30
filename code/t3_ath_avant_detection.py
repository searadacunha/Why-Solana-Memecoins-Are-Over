#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TABLEAU 3 — Part des tokens dont l'ATH est DEJA PASSE quand ils deviennent
visibles.

Mesure : pour chaque token, on compare l'horodatage de l'ATH pump.fun
(`ath_market_cap` + son ts) a l'horodatage de la DETECTION (premiere fois ou le
token existe pour un observateur exterieur : un token `complete` vu par le
detecteur au plus tard 12 s apres sa creation — c'est une borne BASSE de la
latence de n'importe quel acheteur humain, qui voit le token bien plus tard).

Trois seuils, publies ensemble parce qu'ils repondent a trois questions
differentes :
    ATH <= detect_ts        : le sommet est deja derriere au moment ou le token
                              apparait
    ATH < detect_ts + 60 s  : le sommet est derriere avant qu'on ait pu decider
    ATH < detect_ts + 120 s : idem avec 2 minutes de reaction

Decoupage par bande de capitalisation a la detection : c'est la seule facon de
montrer que le phenomene est CONCENTRE sur les tokens qui apparaissent bas —
c'est-a-dire exactement ceux qui ont l'air d'une bonne affaire.

LIMITE DECLAREE : `o_ath_ts` vient de l'API pump.fun, resolution a la seconde,
et `detect_ts` est l'horloge locale du detecteur. Un ecart d'horloge de quelques
secondes est possible ; c'est pourquoi les trois seuils sont publies et pourquoi
la conclusion ne repose pas sur le seuil le plus serre.

Population : socle B propre (regime MC sain, 5k < mc < 300k, ATH connu).

Usage : python3 code/t3_ath_avant_detection.py
Sorties : docs/tables/T3_ath_avant_detection.md, data/t3_ath_avant_detection.json
"""
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, dump_json, load_socle, wilson, write_table  # noqa: E402

BANDS = [(5000, 20000), (20000, 30000), (30000, 40000), (40000, 50000),
         (50000, 65000), (65000, 85000), (85000, 120000), (120000, 300000)]


def main():
    d = load_socle()
    rows = [r for r in d["B"]
            if r.get("q_mc_regime_ok") and r.get("q_mc_plausible")
            and r.get("o_ath_true") and (r.get("detect_mc") or 0) > 0
            and r.get("o_ath_ts") and r.get("detect_ts")]
    ndays = len({r["day"] for r in rows})
    nclu = len({r["cluster_id"] for r in rows})
    print(f"n={len(rows)} tokens, {nclu} clusters, {ndays} jours")

    def bloc(sub):
        n = len(sub)
        k0 = sum(1 for r in sub if r["o_ath_ts"] <= r["detect_ts"])
        k60 = sum(1 for r in sub if r["o_ath_ts"] < r["detect_ts"] + 60)
        k120 = sum(1 for r in sub if r["o_ath_ts"] < r["detect_ts"] + 120)
        lo, hi = wilson(k60, n)
        delays = [(r["o_ath_ts"] - r["detect_ts"]) / 60.0 for r in sub]
        return {"n": n,
                "ath_avant_detection_pct": round(100 * k0 / n, 1),
                "ath_avant_60s_pct": round(100 * k60 / n, 1),
                "ath_avant_60s_ic95": [round(100 * lo, 1), round(100 * hi, 1)],
                "ath_avant_120s_pct": round(100 * k120 / n, 1),
                "delai_ath_median_min": round(st.median(delays), 1)}

    tab, out = [], {}
    for lo_, hi_ in BANDS:
        sub = [r for r in rows if lo_ <= r["detect_mc"] < hi_]
        if len(sub) < 5:
            continue
        b = bloc(sub)
        out[f"{lo_//1000}k-{hi_//1000}k"] = b
        tab.append([f"{lo_//1000}k-{hi_//1000}k", b["n"],
                    f"{b['ath_avant_detection_pct']:.1f}",
                    f"{b['ath_avant_60s_pct']:.1f}",
                    f"[{b['ath_avant_60s_ic95'][0]:.1f}, {b['ath_avant_60s_ic95'][1]:.1f}]",
                    f"{b['ath_avant_120s_pct']:.1f}",
                    f"{b['delai_ath_median_min']:.1f}"])

    sub20 = [r for r in rows if r["detect_mc"] < 20000]
    b20 = bloc(sub20)
    tot = bloc(rows)
    out["_sous_20k"] = b20
    out["_toutes_bandes"] = tot
    tab.append(["--- < 20k (agrege)", b20["n"], f"{b20['ath_avant_detection_pct']:.1f}",
                f"{b20['ath_avant_60s_pct']:.1f}",
                f"[{b20['ath_avant_60s_ic95'][0]:.1f}, {b20['ath_avant_60s_ic95'][1]:.1f}]",
                f"{b20['ath_avant_120s_pct']:.1f}", f"{b20['delai_ath_median_min']:.1f}"])
    tab.append(["--- toute la population", tot["n"], f"{tot['ath_avant_detection_pct']:.1f}",
                f"{tot['ath_avant_60s_pct']:.1f}",
                f"[{tot['ath_avant_60s_ic95'][0]:.1f}, {tot['ath_avant_60s_ic95'][1]:.1f}]",
                f"{tot['ath_avant_120s_pct']:.1f}", f"{tot['delai_ath_median_min']:.1f}"])

    txt = write_table(
        "T3_ath_avant_detection",
        ["bande MC a la detection", "n", "ATH deja passe %", "ATH < +60 s %",
         "IC95 %", "ATH < +120 s %", "delai median ATH (min)"],
        tab,
        ["",
         f"n = {len(rows)} tokens | {nclu} clusters | {ndays} jours UTC | socle B propre.",
         "`detect_ts` = premiere visibilite exterieure (token `complete` vu <= 12 s "
         "apres creation). C'est une borne BASSE de la latence d'un acheteur humain.",
         "Un delai median NEGATIF signifie que, dans la bande, le token typique a "
         "deja fait son sommet avant d'exister pour l'observateur.",
         "Limite : `o_ath_ts` (API pump.fun) et `detect_ts` (horloge locale) peuvent "
         "differer de quelques secondes ; les trois seuils sont publies pour cela.",
         "", "Regenerer : `python3 code/t3_ath_avant_detection.py`"])
    print(txt)
    dump_json({"n": len(rows), "n_clusters": nclu, "n_jours": ndays, "bandes": out},
              os.path.join(DATA, "t3_ath_avant_detection.json"))


if __name__ == "__main__":
    main()
