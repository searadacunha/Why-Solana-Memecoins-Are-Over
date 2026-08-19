#!/usr/bin/env python3
"""Synthesise the origin of the phase-1 distribution hub from the two on-chain walks.

The hub is the address that funded the four wallets of the reference split, five days before the
token they went on to buy existed. Earlier work could not establish where the hub itself got its
funds: the pagination was bounded and stopped in the recent past, the silent failure documented
as P-pagination in docs/PITFALLS.md.

Both walks were therefore redone unbounded, paging until a short page proved the genesis had been
reached, and declaring the outcome either way. This script turns the two raw walks into one
statement, and keeps in the output the two upstream nodes that remain out of reach, rather than
dropping them.

Usage:
    python3 code/a3_hub_origin.py
Reads data/split/hrs6_genesis.json and data/split/hrs6_upstream.json. No network, no key.
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "split")

gen = json.load(open(os.path.join(DATA, "hrs6_genesis.json")))
ups = json.load(open(os.path.join(DATA, "hrs6_upstream.json")))

ev = gen["events"]
first = ev[0] if ev else None
funded = [e for e in ev if e["delta"] > 0.5]
paid = [e for e in ev if e["delta"] < -0.5]

# A fan-out is a credit followed within minutes by a debit of the same size split across several
# recipients. Counting them is what distinguishes a distributor from an ordinary wallet.
fanouts = []
for i, e in enumerate(ev):
    if e["delta"] <= 0.5:
        continue
    for f in ev[i + 1:i + 4]:
        if abs(f["delta"] + e["delta"]) < 0.01 and len(f["contreparties"]) >= 2:
            fanouts.append({"recu_sol": e["delta"], "t_credit": e["t"], "t_debit": f["t"],
                            "n_destinataires": len(f["contreparties"]),
                            "montants_verses": sorted(c[1] for c in f["contreparties"])})
            break

atteints = {a: v for a, v in ups.items() if v["genese_atteinte"]}
hors_portee = {a: v for a, v in ups.items() if not v["genese_atteinte"]}

res = {
    "objet": "Origine du hub de distribution de la phase 1, etablie par pagination non bornee.",
    "hub": {
        "adresse": gen["addr"],
        "n_signatures": gen["n_sigs"],
        "genese_atteinte": gen["genesis_reached"],
        "premiere_operation": first["t"] if first else None,
        "premiere_operation_montant_sol": first["delta"] if first else None,
        "premiere_operation_source": first["contreparties"][0][0] if first
                                     and first["contreparties"] else None,
        "n_credits_notables": len(funded),
        "n_debits_notables": len(paid),
        "n_eventails_observes": len(fanouts),
        "eventails": fanouts[:10],
    },
    "amont_genese_atteinte": {a: {
        "role": v["role"], "n_signatures": v["n_signatures"],
        "premiere_activite_utc": v["premiere_activite_utc"],
        "premier_flux": v["premiers_flux"][0] if v["premiers_flux"] else None,
    } for a, v in atteints.items()},
    "amont_hors_de_portee": {a: {
        "role": v["role"], "n_signatures_lues": v["n_signatures"],
        "plus_ancienne_vue_utc": v["premiere_activite_utc"],
        "statut": "genese NON atteinte : au-dela du plafond de pagination. Aucune conclusion "
                  "d'origine n'est tiree pour cette adresse.",
    } for a, v in hors_portee.items()},
    "ce_qui_est_etabli": [
        "Le compte du hub est neuf a l'ouverture de la fenetre etudiee : sa toute premiere "
        "operation est une activation de quelques centieme de SOL, et son activite reelle "
        "commence deux semaines plus tard.",
        "Sa forme d'usage est un EVENTAIL : il recoit un montant, puis reverse ce meme montant "
        "dans la minute, decoupe en parts rondes entre plusieurs destinataires. Il ne conserve "
        "pas de solde.",
        "Son bailleur principal n'est pas neuf : son propre compte remonte a 2022 et sa genese "
        "est atteinte, ce qui exclut que l'infrastructure ait ete montee pour la seule fenetre "
        "etudiee.",
    ],
    "ce_qui_reste_ouvert": [
        f"{len(hors_portee)} adresses amont depassent le plafond de pagination et sont declarees "
        f"hors de portee plutot que rapportees comme sans financement.",
        "Aboutir a un service de routage ne dit rien de ce service : tout capital entrant sur "
        "cette chaine passe par un pont ou un echange. Aucun lien d'implication n'est etabli, "
        "ni suggere.",
        "Un compte qui reverse ce qu'il recoit est compatible avec un distributeur d'operation "
        "comme avec un relais de service tiers. La forme est etablie, l'intention ne l'est pas.",
    ],
}

out = os.path.join(DATA, "hrs6_synthese.json")
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)

h = res["hub"]
print(f"HUB {h['adresse']}")
print(f"  {h['n_signatures']} signatures, genese atteinte : {h['genese_atteinte']}")
print(f"  premiere operation {h['premiere_operation']} : {h['premiere_operation_montant_sol']} SOL")
print(f"  {h['n_eventails_observes']} eventails (recoit puis reverse le meme montant decoupe)")
for f in h["eventails"][:5]:
    print(f"    {f['t_credit']} recu {f['recu_sol']:.4f} SOL -> reverse a "
          f"{f['n_destinataires']} adresses : {f['montants_verses']}")
print(f"\n  amont a genese atteinte  : {len(atteints)}")
for a, v in res["amont_genese_atteinte"].items():
    print(f"    {a[:16]}… {v['n_signatures']:>7} sigs, actif depuis {v['premiere_activite_utc']}")
print(f"  amont HORS DE PORTEE     : {len(hors_portee)}")
for a, v in res["amont_hors_de_portee"].items():
    print(f"    {a[:16]}… {v['n_signatures_lues']:>7} sigs lues sans atteindre la genese")
print(f"\n-> {out}")
