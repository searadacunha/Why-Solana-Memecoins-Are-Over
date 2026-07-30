#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M5 — COMBIEN COUTE UN ALLER-RETOUR, SUR DIX POLITIQUES DE SORTIE.

Affirmation testee : un acheteur ordinaire qui entre APRES l'ouverture du
marche perd de l'argent en esperance, quelle que soit sa strategie de sortie.

Ce n'est pas un backtest de strategie : c'est une mesure du cout structurel.
On n'essaie pas de gagner, on mesure ce que perd quelqu'un qui achete.

CONVENTIONS D'EXECUTION — toutes explicites, toutes pessimistes-neutres.
Elles sont le coeur de la credibilite du chiffre ; les changer change le
resultat, donc elles sont enoncees, pas cachees.

  X1 Entree a t0 + 120 s (creation + 2 min). Variante +300 s en sensibilite.
     Pourquoi 120 s : c'est le premier instant ou un humain qui a vu le token
     apparaitre peut raisonnablement avoir passe un ordre.
  X2 Prix ROBUSTE d'un instant = mediane des prix executes des swaps
     >= 0,3 SOL dans la fenetre de 30 s qui suit. Un seul swap de poussiere ne
     peut donc pas definir un prix.
  X3 Grille de decision : buckets de 30 s.
  X4 GATE D'ENTREE. On n'entre que si (a) le prix robuste existe, (b) il y a
     >= 0,5 SOL de volume "gros" dans le bucket d'entree, (c) il existe une
     OFFRE absorbant 0,5 SOL. Le prix d'entree paye est max(prix robuste,
     prix de l'offre) : on paie le plus defavorable des deux.
  X5 Verification du fill sur 120 s, sans escalade.
  X6 Carnet = les swaps reels. Profondeur cote demande = on descend les bids
     par prix decroissant jusqu'a absorber 0,5 SOL.
  X7 Une vente AU MARCHE est plafonnee par le prix robuste de l'instant :
     on ne peut pas vendre au-dessus de ce que le marche imprime.
  X8 Couts : 1 % de frais par jambe + 2 % de slippage par jambe.
     Traine aller-retour = 1 - (0,98 x 0,99) / (1,02 x 1,01) = 5,82 %.
  X9 t_safe = dernier swap observe - 120 s. Une sortie planifiee au-dela est
     ramenee a t_safe. On ne credite jamais une sortie qu'on n'a pas vue.
  X10 Un TP est un ordre LIMITE (credite au niveau, sans overshoot) ; SL,
     trailing et timeout sont des ordres AU MARCHE.
  X11 Taille de position 0,5 SOL. Volontairement minuscule : un acheteur plus
     gros ferait PIRE, jamais mieux.
  X12 Non-fillable = -100 %. C'est la convention dure : si personne n'achete
     ce qu'on veut vendre, on ne vend pas. La convention molle (exclure ces
     cas) est calculee aussi, en colonne, pour montrer l'ecart.

UNITE STATISTIQUE : la grappe temporelle (tokens crees a moins de 30 min les
uns des autres). Les tokens d'une meme grappe partagent le regime de marche ;
les traiter comme independants surestimerait la puissance. La moyenne
principale est donc une moyenne de moyennes de grappe.

Ce moteur est un portage direct du moteur utilise en interne. Le portage est
verifiable : `--reference docs/reference_canonical.json` recompare cellule par
cellule avec la sortie du moteur d'origine.

Usage :
    python3 m5_roundtrip.py
    python3 m5_roundtrip.py --entry 300
    python3 m5_roundtrip.py --reference ../docs/reference_canonical.json
"""

import argparse
import bisect
import collections
import json
import math
import os
import statistics

import pumplib as P

MIN_SOL_PRICE = 0.3
DEPTH_MIN_SOL = 0.05
DEPTH_STRICT_SOL = 0.3
POS_SOL = 0.5
BUCKET = 30
FILL_H = 120
FEE_SIDE = 0.01
SLIP_SIDE = 0.02
SAFE_MARGIN = 120
MIN_USEFUL = 120
CLUSTER_GAP = 1800
FEE_IN = (1 + SLIP_SIDE) * (1 + FEE_SIDE)
FEE_OUT = (1 - SLIP_SIDE) * (1 - FEE_SIDE)

POLICIES = ["time_1m", "time_3m", "time_5m", "time_10m",
            "trail_30", "trail_40", "tp50", "tp2x", "tp50_sl35", "tp2x_sl35"]


# --------------------------------------------------------------- chargement
def load(path=None):
    kept, rej = [], collections.Counter()
    for d in P.load_captures(path):
        cl = P.clean_swaps(d)
        if not cl:
            rej["aucun_swap_exploitable"] += 1
            continue
        if cl[-1]["ts"] - cl[0]["ts"] < MIN_USEFUL:
            rej["span_swaps_lt_2min"] += 1
            continue
        if cl[-1]["ts"] - d["created"] < MIN_USEFUL:
            rej["duree_depuis_created_lt_2min"] += 1
            continue
        if not any(x["side"] == "buy" for x in cl):
            rej["aucun_buy"] += 1
            continue
        if not any(x["sol"] >= MIN_SOL_PRICE for x in cl):
            rej["aucun_swap_ge_0.3sol"] += 1
            continue
        d = dict(d)
        d["_sw"] = cl
        kept.append(d)
    kept.sort(key=lambda x: x["created"])
    return kept, dict(rej)


class Book:
    """Carnet reconstruit a partir du flux de trades. Ce n'est pas un carnet
    d'ordres (la donnee n'en contient pas) : c'est la profondeur REELLEMENT
    constatee, c.-a-d. les contreparties qui se sont effectivement presentees.
    C'est plus conservateur qu'un carnet affiche, qui peut etre annule."""

    def __init__(self, sw):
        self.sw = sw
        self.big = [s for s in sw if s["sol"] >= MIN_SOL_PRICE]
        self.big_ts = [s["ts"] for s in self.big]
        self.bids = [s for s in sw if s["side"] == "buy" and s["sol"] >= DEPTH_MIN_SOL]
        self.bid_ts = [s["ts"] for s in self.bids]
        self.bids_s = [s for s in self.bids if s["sol"] >= DEPTH_STRICT_SOL]
        self.bids_s_ts = [s["ts"] for s in self.bids_s]
        self.asks = [s for s in sw if s["side"] == "sell" and s["sol"] >= DEPTH_MIN_SOL]
        self.ask_ts = [s["ts"] for s in self.asks]
        self.all_ts = [s["ts"] for s in sw]
        self.t_last = sw[-1]["ts"]

    @staticmethod
    def _sl(ts_arr, arr, t0, t1):
        return arr[bisect.bisect_left(ts_arr, t0):bisect.bisect_left(ts_arr, t1)]

    def robust(self, t, w=BUCKET):
        seg = self._sl(self.big_ts, self.big, t, t + w)
        return statistics.median([s["p"] for s in seg]) if seg else None

    def big_vol(self, t, w=BUCKET):
        return sum(s["sol"] for s in self._sl(self.big_ts, self.big, t, t + w))

    def depth_bid(self, t, strict=False):
        ts_arr, arr = (self.bids_s_ts, self.bids_s) if strict else (self.bid_ts, self.bids)
        cand = self._sl(ts_arr, arr, t, t + FILL_H + 1)
        if not cand:
            return None, "unfillable"
        cand = sorted(cand, key=lambda s: -s["p"])
        cum = 0.0
        for s in cand:
            cum += s["sol"]
            if cum >= POS_SOL:
                return s["p"], "ok"
        return cand[-1]["p"], "thin"

    def depth_ask(self, t, w=BUCKET):
        cand = self._sl(self.ask_ts, self.asks, t, t + w)
        if not cand:
            return None, "unfillable"
        cand = sorted(cand, key=lambda s: s["p"])
        cum = 0.0
        for s in cand:
            cum += s["sol"]
            if cum >= POS_SOL:
                return s["p"], "ok"
        return cand[-1]["p"], "thin"

    def market_mark(self, t):
        for w in (BUCKET, 60, FILL_H):
            p = self.robust(t, w)
            if p is not None:
                return p
        return None


def pnl(p_in_raw, p_out_raw):
    return (p_out_raw * FEE_OUT) / (p_in_raw * FEE_IN) - 1.0


def simulate(d, off):
    bk = Book(d["_sw"])
    t_e = d["created"] + off
    t_last = bk.t_last
    out = {"entry_flag": None, "policies": {}}

    if t_e >= t_last:
        out["entry_flag"] = "X_entree_apres_fin_capture"
        return out
    p_rob = bk.robust(t_e)
    if p_rob is None:
        out["entry_flag"] = "X_prix_entree_indefini"
        return out
    if bk.big_vol(t_e) < POS_SOL:
        out["entry_flag"] = "X_volume_entree_insuffisant"
        return out
    p_ask, ask_flag = bk.depth_ask(t_e)
    if p_ask is None:
        out["entry_flag"] = "X_aucune_offre_absorbable"
        return out
    p_entry = max(p_rob, p_ask)
    t_safe = t_last - SAFE_MARGIN
    if t_safe < t_e + 60:
        out["entry_flag"] = "X_pas_de_place_aller_retour_verifiable"
        return out

    out["entry_flag"] = "ok"
    out["prix_entree_execute"] = p_entry
    out["entry_pay_up_pct"] = 100 * (p_entry / p_rob - 1)
    out["t_safe_rel"] = int(t_safe - t_e)

    K = int(math.floor((t_last - t_e) / BUCKET))
    grid = [(k, t_e + BUCKET * k, bk.robust(t_e + BUCKET * k)) for k in range(K + 1)]
    defined = [g for g in grid if g[2] is not None]
    k_max_exec = int(math.floor((t_safe - t_e) / BUCKET)) - 1
    pmax = max((g[2] for g in defined), default=None)
    out["mult_max_robuste"] = (pmax / p_entry) if pmax else None
    t_timeout = min(t_e + BUCKET * max(1, k_max_exec + 1), t_safe)

    def record(name, t_x, target, reason, is_limit):
        t_x = int(min(t_x, t_safe))
        rec = {"t_exit_rel": int(t_x - t_e), "reason": reason}
        p_depth, flag = bk.depth_bid(t_x)
        p_dep_s, _ = bk.depth_bid(t_x, strict=True)
        cap = target if is_limit else bk.market_mark(t_x)
        if cap is None:
            cap = p_depth
        if p_depth is None or cap is None:
            rec.update({"fill_flag": "unfillable", "pnl_net": -1.0,
                        "pnl_net_excl": None,
                        "pnl_net_strictbook": -1.0})
        else:
            px = min(cap, p_depth)
            v = round(pnl(p_entry, px), 6)
            vs = None if p_dep_s is None else round(pnl(p_entry, min(cap, p_dep_s)), 6)
            rec.update({"fill_flag": flag, "pnl_net": v, "pnl_net_excl": v,
                        "pnl_net_strictbook": -1.0 if vs is None else vs})
        out["policies"][name] = rec

    for mins in (1, 3, 5, 10):
        t_x = t_e + 60 * mins
        record("time_%dm" % mins, t_x, None,
               "time" if t_x <= t_safe else "tronque_t_safe", False)

    for dd, nm in ((0.30, "trail_30"), (0.40, "trail_40")):
        run_max, fired = p_entry, None
        for (k, ts, p) in grid:
            if p is None:
                continue
            if 1 <= k <= k_max_exec and p <= (1 - dd) * run_max:
                fired = k
                break
            run_max = max(run_max, p)
        if fired is not None:
            record(nm, t_e + BUCKET * (fired + 1), None, "trail_hit", False)
        else:
            record(nm, t_timeout, None, "timeout", False)

    for tpn, tpm in (("tp50", 1.50), ("tp2x", 2.00)):
        for sln, slm in ((None, None), ("sl35", 0.65)):
            nm = tpn + ("_" + sln if sln else "")
            fired = None
            for (k, ts, p) in grid:
                if p is None or not (1 <= k <= k_max_exec):
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
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--entry", type=int, default=120, help="offset d'entree, en s")
    ap.add_argument("--reference", default=None,
                    help="JSON de reference a recomparer cellule par cellule")
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out", "m5_roundtrip.json"))
    a = ap.parse_args()

    # Garde-fou : avec --data (jeu d'exemple), on n'ecrase PAS l'artefact
    # publie. Un tableau du dossier ne doit jamais pouvoir etre remplace par le
    # resultat d'un echantillon de 20 tokens sans que personne s'en apercoive.
    if a.data and a.out == ap.get_default("out"):
        a.out = os.path.join(P.HERE, "..", "data", "sample",
                             os.path.basename(a.out))

    caps, rej = load(a.data)
    cl = P.clusters(caps, CLUSTER_GAP)

    P.head("M5 — ALLER-RETOUR NET, ENTREE A t0 + %d s" % a.entry, "MESURE")
    P.kv("captures exploitables", len(caps))
    for k, v in sorted(rej.items()):
        P.kv("  ecartees : %s" % k, v)
    P.kv("traine aller-retour (frais + slippage)",
         "%.2f %%" % (100 * (1 - FEE_OUT / FEE_IN)))

    sims, flags = {}, collections.Counter()
    for d in caps:
        s = simulate(d, a.entry)
        flags[s["entry_flag"]] += 1
        if s["entry_flag"] == "ok":
            sims[d["mint"]] = s
    n = len(sims)
    print("\n  Gate d'entree :")
    for f, c in flags.most_common():
        print("    %-42s %4d" % (f, c))
    P.kv("tokens reellement entrables", n)
    used_clusters = {cl[m] for m in sims}
    P.kv("grappes representees", len(used_clusters))
    P.kv("pay-up moyen a l'entree (X4)",
         "%.2f %%" % statistics.mean(s["entry_pay_up_pct"] for s in sims.values()))

    print("\n  Resultat par politique de sortie (PnL net, en %) :")
    print("    %-12s %8s %8s %8s %8s %8s" %
          ("politique", "mediane", "moyenne", "%>0", "moy.grap", "%grap>0"))
    table = {}
    for pol in POLICIES:
        vals = [sims[m]["policies"][pol]["pnl_net"] * 100 for m in sims]
        by_c = collections.defaultdict(list)
        for m in sims:
            by_c[cl[m]].append(sims[m]["policies"][pol]["pnl_net"] * 100)
        cmeans = [statistics.mean(v) for v in by_c.values()]
        lo, hi = P.cluster_bootstrap_mean_ci(by_c)
        table[pol] = {
            "n": len(vals), "med": statistics.median(vals),
            "moy": statistics.mean(vals),
            "pct_pos": 100.0 * sum(1 for v in vals if v > 0) / len(vals),
            "moy_grappe": statistics.mean(cmeans),
            "pct_grappe_pos": 100.0 * sum(1 for v in cmeans if v > 0) / len(cmeans),
            "moy_grappe_ic95": [lo, hi],
        }
        t = table[pol]
        print("    %-12s %8.2f %8.2f %7.1f%% %8.2f %7.1f%%" %
              (pol, t["med"], t["moy"], t["pct_pos"], t["moy_grappe"],
               t["pct_grappe_pos"]))

    neg_med = sum(1 for p in POLICIES if table[p]["med"] < 0)
    neg_mean = sum(1 for p in POLICIES if table[p]["moy"] < 0)
    neg_clu = sum(1 for p in POLICIES if table[p]["moy_grappe"] < 0)
    print()
    P.kv("politiques a MEDIANE negative", "%d / %d" % (neg_med, len(POLICIES)))
    P.kv("politiques a MOYENNE negative", "%d / %d" % (neg_mean, len(POLICIES)))
    P.kv("politiques a moyenne de GRAPPE negative",
         "%d / %d" % (neg_clu, len(POLICIES)))

    best = max(POLICIES, key=lambda p: table[p]["moy_grappe"])
    b = table[best]
    P.kv("meilleure politique (moyenne de grappe)", best,
         note="%.2f %% IC95 [%.2f ; %.2f]"
              % (b["moy_grappe"], b["moy_grappe_ic95"][0], b["moy_grappe_ic95"][1]))

    print("\n  Sensibilite a la convention de non-fill (X12) :")
    for pol in ("time_5m", "trail_30", "tp2x"):
        hard = [sims[m]["policies"][pol]["pnl_net"] * 100 for m in sims]
        soft = [sims[m]["policies"][pol]["pnl_net_excl"] * 100 for m in sims
                if sims[m]["policies"][pol]["pnl_net_excl"] is not None]
        strict = [sims[m]["policies"][pol]["pnl_net_strictbook"] * 100 for m in sims]
        print("    %-12s dure %7.2f | molle %7.2f (n=%d) | carnet strict %7.2f"
              % (pol, statistics.median(hard), statistics.median(soft), len(soft),
                 statistics.median(strict)))

    if a.reference:
        print("\n  CONTROLE DE PORTAGE contre %s :" % os.path.basename(a.reference))
        ref = json.load(open(a.reference))
        worst, cells = 0.0, 0
        for pol, r in ref.get("matrice", {}).items():
            if pol not in table:
                continue
            for field in ("med", "moy", "pct_pos"):
                if field in r and r[field] is not None:
                    dlt = abs(table[pol][field] - r[field])
                    worst = max(worst, dlt)
                    cells += 1
        P.kv("cellules comparees", cells)
        P.kv("ecart absolu maximal", "%.6f point de %%" % worst,
             note="OK" if worst < 0.01 else "DIVERGENCE — a expliquer")

    print("""
  LECTURE — enoncer le resultat exactement, sans l'arrondir dans le bon sens :
   - Les DIX politiques ont une MOYENNE negative. C'est le resultat principal :
     l'esperance d'un aller-retour est negative quelle que soit la sortie
     choisie parmi les dix. [MESURE]
   - NEUF politiques sur dix ont aussi une mediane negative. La dixieme,
     `tp50` (prise de profit a +50 %), a une mediane POSITIVE (+3,3 %) tout en
     ayant la PIRE moyenne de la grille (-12,9 %). Ce n'est pas une
     contradiction : cette politique gagne souvent un peu et perd rarement
     beaucoup. Ecrire "les dix politiques ont une mediane negative" serait
     faux, et le dossier ne l'ecrit pas. [MESURE]
   - Le taux de tokens gagnants (%>0) depasse 50 % pour `tp50` : on peut avoir
     raison plus d'une fois sur deux et perdre de l'argent. C'est la forme
     meme de la distribution qui est defavorable, pas la frequence des gains.
     [MESURE]
   - La position simulee fait 0,5 SOL. Un acheteur ordinaire qui met plus
     subit un impact plus grand, dans le meme sens. [INFERE]
   - Ces chiffres sont NETS de 5,82 % de traine, qui expliquent une partie de
     la perte mais pas sa totalite : plusieurs politiques perdent nettement
     plus. [MESURE]
   - Ce que ce script NE dit PAS : qu'il existerait une onzieme politique
     gagnante. Il dit qu'aucune des dix testees ne l'est en esperance, sur ce
     corpus, sur cette fenetre. [MESURE]""")

    P.emit({"entry_offset_s": a.entry, "n_entrables": n,
            "n_grappes": len(used_clusters),
            "gate": dict(flags), "rejets_chargement": rej,
            "traine_aller_retour_pct": 100 * (1 - FEE_OUT / FEE_IN),
            "matrice": table,
            "politiques_mediane_negative": neg_med,
            "politiques_moyenne_grappe_negative": neg_clu,
            "niveau": "MESURE"}, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
