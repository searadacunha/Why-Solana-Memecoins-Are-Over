#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r1_burst_window.py — geometrie d'une salve de financement, sur une FENETRE
TEMPORELLE donnee, avec le montant comme critere.

Etape 1 : on remonte l'historique de signatures de l'adresse (pages de 1000,
          du plus recent au plus ancien) jusqu'a depasser le debut de la
          fenetre. Une page vide distingue "fin de l'historique" d'une coupure
          de quota : r1lib leve sur erreur, donc aucune troncature muette.
Etape 2 : on repart de la premiere signature POSTERIEURE a la fenetre et on
          descend en transactions parsees jusqu'a sortir de la fenetre par le
          bas ; on garde tous les transferts natifs sortants.
Etape 3 : on mesure -- destinataires distincts, distribution des tickets,
          separation poussiere/financement (memes seuils que r1_dust_vs_funding),
          fenetre la plus courte contenant 90 % des envois FINANCES, debit.

Sortie : data/r1_burst_<addr8>_<ts0>.json  (+ liste des destinataires finances)
Usage  : python3 r1_burst_window.py <adresse> <ts_debut> <ts_fin>
"""
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1lib as R  # noqa: E402

SEUIL_FIN = 0.01  # SOL : au-dela, le destinataire peut effectivement acheter


def fenetre_la_plus_courte(ts, frac=0.90):
    if not ts:
        return None
    ts = sorted(ts)
    k = max(1, int(len(ts) * frac))
    return min(ts[i + k - 1] - ts[i] for i in range(0, len(ts) - k + 1))


def signature_avant(addr, ts_fin):
    """Signature la plus ancienne encore POSTERIEURE a ts_fin, en remontant."""
    sigs, before, pages = [], None, 0
    while pages < 400:
        page = R.sig_page(addr, 1000, before)
        pages += 1
        if not page:
            return None, sigs, pages, True
        sigs += page
        old = page[-1].get("blockTime") or 0
        sys.stderr.write("  sigs page %d n=%d oldest=%s\n" % (pages, len(sigs), old))
        before = page[-1]["signature"]
        if old < ts_fin:
            for s in page:
                if (s.get("blockTime") or 0) > ts_fin:
                    dernier = s
            cand = [s for s in sigs if (s.get("blockTime") or 0) > ts_fin]
            return (cand[-1]["signature"] if cand else None), sigs, pages, False
        if len(page) < 1000:
            return None, sigs, pages, True
    return None, sigs, pages, False


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return
    addr, ts0, ts1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

    key = "sigwalk_%s_%d" % (addr[:8], ts1)
    walk = R.cached(key, lambda: (lambda r: {
        "before_sig": r[0], "n_sigs": len(r[1]), "pages": r[2],
        "fin_historique": r[3],
        "oldest_ts": min((s.get("blockTime") or 0) for s in r[1]) if r[1] else None,
        "newest_ts": max((s.get("blockTime") or 0) for s in r[1]) if r[1] else None,
    })(signature_avant(addr, ts1)))
    sys.stderr.write("marche arriere: %s\n" % json.dumps(walk))

    # descente en transactions parsees a partir de la frontiere
    before = walk["before_sig"]
    outs, ins, n_tx, pages = [], [], 0, 0
    fini = False
    while not fini and pages < 400:
        page = R.enhanced(addr, 100, before)
        pages += 1
        if not page:
            break
        for t in page:
            ts = t.get("timestamp") or 0
            n_tx += 1
            if ts < ts0:
                continue
            if ts > ts1:
                continue
            for nt in t.get("nativeTransfers") or []:
                a = (nt.get("amount") or 0) / 1e9
                if a <= 0:
                    continue
                if nt.get("fromUserAccount") == addr:
                    outs.append((ts, nt.get("toUserAccount"), a, t.get("signature")))
                elif nt.get("toUserAccount") == addr:
                    ins.append((ts, nt.get("fromUserAccount"), a))
        if (page[-1].get("timestamp") or 0) < ts0:
            fini = True
        before = page[-1]["signature"]
        if len(page) < 100:
            break
        sys.stderr.write("  tx page %d n=%d ts=%s outs=%d\n"
                         % (pages, n_tx, page[-1].get("timestamp"), len(outs)))

    par_dest = {}
    for ts, to, sol, sig in outs:
        d = par_dest.setdefault(to, {"n": 0, "sol": 0.0, "first_ts": ts, "sig": sig})
        d["n"] += 1
        d["sol"] += sol
        d["first_ts"] = min(d["first_ts"], ts)
    fin = {k: v for k, v in par_dest.items() if v["sol"] >= SEUIL_FIN}
    dust = {k: v for k, v in par_dest.items() if v["sol"] < R.RENT_MIN_SOL}
    tf = sorted(v["first_ts"] for v in fin.values())
    tickets = sorted(v["sol"] for v in fin.values())
    par_src = {}
    for ts, fr, sol in ins:
        par_src[fr] = round(par_src.get(fr, 0.0) + sol, 6)

    res = {
        "adresse": addr,
        "fenetre_utc": [R.__dict__.get("_", None) or ts0, ts1],
        "marche_arriere": walk,
        "n_tx_parcourues": n_tx,
        "n_pages_tx": pages,
        "n_transferts_sortants_dans_fenetre": len(outs),
        "n_destinataires_distincts": len(par_dest),
        "n_destinataires_FINANCES_ge_%.2f" % SEUIL_FIN: len(fin),
        "n_destinataires_POUSSIERE": len(dust),
        "sol_sortant_total": round(sum(v["sol"] for v in par_dest.values()), 6),
        "sol_vers_finances": round(sum(tickets), 6),
        "ticket_finance_median_SOL": st.median(tickets) if tickets else None,
        "ticket_finance_min_max": [min(tickets), max(tickets)] if tickets else None,
        "premier_envoi_finance_ts": tf[0] if tf else None,
        "dernier_envoi_finance_ts": tf[-1] if tf else None,
        "duree_salve_s": (tf[-1] - tf[0]) if tf else None,
        "fenetre_90pct_s": fenetre_la_plus_courte(tf),
        "debit_wallets_par_min": round(len(fin) / max(1, (tf[-1] - tf[0])) * 60, 1) if len(tf) > 1 else None,
        "sources_entrantes_dans_fenetre": sorted(({"src": k, "sol": v} for k, v in par_src.items()),
                                                 key=lambda d: -d["sol"])[:20],
        "_finances": {k: {"sol": round(v["sol"], 6), "ts": v["first_ts"]}
                      for k, v in fin.items()},
    }
    p = dict(res)
    p.pop("_finances")
    print(json.dumps(p, indent=1, ensure_ascii=False))
    R.save("r1_burst_%s_%d.json" % (addr[:8], ts0), res)


if __name__ == "__main__":
    main()
