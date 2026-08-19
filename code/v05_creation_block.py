#!/usr/bin/env python3
"""v05 - le bloc d'achat du slot de creation, mesure non circulaire.

v03/v04 partaient des wallets de la flotte. Ici on oublie l'identite : sur les
memes 42 slots de creation, on enumere tous les achats reussis du bloc et on
appelle "bloc d'achat" l'ensemble des acheteurs a >= 5 SOL, quels qu'ils soient.
L'identite ne sert plus qu'a choisir les tokens.

Cela corrige aussi les 2 lancements ou un wallet de rechange (present 1 seule
fois dans tout le corpus, meme ticket que le noyau) remplacait un titulaire.

Mesures : n acheteurs du bloc, SOL total, tokens, part de supply, span de slots,
rang du 1er acheteur externe, prix.

Sortie: data/v05_creation_block.json
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import save, med, cv, DATA, CACHE

SEUIL = 5.0
SOLUSD = json.load(open(f"{CACHE}/solusd_window.json"))["median_close"]
V4 = json.load(open(f"{DATA}/v04_slot_order.json"))["lancements"]
V3 = {o["mint"]: o for o in json.load(open(f"{DATA}/v03_onchain.json"))["lancements"]}

def block_rows(slot, mint):
    b = json.load(open(f"{CACHE}/block_{slot}.json"))
    rows = []
    for i, t in enumerate(b["transactions"]):
        msg = t["transaction"]["message"]
        keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
        la = t["meta"].get("loadedAddresses") or {}
        if mint not in (set(keys) | set(la.get("writable") or []) | set(la.get("readonly") or [])):
            continue
        m = t["meta"]
        if m.get("err"):
            continue
        signer = keys[0]
        dsol = (m["postBalances"][0] - m["preBalances"][0]) / 1e9
        prem = {x["accountIndex"]: x for x in m.get("preTokenBalances") or []}
        tok = {}
        for x in m.get("postTokenBalances") or []:
            if x.get("mint") != mint:
                continue
            a0 = float((prem.get(x["accountIndex"]) or {}).get("uiTokenAmount", {}).get("uiAmount") or 0)
            a1 = float(x["uiTokenAmount"].get("uiAmount") or 0)
            tok[x.get("owner")] = tok.get(x.get("owner"), 0.0) + (a1 - a0)
        rows.append({"idx": i, "sig": t["transaction"]["signatures"][0], "signer": signer,
                     "sol": -dsol, "recu": tok.get(signer, 0.0), "tok": tok})
    return rows

out = []
for L in V4:
    mint, slot = L["mint"], L["slot"]
    rows = block_rows(slot, mint)
    icr = L["idx_creation"]; creator = L["creator"]
    achats = [r for r in rows if r["recu"] > 0 and r["sol"] > 0.0005 and r["signer"] != creator]
    bloc = [r for r in achats if r["sol"] >= SEUIL]
    petits = [r for r in achats if r["sol"] < SEUIL]
    if not bloc:
        continue
    lastb = max(r["idx"] for r in bloc)
    firstb = min(r["idx"] for r in bloc)
    avant = [r for r in petits if r["idx"] < lastb]
    apres = [r for r in petits if r["idx"] > lastb]
    sol = sum(r["sol"] for r in bloc); tok = sum(r["recu"] for r in bloc)
    vwap = sol / tok
    tickets = sorted((r["sol"] for r in bloc), reverse=True)
    fe = apres[0] if apres else None
    o = {
      "mint": mint, "slot": slot,
      "n_bloc": len(bloc),
      "wallets_bloc": [r["signer"] for r in sorted(bloc, key=lambda x: x["idx"])],
      "idx_bloc": sorted(r["idx"] for r in bloc),
      "idx_creation": icr, "creator": creator,
      "sol_bloc": round(sol, 4), "tokens_bloc": round(tok, 2),
      "part_supply": round(tok / 1e9, 5),
      "tickets": [round(x, 4) for x in tickets],
      "ticket_cv": round(cv([r["sol"] for r in bloc]), 4),
      "n_petits_acheteurs_avant": len(avant),
      "sol_petits_avant": round(sum(r["sol"] for r in avant), 4),
      "petits_avant": [{"idx": r["idx"], "signer": r["signer"], "sol": round(r["sol"], 4)} for r in avant],
      "vwap_sol_par_token": vwap,
      "mc_bloc_usd": round(vwap * 1e9 * SOLUSD, 1),
      "mc_dernier_ticket_usd": round(
          (max(bloc, key=lambda r: r["idx"])["sol"] /
           max(bloc, key=lambda r: r["idx"])["recu"]) * 1e9 * SOLUSD, 1),
      "premier_externe": ({"idx": fe["idx"], "signer": fe["signer"], "sol": round(fe["sol"], 4),
                           "sig": fe["sig"],
                           "mc_usd": round((fe["sol"] / fe["recu"]) * 1e9 * SOLUSD, 1),
                           "ratio": round((fe["sol"] / fe["recu"]) / vwap, 3)} if fe else None),
      "mc_amm_ouverture_usd": L["mc_amm_ouverture_usd"],
      "ratio_amm": L["ratio_amm_sur_operateur"],
    }
    out.append(o)

R = [o["premier_externe"]["ratio"] for o in out if o["premier_externe"]]
sols = [o["sol_bloc"] for o in out]; parts = [o["part_supply"] for o in out]
n4 = [o for o in out if o["n_bloc"] == 4]
agg = {
 "seuil_bloc_SOL": SEUIL, "n_lancements": len(out),
 "n_bloc_egal_4": len(n4),
 "distribution_n_bloc": {str(k): sum(1 for o in out if o["n_bloc"] == k)
                         for k in sorted({o["n_bloc"] for o in out})},
 "sol_bloc_med": round(med(sols), 3),
 "sol_bloc_q1q3": [round(st.quantiles(sols, n=4)[0], 2), round(st.quantiles(sols, n=4)[2], 2)],
 "sol_bloc_min_max": [round(min(sols), 2), round(max(sols), 2)],
 "part_supply_med": round(med(parts), 5),
 "part_supply_q1q3": [round(st.quantiles(parts, n=4)[0], 5), round(st.quantiles(parts, n=4)[2], 5)],
 "part_supply_min_max": [round(min(parts), 5), round(max(parts), 5)],
 "ticket_cv_intra_med": round(med([o["ticket_cv"] for o in out]), 4),
 "n_zero_petit_acheteur_avant": sum(1 for o in out if o["n_petits_acheteurs_avant"] == 0),
 "sol_petits_avant_med": round(med([o["sol_petits_avant"] for o in out]), 4),
 "sol_petits_avant_max": round(max(o["sol_petits_avant"] for o in out), 4),
 "mc_bloc_usd_med": round(med([o["mc_bloc_usd"] for o in out])),
 "mc_dernier_ticket_usd_med": round(med([o["mc_dernier_ticket_usd"] for o in out])),
 "mc_amm_ouverture_usd_med": round(med([o["mc_amm_ouverture_usd"] for o in out if o["mc_amm_ouverture_usd"]])),
 "ratio_premier_externe_med": round(med(R), 3), "n_ratio": len(R),
 "ratio_premier_externe_min_max": [min(R), max(R)],
 "n_ratio_ge_3": sum(1 for x in R if x >= 3),
 "ratio_amm_med": round(med([o["ratio_amm"] for o in out if o["ratio_amm"]]), 3),
 "sol_usd_reference": SOLUSD,
}
save("v05_creation_block.json", {"agregats": agg, "lancements": out})
print(json.dumps(agg, indent=1))
