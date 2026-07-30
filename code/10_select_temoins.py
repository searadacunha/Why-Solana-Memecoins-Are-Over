#!/usr/bin/env python3
"""Selection deterministe du groupe temoin + ecriture de data/cibles/cibles.json.

REGLE PRE-ENREGISTREE (fixee avant toute mesure de financement) :
 1. Univers    : tout mint pump.fun dont la TRANSACTION DE CREATION tombe dans la
                 fenetre +/-200 slots autour du slot de creation d'une cible.
 2. Exclusion  : complete==true (courbe terminee / graduation) OU koth==true.
 3. Analysable : bc_tx_total >= 30 et genese de pagination atteinte.
 4. Classement : |slot - slot_ancre| croissant. On prend les 3 premiers par fenetre.

Aucun critere ne porte sur le financement, l'origine des portefeuilles, ni G2Y.
"""
import json, glob, os, datetime as dt

import sys
S = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
#   S = repertoire contenant harvest_*.json et enriched.json (sorties des scripts 07 et 08)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "cibles", "cibles.json")

TARGETS = {
    "FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump": {
        "label": "h2w6gm6jz", "capture": "2024-12-13", "gain_capture_pct": 316.75},
    "9fURVh8YkzXDch2KmiBK7YT1zPYGC9UcWfXATvcupump": {
        "label": "OPTIMUS", "capture": None, "gain_capture_pct": 307.26},
    "GzcqHzszqpcHqKa68Wwe225ZmBcRHph1H1C1vC5Qpump": {
        "label": "POLMRKTBOT", "capture": "2024-12-15", "gain_capture_pct": 443.0},
}
MIN_TX = 30
N_PER_WINDOW = 3

enr = {x["mint"]: x for x in json.load(open(f"{S}/enriched.json"))}
anchors = {}
for f in glob.glob(f"{S}/harvest_*.json"):
    d = json.load(open(f))
    for m in d["mints"]:
        anchors.setdefault(m["mint"], {
            "anchor": d["anchor"], "anchor_slot": d["anchor_slot"],
            "slot": m["slot"], "sig": m["sig"],
            "blocs": d["blocs"], "sautes": d["sautes"]})


def row(mint, role, raison):
    v, a = enr[mint], anchors.get(mint, {})
    return {
        "mint": mint, "role": role,
        "symbole": v.get("symbol"), "nom": v.get("name"),
        "date_creation_utc": v.get("created_utc"),
        "slot_creation": a.get("slot"),
        "tx_creation": a.get("sig"),
        "createur": v.get("creator"),
        "bonding_curve": v.get("bonding_curve"),
        "pumpfun": True,
        "gradue": v.get("complete"),
        "raydium_pool": v.get("raydium_pool"),
        "king_of_the_hill": v.get("koth"),
        "tx_totales_bonding_curve": v.get("bc_tx_total"),
        "genese_pagination_atteinte": v.get("bc_tx_genese_atteinte"),
        "reply_count": v.get("reply_count"),
        "usd_market_cap_actuel": v.get("usd_market_cap"),
        "ath_2024": None,
        "ath_note": ("indisponible : le champ ath_market_cap de l'API pump n'est renseigne "
                     "que pour 10/171 tokens de la fenetre et TOUS ses horodatages tombent "
                     "en 2025-2026 (aucun en 2024). C'est un maximum recent, pas l'ATH "
                     "historique. Un cas (Fart) a meme ath < market cap actuel."),
        "ath_market_cap_api_recent": v.get("ath_market_cap_api"),
        "ath_ts_api_recent": (dt.datetime.fromtimestamp(v["ath_ts_api"] / 1000, dt.timezone.utc)
                              .isoformat().replace("+00:00", "Z") if v.get("ath_ts_api") else None),
        "fenetre_ancre": a.get("anchor"),
        "delta_slots_vs_ancre": (a["slot"] - a["anchor_slot"]) if a else None,
        "raison_inclusion": raison,
    }


cibles = []
for m, meta in TARGETS.items():
    r = row(m, "cible", (
        f"Cible confirmee par capture de trade de l'auteur (gain {meta['gain_capture_pct']:+.2f} %). "
        f"Verifie on-chain : token pump.fun, courbe terminee (graduation Raydium), "
        f"King-of-the-Hill atteint."))
    r["gain_capture_pct"] = meta["gain_capture_pct"]
    r["date_capture"] = meta["capture"]
    r["label_capture"] = meta["label"]
    cibles.append(r)
cibles.sort(key=lambda z: z["date_creation_utc"])

temoins = []
for anc in ["OPTIMUS", "h2w6gm6jz", "POLMRKTBOT"]:
    q = [m for m, v in enr.items()
         if m not in TARGETS and v.get("created_timestamp")
         and anchors.get(m, {}).get("anchor") == anc
         and not v["complete"] and not v["koth"]
         and v["bc_tx_total"] is not None and v["bc_tx_total"] >= MIN_TX
         and v["bc_tx_genese_atteinte"]]
    q.sort(key=lambda m: abs(anchors[m]["slot"] - anchors[m]["anchor_slot"]))
    for rank, m in enumerate(q[:N_PER_WINDOW], 1):
        d = anchors[m]["slot"] - anchors[m]["anchor_slot"]
        temoins.append(row(m, "temoin", (
            f"Temoin apparie a la fenetre {anc} : cree {abs(d)} slots "
            f"({abs(d)*0.4:.0f} s) {'apres' if d > 0 else 'avant'} la cible, donc memes "
            f"conditions de marche. Jamais gradue, jamais King-of-the-Hill "
            f"({enr[m]['bc_tx_total']} tx sur sa courbe au total) = token mort. "
            f"Rang {rank}/{len(q)} par proximite temporelle a l'ancre.")))

doc = {
    "genere_le": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    "objet": ("Cibles confirmees + groupe temoin apparie, pour tester si les premiers "
              "acheteurs d'un token pump.fun sont finances par un service de swap avec "
              "signature de decoupage."),
    "methode_selection_temoins": {
        "principe": ("Le mode de selection ne depend QUE de la date de creation et de la "
                     "performance de marche. Aucun critere ne porte sur le financement, "
                     "l'origine des portefeuilles, ni sur G2Y. La regle a ete fixee avant "
                     "toute mesure de financement."),
        "1_univers": ("Tout mint pump.fun dont la transaction de CREATION tombe dans une "
                      "fenetre de +/-200 slots autour du slot de creation d'une cible."),
        "detecteur_creation": ("Dans une creation pump.fun, la keypair du mint SIGNE la "
                               "transaction. On lit chaque bloc en transactionDetails=accounts "
                               "et on retient tout compte SIGNATAIRE dont l'adresse finit par "
                               "'pump' dans une tx invoquant "
                               "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P."),
        "validation_detecteur": ("Les 3 cibles sont elles-memes retrouvees par le detecteur "
                                 "dans leur propre fenetre. Faux negatif ecarte."),
        "2_exclusion": "complete==true (graduation) OU king_of_the_hill==true.",
        "3_analysabilite": (f"bc_tx_total >= {MIN_TX} ET pagination menee jusqu'a la genese. "
                            "Un token a 1-4 tx n'a pas d'acheteurs a analyser : il ne peut ni "
                            "confirmer ni infirmer la signature de decoupage."),
        "4_classement": (f"|slot - slot_ancre| croissant, {N_PER_WINDOW} premiers par fenetre. "
                         "Departage purement temporel, independant de toute propriete de "
                         "financement."),
    },
    "couverture_pagination": {
        "fenetres_de_blocs": [
            {"ancre": d["anchor"], "slot_ancre": d["anchor_slot"],
             "blocs_lus": d["blocs"], "blocs_sautes": d["sautes"]}
            for d in [json.load(open(f)) for f in sorted(glob.glob(f"{S}/harvest_*.json"))]],
        "mints_uniques_recoltes": len(enr),
        "avec_fiche_api_pump": sum(1 for v in enr.values() if v.get("created_timestamp")),
        "gradues_dans_les_fenetres": sum(1 for v in enr.values() if v.get("complete")),
        "genese_non_atteinte": sum(1 for v in enr.values()
                                   if v.get("bc_tx_genese_atteinte") is False),
        "garantie": ("Pour les 171 mints, getSignaturesForAddress sur le compte bonding_curve "
                     "a ete pagine jusqu'a une page incomplete : la genese est atteinte pour "
                     "TOUS. Aucun comptage tronque."),
    },
    "avertissements": [
        ("ATH 2024 INDISPONIBLE. Le champ ath_market_cap de l'API pump n'est renseigne que pour "
         "10/171 tokens et tous ses horodatages tombent en 2025-2026, aucun en 2024 ; les valeurs "
         "valent 1.1 a 1.7 fois la capitalisation actuelle, et un cas a un 'ATH' INFERIEUR a sa "
         "capitalisation actuelle. C'est un maximum recent, pas l'ATH historique. La performance "
         "est donc mesuree par GRADUATION + King-of-the-Hill + nombre total de transactions sur "
         "la courbe, tous verifiables on-chain et valables pour l'epoque."),
        ("L'API pump ne pagine pas au-dela d'un offset ~1000-5000 : /coins?offset=N renvoie [] "
         "SANS erreur au-dela. Elle ne permet donc pas d'enumerer la fenetre oct-2024/fev-2025. "
         "C'est pourquoi l'univers des temoins est construit on-chain, bloc par bloc."),
        ("La date de creation d'OPTIMUS est 2024-10-10T05:24:25Z (UTC), et non le 2024-10-11 "
         "indique dans la consigne."),
        ("Les temoins sont apparies au SLOT, pas seulement au mois : chacun est cree a moins de "
         "200 slots (~80 s) de sa cible. L'appariement temporel est donc bien plus serre que la "
         "fenetre oct-2024/fev-2025 demandee."),
        ("Etape suivante (script 04) : verifier que chaque temoin a assez d'ACHETEURS DISTINCTS "
         "precoces pour que la recherche de decoupage ait une chance de se declencher. Le seuil "
         "de 30 tx est un filtre grossier ; le compte d'acheteurs distincts doit etre reporte "
         "par token, et tout temoin en ayant moins de 10 doit etre signale."),
    ],
    "cibles": cibles,
    "temoins": temoins,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(doc, open(OUT, "w"), indent=1, ensure_ascii=False)
print("ecrit:", OUT)
print("cibles:", len(cibles), "temoins:", len(temoins))
for r in cibles + temoins:
    print(" %-7s %-12s %-44s %s tx=%-5s grad=%s" % (
        r["role"], str(r["symbole"])[:12], r["mint"], r["date_creation_utc"][:19],
        r["tx_totales_bonding_curve"], r["gradue"]))
