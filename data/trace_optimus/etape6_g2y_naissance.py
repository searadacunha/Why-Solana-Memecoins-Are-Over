#!/usr/bin/env python3
"""Etape 6 : a quelle date le service de swap G2Y a-t-il commence a operer ?

Pagine l'historique complet de G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t, ecrit
e6_g2y_naissance.json.

OPTIMUS est cree le 2024-10-10. Si la premiere transaction de G2Y est posterieure a cette date, G2Y
ne peut pas, meme indirectement, avoir finance les premiers acheteurs d'OPTIMUS : la question
« ces portefeuilles viennent-ils de G2Y ? » est alors tranchee par impossibilite chronologique,
sans remonter une seule chaine, et l'hypothese a tester devient : le service operait-il depuis une
autre adresse en 2024 ?

Mesure couteuse, faite une seule fois, valable pour les trois cibles. La pagination va jusqu'a la
genese. Si le plafond est touche, on le dit et on ne conclut pas.
"""
from __future__ import annotations
import json, sys, datetime as dt
import lib_trace as L

ADDR = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"

sigs, genesis, pages = L.all_signatures(ADDR, max_pages=4000, label="G2Y")
if not sigs:
    sys.exit("aucune signature")
oldest = sigs[0].get("blockTime")
newest = sigs[-1].get("blockTime")
res = {"addr": ADDR, "n_signatures": len(sigs), "pages": pages,
       "genesis_reached": genesis,
       "oldest_seen_utc": L.utc(oldest), "newest_seen_utc": L.utc(newest),
       "conclusion": None}
if genesis:
    d = dt.datetime.fromtimestamp(oldest, dt.UTC)
    res["conclusion"] = (
        f"Premiere transaction de G2Y : {res['oldest_seen_utc']} UTC. "
        + ("POSTERIEURE a la creation d'OPTIMUS (2024-10-10) : G2Y ne peut pas avoir finance ses "
           "premiers acheteurs. Le service operait donc depuis une autre adresse a l'epoque, ou "
           "n'existait pas encore."
           if d > dt.datetime(2024, 10, 10, tzinfo=dt.UTC) else
           "ANTERIEURE a la creation d'OPTIMUS : G2Y etait deja en service, l'hypothese reste ouverte."))
else:
    res["conclusion"] = ("Plafond de pagination atteint : la premiere transaction de G2Y n'est PAS "
                         "etablie. Aucune conclusion chronologique possible.")
json.dump(res, open("e6_g2y_naissance.json", "w"), indent=1)
print(json.dumps(res, indent=1))
