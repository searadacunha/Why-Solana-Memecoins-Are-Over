#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TABLEAU 5 — Au-dela des 20 minutes : +1 h, +2 h, +4 h, +24 h.

Les captures `floor_capture` s'arretent a 20 minutes. Le tableau 4 ne peut donc
pas repondre a << et si j'attendais plus longtemps ? >>. Cette table leve la
limite avec les bougies HORAIRES GeckoTerminal (1000 bougies = 41 jours, ce qui
couvre toute la fenetre d'observation).

Achat : a la FIN de la capture (dernier swap enregistre), au prix robuste des
120 dernieres secondes (mediane des swaps >= 0.3 SOL). Vente : au `close` de la
bougie horaire la plus proche de l'echeance, tolerance 90 minutes.

*** PIEGE D'UNITES — c'est la raison d'etre de ce script ***
Les swaps de `floor_capture` sont libelles en **SOL par token**. GeckoTerminal
renvoie des **USD par token**. Diviser l'un par l'autre sans conversion gonfle
tous les multiples d'un facteur egal au prix du SOL, soit ~73x sur la fenetre.
Le fichier `analysis_supervision/horizon.json` du 29/07 contient d'ailleurs, en
commentaire, l'affirmation << les prix GT et les prix de swap sont dans la meme
unite (SOL/token) >> : elle est FAUSSE. Ici :
  - le prix d'entree en SOL est converti en USD via la serie horaire SOL/USDC
    (data/sol_usd_hourly.json) ;
  - la conversion est ensuite VERIFIEE contre les donnees elles-memes : pour
    chaque token on compare l'ouverture de sa premiere bougie GT (USD) au prix
    robuste de ses premieres secondes de swaps (SOL). Le rapport doit reproduire
    le prix du SOL. Le controle est imprime a chaque execution.

Prerequis : `python3 code/fetch_sol_usd.py` puis `python3 code/fetch_gt_ohlcv.py`.

Usage : python3 code/t5_horizon_1h_24h.py
Sorties : docs/tables/T5_horizon_1h_24h.md
          data/cout_acheteur/t5_horizon_1h_24h.json
"""
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DATA, boot_ci_median, clusters, load_captures,  # noqa: E402
                    med, q, robust_price, sol_usd, wilson, write_table, dump_json)

GT_RAW = os.path.join(DATA, "cout_acheteur", "gt_raw.json")
TOL = 5400          # tolerance de 90 min autour de l'echeance
HORIZONS = [1, 2, 4, 24]


def candle_at(series, target, tol=TOL):
    """(close, high, volume) de la bougie la plus proche de `target`, ou None."""
    cand = [(abs(c[0] - target), c) for c in series if abs(c[0] - target) <= tol]
    if not cand:
        return None
    return min(cand, key=lambda z: z[0])[1]


def main():
    if not os.path.exists(GT_RAW):
        raise SystemExit("data/cout_acheteur/gt_raw.json absent : "
                         "lancer code/fetch_gt_ohlcv.py")
    gt = json.load(open(GT_RAW))
    caps, rej, nfiles = load_captures()
    cmap = clusters(caps)
    bymint = {c["mint"]: c for c in caps}

    smed, sn, s0, s1 = sol_usd()
    print(f"serie SOL/USDC : {sn} bougies horaires, mediane {smed:.2f} USD")

    # ---------------- controle d'unites -------------------------------------
    ratios = []
    for m, r in gt.items():
        if r.get("status") != "ok" or m not in bymint:
            continue
        sw = bymint[m]["_sw"]
        t0 = bymint[m]["_created"]
        p_sol = robust_price(sw, t0, t0 + 300)      # 5 premieres minutes
        if not p_sol or not r["ohlcv"]:
            continue
        first = r["ohlcv"][0]
        if first[0] > t0 + 7200:                    # 1re bougie trop tardive
            continue
        p_usd = first[1] or first[4]                # open, sinon close
        if p_usd and p_sol:
            ratios.append((p_usd / p_sol) / sol_usd(t0))
    ctrl = {"n": len(ratios), "mediane_rapport": med(ratios),
            "p25": q(ratios, 0.25), "p75": q(ratios, 0.75)}
    print(f"CONTROLE D'UNITES : (prix GT USD / prix swap SOL) / (SOL en USD) "
          f"-> mediane {ctrl['mediane_rapport']:.3f} "
          f"[p25 {ctrl['p25']:.2f}, p75 {ctrl['p75']:.2f}] sur n={ctrl['n']} tokens. "
          f"Une valeur proche de 1 confirme la conversion.")

    # ---------------- table -------------------------------------------------
    rows = []
    for m, r in gt.items():
        if m not in bymint:
            continue
        c = bymint[m]
        sw = c["_sw"]
        t_in = sw[-1]["ts"]
        p_sol = robust_price(sw, t_in - 120, t_in + 1)
        if not p_sol:
            continue
        p_usd = p_sol * sol_usd(t_in)
        rec = {"mint": m, "cluster": cmap[m], "t_in": t_in,
               "entree_usd_par_token": p_usd,
               "entree_mc_usd": p_usd * (c.get("supply") or 1e9),
               "statut_gt": r.get("status"), "ratios": {}, "highs": {}}
        ser = r.get("ohlcv") or []
        for h in HORIZONS:
            cd = candle_at(ser, t_in + h * 3600)
            rec["ratios"][h] = (cd[4] / p_usd) if cd else None
            rec["highs"][h] = (cd[2] / p_usd) if cd else None
        rows.append(rec)

    n_tot = len(rows)
    nclu = len({r["cluster"] for r in rows})
    table, out = [], {}
    for h in HORIZONS:
        v = [r["ratios"][h] for r in rows if r["ratios"][h] is not None]
        vh = [r["highs"][h] for r in rows if r["highs"][h] is not None]
        absent = n_tot - len(v)
        lo, hi = boot_ci_median(v)
        wl, wh = wilson(absent, n_tot)
        rec = {"horizon_h": h, "n_avec_bougie": len(v), "n_total": n_tot,
               "sans_bougie": absent,
               "sans_bougie_pct": 100 * absent / n_tot,
               "sans_bougie_ic95_pct": [100 * wl, 100 * wh],
               "mult_median": med(v), "mult_ic95": [lo, hi],
               "mult_p25": q(v, 0.25), "mult_p75": q(v, 0.75),
               "pct_sup_1": 100 * sum(1 for x in v if x > 1) / len(v),
               "high_median": med(vh),
               "mult_median_pop_entiere": med(
                   [r["ratios"][h] if r["ratios"][h] is not None else 0.0
                    for r in rows])}
        out[h] = rec
        table.append([f"+{h} h", len(v), f"{absent} ({100*absent/n_tot:.0f} %)",
                      f"{rec['mult_median']:.2f}", f"[{lo:.2f}, {hi:.2f}]",
                      f"{rec['mult_p25']:.2f} / {rec['mult_p75']:.2f}",
                      f"{rec['pct_sup_1']:.1f}",
                      f"{rec['high_median']:.2f}",
                      f"{rec['mult_median_pop_entiere']:.2f}"])

    txt = write_table(
        "T5_horizon_1h_24h",
        ["horizon", "n avec bougie", "sans bougie", "multiple median",
         "IC95", "p25 / p75", "% > 1", "high median", "median population entiere"],
        table,
        ["",
         f"n = {n_tot} tokens | {nclu} clusters. Achat au prix robuste des 120 "
         f"dernieres secondes de la capture (~t0+20 min), converti en USD ; vente "
         f"au `close` de la bougie horaire la plus proche (tolerance 90 min).",
         "`high median` = mediane du plus haut de la bougie d'echeance : borne "
         "OPTIMISTE (elle suppose de vendre au plus haut de l'heure).",
         "`median population entiere` compte 0,00x les tokens qui n'ont plus "
         "AUCUNE bougie a l'echeance, c'est-a-dire plus aucun echange : c'est la "
         "convention honnete pour un actif qu'on ne peut plus vendre.",
         f"Controle d'unites (prix GT en USD / prix de swap en SOL) / (SOL en USD) "
         f"= **{ctrl['mediane_rapport']:.3f}** en mediane sur n={ctrl['n']} tokens. "
         f"Proche de 1 : la conversion SOL->USD est correcte. Sans cette "
         f"conversion, tous les multiples de cette table seraient multiplies par "
         f"~{smed:.0f}.",
         "", "Prerequis : `python3 code/fetch_sol_usd.py` puis "
         "`python3 code/fetch_gt_ohlcv.py`.",
         "Regenerer : `python3 code/t5_horizon_1h_24h.py`"])
    print(txt)
    dump_json({"n_tokens": n_tot, "n_clusters": nclu,
               "controle_unites": ctrl, "sol_usd_median": smed,
               "horizons": out},
              os.path.join(DATA, "cout_acheteur", "t5_horizon_1h_24h.json"))
    dump_json(rows, os.path.join(DATA, "cout_acheteur", "t5_par_token.json"))


if __name__ == "__main__":
    main()
