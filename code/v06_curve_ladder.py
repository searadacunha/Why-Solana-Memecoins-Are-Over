#!/usr/bin/env python3
"""v06 - l'echelle de prix de la courbe (bonding curve), acheteur par acheteur.

Filtre strict : on ne compte comme "achat de courbe" qu'une transaction ou
le compte de courbe (identifie dans la tx de creation comme le compte recevant
~99 % de la supply) perd des tokens et ou le signataire en gagne. Cela elimine
les swaps AMM, les arbitrages et les tx multi-legs qui polluaient v05.

On sort, par lancement, la sequence ordonnee des achats de courbe avec le prix
paye, ce qui donne l'echelle exacte : combien paie le bloc de creation, puis le
suivant, puis le dernier avant graduation.

Sortie: data/v06_curve_ladder.json
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import save, med, DATA, CACHE

SEUIL = 5.0
SOLUSD = json.load(open(f"{CACHE}/solusd_window.json"))["median_close"]
V4 = json.load(open(f"{DATA}/v04_slot_order.json"))["lancements"]

# --- prix d'ouverture AMM, robuste : mediane des prix des swaps PUMP_AMM
#     de >= 0.1 SOL dans les 60 premieres secondes (les swaps poussiere de
#     0,002 SOL portent un prix aberrant et sont exclus).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import load_floor
_F = load_floor()
AMM = {}
for _m, _d in _F.items():
    sw = [s for s in (_d.get("swaps") or [])
          if s.get("src") == "PUMP_AMM" and (s.get("sol") or 0) >= 0.1
          and (s.get("tokens") or 0) > 1000 and s.get("price")]
    if not sw:
        continue
    t0 = min(s["ts"] for s in sw)
    px = [s["price"] for s in sw if s["ts"] <= t0 + 60]
    AMM[_m] = round(st.median(px) * 1e9 * SOLUSD, 1)

def rows_of(slot, mint):
    b = json.load(open(f"{CACHE}/block_{slot}.json"))
    out = []
    for i, t in enumerate(b["transactions"]):
        msg = t["transaction"]["message"]
        keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
        la = t["meta"].get("loadedAddresses") or {}
        if mint not in (set(keys) | set(la.get("writable") or []) | set(la.get("readonly") or [])):
            continue
        m = t["meta"]
        if m.get("err"):
            continue
        prem = {x["accountIndex"]: x for x in m.get("preTokenBalances") or []}
        tok = {}
        for x in m.get("postTokenBalances") or []:
            if x.get("mint") != mint:
                continue
            a0 = float((prem.get(x["accountIndex"]) or {}).get("uiTokenAmount", {}).get("uiAmount") or 0)
            a1 = float(x["uiTokenAmount"].get("uiAmount") or 0)
            tok[x.get("owner")] = tok.get(x.get("owner"), 0.0) + (a1 - a0)
        out.append({"idx": i, "sig": t["transaction"]["signatures"][0], "signer": keys[0],
                    "sol": -(m["postBalances"][0] - m["preBalances"][0]) / 1e9, "tok": tok})
    return out

res = []
for L in V4:
    mint, slot = L["mint"], L["slot"]
    rs = rows_of(slot, mint)
    if not rs:
        continue
    cre = rs[0]                                   # tx de creation
    curve = max(cre["tok"].items(), key=lambda kv: kv[1])[0]   # compte de courbe
    supply_curve = cre["tok"][curve]
    ladder = []
    for r in rs[1:]:
        d = r["tok"].get(curve, 0.0)
        g = r["tok"].get(r["signer"], 0.0)
        # achat de courbe propre : la courbe perd, le signataire gagne, et il
        # gagne >=85% de ce que la courbe perd (sinon tx multi-leg -> prix faux)
        if d < -1 and g > 1 and g >= 0.85 * (-d) and r["sol"] > 0.0005:
            ladder.append({"idx": r["idx"], "signer": r["signer"], "sig": r["sig"],
                           "sol": round(r["sol"], 4), "tokens": round(g, 2),
                           "mc_usd": round((r["sol"] / g) * 1e9 * SOLUSD, 1)})
    if not ladder:
        continue
    bloc = [x for x in ladder if x["sol"] >= SEUIL]
    if not bloc:
        continue
    last_b = max(x["idx"] for x in bloc)
    apres = [x for x in ladder if x["idx"] > last_b]
    avant = [x for x in ladder if x["idx"] < min(y["idx"] for y in bloc) and x["sol"] < SEUIL]
    sol = sum(x["sol"] for x in bloc); tk = sum(x["tokens"] for x in bloc)
    mc_bloc = (sol / tk) * 1e9 * SOLUSD
    res.append({
      "mint": mint, "slot": slot, "compte_courbe": curve,
      "supply_dans_courbe": round(supply_curve, 2),
      "dev_buy_sol": round(cre["sol"], 4),
      "dev_buy_tokens": round(sum(v for k, v in cre["tok"].items() if k != curve), 2),
      "n_achats_courbe": len(ladder),
      "n_bloc": len(bloc), "sol_bloc": round(sol, 3), "tokens_bloc": round(tk, 2),
      "part_courbe_bloc": round(tk / supply_curve, 4),
      "part_supply_bloc": round(tk / 1e9, 5),
      "mc_bloc_usd": round(mc_bloc, 1),
      "n_avant_bloc": len(avant), "sol_avant_bloc": round(sum(x["sol"] for x in avant), 4),
      "n_apres_bloc": len(apres),
      "sol_apres_bloc": round(sum(x["sol"] for x in apres), 3),
      "premier_apres": (dict(apres[0], ratio=round(apres[0]["mc_usd"] / mc_bloc, 3))
                        if apres else None),
      "mc_amm_ouverture_usd": AMM.get(mint),
      "ratio_amm_sur_bloc": (round(AMM[mint] / mc_bloc, 3) if AMM.get(mint) else None),
      "ladder": ladder,
    })

R1 = [r["premier_apres"]["ratio"] for r in res if r["premier_apres"]]
RA = [r["ratio_amm_sur_bloc"] for r in res if r["ratio_amm_sur_bloc"]]
agg = {
 "n_lancements": len(res), "sol_usd_reference": SOLUSD,
 "n_zero_achat_courbe_avant_bloc": sum(1 for r in res if r["n_avant_bloc"] == 0),
 "sol_courbe_avant_bloc_max": max(r["sol_avant_bloc"] for r in res),
 "part_courbe_captee_med": round(med([r["part_courbe_bloc"] for r in res]), 4),
 "part_courbe_captee_min_max": [min(r["part_courbe_bloc"] for r in res),
                                max(r["part_courbe_bloc"] for r in res)],
 "part_supply_captee_med": round(med([r["part_supply_bloc"] for r in res]), 5),
 "sol_bloc_med": round(med([r["sol_bloc"] for r in res]), 3),
 "part_sol_courbe_captee_med": round(med([r["sol_bloc"] / (r["sol_bloc"] + r["sol_apres_bloc"])
                                          for r in res]), 4),
 "dev_buy_sol_med": round(med([r["dev_buy_sol"] for r in res]), 4),
 "mc_bloc_usd_med": round(med([r["mc_bloc_usd"] for r in res])),
 "mc_premier_apres_usd_med": round(med([r["premier_apres"]["mc_usd"] for r in res
                                        if r["premier_apres"]])),
 "ratio_premier_apres_med": round(med(R1), 3), "n_ratio1": len(R1),
 "ratio_premier_apres_min_max": [min(R1), max(R1)],
 "n_ratio1_ge_3": sum(1 for x in R1 if x >= 3), "n_ratio1_ge_2": sum(1 for x in R1 if x >= 2),
 "mc_amm_ouverture_usd_med": round(med([r["mc_amm_ouverture_usd"] for r in res
                                        if r["mc_amm_ouverture_usd"]])),
 "ratio_amm_med": round(med(RA), 3), "n_ratio_amm": len(RA),
 "ratio_amm_min_max": [min(RA), max(RA)],
 "n_ratio_amm_ge_3": sum(1 for x in RA if x >= 3),
}
save("v06_curve_ladder.json", {"agregats": agg, "lancements": res})
print(json.dumps(agg, indent=1))
