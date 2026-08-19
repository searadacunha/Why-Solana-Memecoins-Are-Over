#!/usr/bin/env python3
"""v08 - age et naissance des wallets.

Deux populations, meme mesure : la signature la plus ancienne de l'adresse
(getSignaturesForAddress pagine en arriere jusqu'a epuisement), c'est-a-dire la
date de premiere activite on-chain = naissance du wallet.

  A. les wallets du bloc de creation (les 4 snipeurs de chaque quad)
  B. les createurs des memes tokens (deployeurs du mint)

On mesure : date de naissance, ecart de naissance intra-flotte (naissance en
lot ?), age au moment du 1er lancement observe (vieillissement).

Limite : la pagination est plafonnee (CAP pages x 1000 signatures). Un wallet
plus actif que le plafond est marque `censure=true` : sa naissance est alors
une borne superieure de date (donc son age une borne inferieure).

Sortie: data/v08_ages.json
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import first_signature, load_floor, save, med, DATA, CACHE

V6 = json.load(open(f"{DATA}/v06_curve_ladder.json"))["lancements"]
V2 = json.load(open(f"{DATA}/v02_fleets.json"))["flottes"]

fleet_of = {}
for f in V2:
    for w in f["wallets"]:
        fleet_of[w] = f["lead"]

# wallets du bloc + createurs
bloc_w, creators = {}, {}
for L in V6:
    for x in L["ladder"]:
        if x["sol"] >= 5.0:
            bloc_w.setdefault(x["signer"], []).append(L["slot"])
    # createur : signataire de la tx de creation -> depuis v04
V4 = {o["mint"]: o for o in json.load(open(f"{DATA}/v04_slot_order.json"))["lancements"]}
for L in V6:
    c = V4[L["mint"]]["creator"]
    if c:
        creators[c] = V4[L["mint"]]["created"] if "created" in V4[L["mint"]] else None

# date de creation de chaque token, pour dater l'age du wallet au lancement
FC = {m: d.get("created") for m, d in load_floor().items()}

def birth(addr):
    p = f"{CACHE}/birth_{addr}.json"
    if os.path.exists(p):
        return json.load(open(p))
    sig, bt, pages, cens = first_signature(addr)
    v = {"addr": addr, "first_sig": sig, "first_ts": bt, "pages": pages, "censure": cens}
    json.dump(v, open(p, "w"))
    return v

# --- A. wallets de bloc -----------------------------------------------------
A = []
for w in sorted(bloc_w):
    b = birth(w)
    prem = min(FC.get(L["mint"]) or 1 << 62 for L in V6
               if any(x["signer"] == w and x["sol"] >= 5.0 for x in L["ladder"]))
    b["fleet"] = fleet_of.get(w)
    b["premier_lancement_ts"] = prem if prem < (1 << 62) else None
    b["age_j_au_1er_lancement"] = (round((prem - b["first_ts"]) / 86400, 1)
                                   if b["first_ts"] and prem < (1 << 62) else None)
    A.append(b)
    print(f"BLOC {w[:12]:14s} fleet={str(b['fleet'])[:10]:12s} ne={b['first_ts']} "
          f"censure={b['censure']} age={b['age_j_au_1er_lancement']}j")

# --- B. createurs -----------------------------------------------------------
B = []
for c in sorted(creators):
    b = birth(c)
    ms = [L["mint"] for L in V6 if V4[L["mint"]]["creator"] == c]
    prem = min(FC.get(m) or 1 << 62 for m in ms)
    b["n_tokens"] = len(ms)
    b["premier_token_ts"] = prem if prem < (1 << 62) else None
    b["age_min_au_1er_token"] = (round((prem - b["first_ts"]) / 60, 1)
                                 if b["first_ts"] and prem < (1 << 62) else None)
    B.append(b)

# --- naissance en lot par flotte -------------------------------------------
lots = {}
for f in V2:
    ts = [x["first_ts"] for x in A if x["fleet"] == f["lead"] and x["first_ts"] and not x["censure"]]
    if len(ts) >= 2:
        lots[f["lead"]] = {"n_wallets_dates": len(ts), "n_wallets": f["n_wallets"],
                           "naissances": sorted(ts),
                           "span_s": max(ts) - min(ts),
                           "span_h": round((max(ts) - min(ts)) / 3600, 2)}

ageA = [x["age_j_au_1er_lancement"] for x in A if x["age_j_au_1er_lancement"] is not None and not x["censure"]]
ageB = [x["age_min_au_1er_token"] for x in B if x["age_min_au_1er_token"] is not None and not x["censure"]]
agg = {
 "n_wallets_bloc": len(A), "n_bloc_censure": sum(1 for x in A if x["censure"]),
 "age_j_bloc_med": round(med(ageA), 1) if ageA else None, "n_age_bloc": len(ageA),
 "age_j_bloc_min_max": [min(ageA), max(ageA)] if ageA else None,
 "n_createurs": len(B), "n_createurs_censure": sum(1 for x in B if x["censure"]),
 "age_min_createur_med": round(med(ageB), 1) if ageB else None, "n_age_createur": len(ageB),
 "age_min_createur_q1q3": [round(st.quantiles(ageB, n=4)[0], 1),
                           round(st.quantiles(ageB, n=4)[2], 1)] if len(ageB) > 3 else None,
 "part_createurs_moins_24h": round(sum(1 for x in ageB if x < 1440) / len(ageB), 3) if ageB else None,
 "part_createurs_moins_2h": round(sum(1 for x in ageB if x < 120) / len(ageB), 3) if ageB else None,
 "naissance_en_lot_par_flotte": lots,
}
save("v08_ages.json", {"agregats": agg, "wallets_bloc": A, "createurs": B})
print(json.dumps(agg, indent=1))
