#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tableau 5 : au-dela des 20 minutes, +1 h, +2 h, +4 h, +24 h.

Les captures `floor_capture` s'arretent a 20 minutes, le tableau 4 ne peut donc
pas repondre a << et si j'attendais plus longtemps ? >>. Cette table leve la
limite avec les bougies horaires GeckoTerminal (1000 bougies = 41 jours, ce qui
couvre toute la fenetre d'observation).

Achat : a la fin de la capture (dernier swap enregistre), au prix robuste des
120 dernieres secondes (mediane des swaps >= 0.3 SOL). Vente : au `close` de la
bougie horaire la plus proche de l'echeance, tolerance 90 minutes.

Piege d'unites, la raison d'etre de ce script : les swaps de `floor_capture`
sont libelles en **SOL par token**, GeckoTerminal renvoie des **USD par token**.
Diviser l'un par l'autre sans conversion gonfle tous les multiples d'un facteur
egal au prix du SOL, soit ~73x sur la fenetre. Le fichier
`analysis_supervision/horizon.json` du 29/07 affirme d'ailleurs en commentaire
que << les prix GT et les prix de swap sont dans la meme unite (SOL/token) >> :
c'est faux. Ici :
  - le prix d'entree en SOL est converti en USD via la serie horaire SOL/USDC
    (data/sol_usd_hourly.json) ;
  - la conversion est ensuite verifiee contre les donnees elles-memes : pour
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
from common import (DATA, boot_ci_median_tokens, clusters, load_captures,  # noqa: E402
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
        lo, hi = boot_ci_median_tokens(v)
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
        ["horizon", "n with candle", "no candle", "median multiple",
         "95% CI", "p25 / p75", "% > 1", "high median", "whole-population median"],
        table,
        ["",
         f"n = {n_tot} tokens | {nclu} clusters. Bought at the robust price of the "
         f"last 120 seconds of the capture (~t0+20 min), converted to USD; sold "
         f"at the `close` of the nearest hourly candle (90 min tolerance).",
         "`high median` = median of the expiry candle's high: an optimistic bound "
         "(it assumes selling at the hour's high).",
         "`whole-population median` counts as 0.00x the tokens with no candle at "
         "all at expiry, i.e. no trading left: an asset that can no longer be "
         "sold is priced at zero rather than dropped from the sample.",
         f"Units control (GT price in USD / swap price in SOL) / (SOL in USD) "
         f"= **{ctrl['mediane_rapport']:.3f}** median on n={ctrl['n']} tokens. "
         f"Close to 1: the SOL->USD conversion is correct. Without it, every "
         f"multiple in this table would be multiplied by "
         f"~{smed:.0f}.",
         "", "Prerequisites: `python3 code/fetch_sol_usd.py` then "
         "`python3 code/fetch_gt_ohlcv.py`.",
         "Regenerate: `python3 code/t5_horizon_1h_24h.py`"])
    print(txt)
    dump_json({"n_tokens": n_tot, "n_clusters": nclu,
               "controle_unites": ctrl, "sol_usd_median": smed,
               "horizons": out},
              os.path.join(DATA, "cout_acheteur", "t5_horizon_1h_24h.json"))
    dump_json(rows, os.path.join(DATA, "cout_acheteur", "t5_par_token.json"))


if __name__ == "__main__":
    main()
