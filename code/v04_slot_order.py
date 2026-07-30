#!/usr/bin/env python3
"""v04 - ORDRE D'EXECUTION DANS LE SLOT DE CREATION + ECHELLE DE PRIX.

On telecharge le BLOC ENTIER du slot de creation (getBlock) et on enumere
*toutes* les transactions qui touchent le mint, dans l'ordre du bloc. C'est une
enumeration exhaustive : rien ne peut se cacher entre deux index.

On mesure alors, par lancement :
  - index de la tx de creation, index des achats de la flotte, contiguite
  - nombre d'acheteurs NON-operateur executes AVANT le dernier achat de la flotte
  - VWAP de la flotte (SOL/token)  -> MC d'entree (prix x 1e9)
  - prix du PREMIER acheteur non-operateur non-createur -> MC d'ouverture publique
  - ratio MC_ouverture / MC_flotte
  - prix d'ouverture du pool AMM (1er swap PUMP_AMM de floor_capture)

Sortie: data/v04_slot_order.json
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import rpc, load_snipe, load_floor, save, med, DATA, CACHE

SOLUSD = json.load(open(f"{CACHE}/solusd_window.json"))["median_close"]
S = load_snipe()
F = load_floor()
ON = json.load(open(f"{DATA}/v03_onchain.json"))

def get_block(slot):
    p = f"{CACHE}/block_{slot}.json"
    if os.path.exists(p):
        return json.load(open(p))
    b = rpc("getBlock", [slot, {"encoding": "jsonParsed",
                                "maxSupportedTransactionVersion": 0,
                                "transactionDetails": "full", "rewards": False}],
            timeout=180)
    # on ne garde que les tx touchant un mint pump (allege le cache)
    json.dump(b, open(p, "w"))
    return b

def scan(slot, mint):
    b = get_block(slot)
    rows = []
    for i, t in enumerate(b["transactions"]):
        msg = t["transaction"]["message"]
        keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
        la = t["meta"].get("loadedAddresses") or {}
        allk = set(keys) | set(la.get("writable") or []) | set(la.get("readonly") or [])
        if mint not in allk:
            continue
        m = t["meta"]
        signer = keys[0]
        dsol = (m["postBalances"][0] - m["preBalances"][0]) / 1e9
        prem = {x["accountIndex"]: x for x in m.get("preTokenBalances") or []}
        tok = {}
        for x in m.get("postTokenBalances") or []:
            if x.get("mint") != mint:
                continue
            a0 = float((prem.get(x["accountIndex"]) or {}).get("uiTokenAmount", {}).get("uiAmount") or 0)
            a1 = float(x["uiTokenAmount"].get("uiAmount") or 0)
            o = x.get("owner")
            tok[o] = tok.get(o, 0.0) + (a1 - a0)
        rows.append({"idx": i, "sig": t["transaction"]["signatures"][0],
                     "signer": signer, "err": m.get("err") is not None,
                     "dsol": dsol, "tok": tok})
    return rows, len(b["transactions"])

out = []
for L in ON["lancements"]:
    mint, slot = L["mint"], L["creation_slot"]
    if not slot:
        continue
    rows, ntx = scan(slot, mint)
    ops = {b["wallet"] for b in L["buys"]}
    creator = None
    idx_create = None
    for r in rows:
        if not r["err"] and any(v > 1e6 for v in r["tok"].values()) and r["idx"] is not None:
            idx_create = r["idx"]
            creator = r["signer"]
            break
    op_idx = sorted(r["idx"] for r in rows if r["signer"] in ops and not r["err"])
    if not op_idx:
        continue
    last_op = max(op_idx)
    # acheteurs (token recu > 0 pour le signataire, SOL depense) avant la fin du bloc operateur
    def is_buy(r):
        return (not r["err"]) and r["tok"].get(r["signer"], 0) > 0 and r["dsol"] < -0.0005
    before = [r for r in rows if r["idx"] < last_op and is_buy(r)
              and r["signer"] not in ops and r["signer"] != creator]
    after = [r for r in rows if r["idx"] > last_op and is_buy(r)
             and r["signer"] not in ops and r["signer"] != creator]
    sol_op = sum(b["sol_net"] for b in L["buys"])
    tok_op = sum(b["tokens"] for b in L["buys"])
    vwap = sol_op / tok_op
    first_ext = None
    if after:
        r = after[0]
        q = r["tok"][r["signer"]]
        first_ext = {"idx": r["idx"], "signer": r["signer"], "sig": r["sig"],
                     "sol": round(-r["dsol"], 4), "tokens": round(q, 2),
                     "prix": (-r["dsol"]) / q, "gap_idx": r["idx"] - last_op}
    # prix d'ouverture AMM : 1er swap PUMP_AMM de floor_capture
    amm = None
    fc = F.get(mint)
    if fc and fc.get("swaps"):
        s0 = [s for s in fc["swaps"] if s.get("src") == "PUMP_AMM" and s.get("price")]
        if s0:
            amm = {"ts": s0[0]["ts"], "prix": s0[0]["price"], "side": s0[0]["side"]}
    o = {
      "mint": mint, "slot": slot, "n_tx_bloc": ntx,
      "n_tx_touchant_mint": len(rows),
      "idx_creation": idx_create, "creator": creator,
      "idx_operateur": op_idx,
      "contigu": (op_idx == list(range(op_idx[0], op_idx[0] + len(op_idx)))),
      "idx_creation_juste_avant": (idx_create is not None and op_idx[0] == idx_create + 1),
      "n_acheteurs_externes_avant_fin_bloc_op": len(before),
      "acheteurs_externes_avant": [{"idx": r["idx"], "signer": r["signer"]} for r in before],
      "sol_operateur": round(sol_op, 4), "tokens_operateur": round(tok_op, 2),
      "vwap_sol_par_token": vwap,
      "mc_operateur_sol": round(vwap * 1e9, 3),
      "mc_operateur_usd": round(vwap * 1e9 * SOLUSD, 1),
      "premier_acheteur_externe": first_ext,
      "mc_premier_externe_sol": round(first_ext["prix"] * 1e9, 3) if first_ext else None,
      "mc_premier_externe_usd": round(first_ext["prix"] * 1e9 * SOLUSD, 1) if first_ext else None,
      "ratio_premier_externe_sur_operateur": round(first_ext["prix"] / vwap, 3) if first_ext else None,
      "amm_ouverture": amm,
      "mc_amm_ouverture_usd": round(amm["prix"] * 1e9 * SOLUSD, 1) if amm else None,
      "ratio_amm_sur_operateur": round(amm["prix"] / vwap, 3) if amm else None,
    }
    out.append(o)
    print(f"{mint[:12]:14s} tx_mint={len(rows):3d} cre={idx_create} op={op_idx} "
          f"contigu={o['contigu']} ext_avant={len(before)} "
          f"MCop=${o['mc_operateur_usd']:>9,.0f} MCext=${o['mc_premier_externe_usd'] or 0:>9,.0f} "
          f"x{o['ratio_premier_externe_sur_operateur']}")

R = [o["ratio_premier_externe_sur_operateur"] for o in out if o["ratio_premier_externe_sur_operateur"]]
RA = [o["ratio_amm_sur_operateur"] for o in out if o["ratio_amm_sur_operateur"]]
agg = {
 "sol_usd_reference": SOLUSD,
 "n": len(out),
 "n_contigu": sum(1 for o in out if o["contigu"]),
 "n_creation_juste_avant": sum(1 for o in out if o["idx_creation_juste_avant"]),
 "n_zero_acheteur_externe_avant": sum(1 for o in out if o["n_acheteurs_externes_avant_fin_bloc_op"] == 0),
 "total_acheteurs_externes_avant": sum(o["n_acheteurs_externes_avant_fin_bloc_op"] for o in out),
 "mc_operateur_usd_med": round(med([o["mc_operateur_usd"] for o in out]), 0),
 "mc_operateur_usd_q1q3": [round(st.quantiles([o["mc_operateur_usd"] for o in out], n=4)[0]),
                           round(st.quantiles([o["mc_operateur_usd"] for o in out], n=4)[2])],
 "mc_premier_externe_usd_med": round(med([o["mc_premier_externe_usd"] for o in out
                                          if o["mc_premier_externe_usd"]]), 0),
 "ratio_premier_externe_med": round(med(R), 3), "ratio_premier_externe_n": len(R),
 "ratio_premier_externe_min_max": [min(R), max(R)],
 "n_ratio_sup_2": sum(1 for x in R if x >= 2.0),
 "n_ratio_sup_3": sum(1 for x in R if x >= 3.0),
 "ratio_amm_ouverture_med": round(med(RA), 3) if RA else None, "ratio_amm_n": len(RA),
 "mc_amm_ouverture_usd_med": round(med([o["mc_amm_ouverture_usd"] for o in out
                                        if o["mc_amm_ouverture_usd"]]), 0) if RA else None,
}
save("v04_slot_order.json", {"agregats": agg, "lancements": out})
print(json.dumps(agg, indent=1))
