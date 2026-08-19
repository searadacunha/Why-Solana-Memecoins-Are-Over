#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r1_dust_vs_funding.py : un envoi de SOL ne finance le destinataire que si le
montant lui permet d'acheter. Ce script mesure la distribution des tickets
sortants des adresses que les notes d'enquete de mai 2026 appellent
"dispatchers de masse", et separe :

  poussiere (dusting)  ticket < 0.00089088 SOL, sous le minimum de rente d'un
                       compte systeme. Le destinataire ne peut rien signer :
                       le montant ne couvre meme pas 179 fois les 0.000005 SOL
                       de frais de base. C'est un marquage d'adresse, pas un
                       financement.
  financement          ticket >= 0.01 SOL, de quoi payer frais + priorite et
                       acheter sur la courbe.

"N wallets finances en T secondes" ne veut rien dire tant qu'on n'a pas regarde
le montant. Un spray de poussiere touche par construction des adresses deja
actives (c'est la liste de diffusion du spammeur) ; retrouver ensuite ces
adresses parmi les gros acheteurs d'un token n'etablit aucun lien d'operation.

Sortie : data/r1_dust_vs_funding.json
Usage  : python3 r1_dust_vs_funding.py [adresse ...]
"""
import json
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r1lib as R  # noqa: E402

# adresses citees par les notes d'enquete comme "dispatchers de masse".
# claim = ce que la note affirme ; rien n'est suppose vrai.
CIBLES = {
    "4KHPw3QDsXe6HFJPNA4SiBi6Qe3mrziDFgyYToeEWGu4":
        "note price_movers : dispatcher A, aurait mass-funde 194 wallets en 7 s",
    "4NyVM3epZLVRnUbHp5H7NrSP53nMU2kLMymhHm6TyUwS":
        "note price_movers : dispatcher B, aurait mass-funde 194 wallets en 7 s",
}
FENETRE_NOTE = (1770176583, 1770176590)  # les "7 secondes" citees par la note


def all_enhanced(addr, max_pages=200):
    out, before = [], None
    for _ in range(max_pages):
        page = R.enhanced(addr, 100, before)
        if not page:
            break
        out += page
        before = page[-1]["signature"]
        if len(page) < 100:
            break
    return out


def profil(addr, claim):
    tx = R.cached("enh_full_%s" % addr[:8], lambda: all_enhanced(addr))
    outs, ins = [], []
    for t in tx:
        ts = t.get("timestamp")
        for nt in t.get("nativeTransfers") or []:
            a = (nt.get("amount") or 0) / 1e9
            if a <= 0:
                continue
            if nt.get("fromUserAccount") == addr:
                outs.append((ts, nt.get("toUserAccount"), a))
            elif nt.get("toUserAccount") == addr:
                ins.append((ts, nt.get("fromUserAccount"), a))

    par_dest = {}
    for ts, to, sol in outs:
        d = par_dest.setdefault(to, {"n": 0, "sol": 0.0, "first_ts": ts, "last_ts": ts})
        d["n"] += 1
        d["sol"] += sol
        d["first_ts"] = min(d["first_ts"], ts)
        d["last_ts"] = max(d["last_ts"], ts)

    dust = {k: v for k, v in par_dest.items() if v["sol"] < R.RENT_MIN_SOL}
    fund = {k: v for k, v in par_dest.items() if v["sol"] >= 0.01}
    entre = {k: v for k, v in par_dest.items()
             if R.RENT_MIN_SOL <= v["sol"] < 0.01}
    tickets = sorted(x[2] for x in outs)
    ts_all = [t for t, _, _ in outs]

    # d'ou vient le SOL de cette adresse, et ou repart le solde ?
    par_src = {}
    for ts, fr, sol in ins:
        par_src[fr] = round(par_src.get(fr, 0.0) + sol, 9)
    gros_sorties = sorted(({"dest": k, "sol": round(v["sol"], 9), "ts": v["last_ts"]}
                           for k, v in fund.items()),
                          key=lambda d: -d["sol"])

    dans_fenetre = [k for k, v in par_dest.items()
                    if FENETRE_NOTE[0] <= v["first_ts"] <= FENETRE_NOTE[1]]

    return {
        "adresse": addr,
        "claim_note": claim,
        "n_tx_parsees": len(tx),
        "vie_s": (max(ts_all) - min(ts_all)) if ts_all else None,
        "ts_premier_envoi": min(ts_all) if ts_all else None,
        "ts_dernier_envoi": max(ts_all) if ts_all else None,
        "n_transferts_sortants": len(outs),
        "n_destinataires_distincts": len(par_dest),
        "sol_sortant_total": round(sum(tickets), 9),
        "ticket_median_SOL": st.median(tickets) if tickets else None,
        "ticket_p99_SOL": tickets[int(0.99 * (len(tickets) - 1))] if tickets else None,
        "ticket_max_SOL": max(tickets) if tickets else None,
        "n_destinataires_POUSSIERE_lt_rente": len(dust),
        "n_destinataires_entre_rente_et_0.01": len(entre),
        "n_destinataires_FINANCES_ge_0.01": len(fund),
        "part_destinataires_poussiere": round(len(dust) / len(par_dest), 4) if par_dest else None,
        "sol_vers_poussiere": round(sum(v["sol"] for v in dust.values()), 9),
        "sol_vers_finances": round(sum(v["sol"] for v in fund.values()), 9),
        "destinataires_finances": gros_sorties,
        "sources_entrantes": sorted(({"src": k, "sol": v} for k, v in par_src.items()),
                                    key=lambda d: -d["sol"]),
        "n_destinataires_dans_fenetre_7s_de_la_note": len(dans_fenetre),
        "recu_max_par_un_destinataire_dans_fenetre_SOL":
            max((par_dest[k]["sol"] for k in dans_fenetre), default=None),
        "_destinataires": {k: {"sol": round(v["sol"], 9), "n": v["n"],
                               "first_ts": v["first_ts"]} for k, v in par_dest.items()},
    }


def main():
    addrs = sys.argv[1:] or list(CIBLES)
    profs = []
    for a in addrs:
        p = profil(a, CIBLES.get(a, "adresse fournie en argument"))
        profs.append(p)
        q = dict(p)
        q.pop("_destinataires")
        print(json.dumps(q, indent=1, ensure_ascii=False)[:2600])

    # recoupement des deux listes de diffusion
    croise = None
    if len(profs) == 2:
        a, b = set(profs[0]["_destinataires"]), set(profs[1]["_destinataires"])
        croise = {"n_a": len(a), "n_b": len(b), "n_commun": len(a & b),
                  "jaccard": round(len(a & b) / len(a | b), 4)}
        print("recoupement des listes:", croise)

    out = {
        "_seuils": {"rente_min_compte_systeme_SOL": R.RENT_MIN_SOL,
                    "frais_base_tx_SOL": R.TX_FEE_SOL,
                    "seuil_financement_SOL": 0.01},
        "profils": [{k: v for k, v in p.items() if k != "_destinataires"} for p in profs],
        "recoupement_listes_diffusion": croise,
    }
    R.save("r1_dust_vs_funding.json", out)
    for p in profs:
        R.save("r1_destinataires_%s.json" % p["adresse"][:8], p["_destinataires"])


if __name__ == "__main__":
    main()
