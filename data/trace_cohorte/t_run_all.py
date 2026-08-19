#!/usr/bin/env python3
"""Lanceur : applique aux 9 temoins la procedure des cibles, sans en changer un seuil.

Les trois etapes sont les scripts des cibles recopies a l'identique (t1_/t2_/t3_ = etape1_/etape2_/
etape3_ de trace_optimus). Aucun parametre n'est touche : N_BUYERS=40, MIN_INFLOW=0.05,
PREBUY_DAYS=21, REL_TOL=1e-4, WINDOW_S=3600, MIN_CLUSTER=3, MAX_PAGES=400.

Deux temoins (Calm, faith) ont deja ete passes par cette meme procedure pendant l'analyse des cibles.
Leurs fichiers e1/e2 sont repris tels quels, les recalculer donnerait le meme resultat et
consommerait le budget de requetes. Le drapeau `deja_mesure_pendant_les_cibles` le dit dans la
synthese.

Usage :
    python3 t_run_all.py                 # tous les temoins
    python3 t_run_all.py --only CREEKS BandD
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
N_BUYERS = 40          # identique aux cibles
MAX_TX = 260           # identique aux cibles


def run(cmd, log):
    print("  $ " + " ".join(os.path.basename(c) if c.endswith(".py") else c for c in cmd),
          flush=True)
    p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    open(log, "a").write(p.stdout + p.stderr)
    tail = [l for l in (p.stdout or "").splitlines() if l.strip()][-6:]
    for l in tail:
        print("    | " + l, flush=True)
    if p.returncode != 0:
        print("    !! code " + str(p.returncode) + " : " + (p.stderr or "")[-400:], flush=True)
    return p.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    temoins = json.load(open(os.path.join(HERE, "t0_cohorte.json")))["temoins"]
    if a.only:
        temoins = [t for t in temoins if t["label"] in a.only]

    for t in temoins:
        lab, t0 = t["label"], time.time()
        log = os.path.join(HERE, f"t_{lab}.log")
        print(f"\n===== {lab} ({t['symbole']}) — {t['mint']}", flush=True)
        e1 = os.path.join(HERE, f"e1_buyers_{lab}.json")
        if not os.path.exists(e1):
            run([sys.executable, "t1_premiers_acheteurs.py", "--mint", t["mint"],
                 "--curve", t["bonding_curve"], "--label", lab,
                 "--n-buyers", str(N_BUYERS), "--max-tx", str(MAX_TX)], log)
        else:
            print("    (e1 deja present)", flush=True)
        if not os.path.exists(e1):
            print("    !! pas de premiers acheteurs : temoin non mesurable", flush=True)
            continue
        run([sys.executable, "t2_financement.py", "--buyers", e1], log)
        run([sys.executable, "t3_decoupage.py", "--funding",
             os.path.join(HERE, f"e2_funding_{lab}.json")], log)
        print(f"  {lab} termine en {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
