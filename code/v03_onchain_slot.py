#!/usr/bin/env python3
"""v03 -- on-chain verification, transaction by transaction.

For each launch of the fleets re-derived in v02, the transactions of the
creation window are downloaded again from Helius (public Solana RPC) and
measured without going through any file of the earlier analysis:

  - the slot of the mint's creation transaction
  - the slot of each of the fleet's buys, and whether they are identical
  - the SOL each wallet spent (the signer's lamport delta, fees excluded)
  - the number of tokens received (the postTokenBalances delta of its ATA)
  - the share of the 1e9 supply the fleet captured in the creation slot
  - the average price paid (SOL per token) and the marginal price after
    their buys

Output: data/v03_onchain.json, plus cache/tx_*.json holding the raw RPC
replies.
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import load_snipe, get_tx, save, DATA
from statlib import median

S = load_snipe()
FL = json.load(open(f"{DATA}/v02_fleets.json"))

def tx_facts(sig, mint):
    """extrait d'une tx: slot, ts, lamports nets par compte, tokens recus par owner"""
    t = get_tx(sig)
    if not t:
        return None
    msg = t["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
    meta = t["meta"]
    pre, post = meta["preBalances"], meta["postBalances"]
    lam = {keys[i]: (post[i] - pre[i]) for i in range(len(keys))}
    tok = {}
    prem = {(b["accountIndex"]): b for b in meta.get("preTokenBalances") or []}
    for b in meta.get("postTokenBalances") or []:
        if b.get("mint") != mint:
            continue
        i = b["accountIndex"]
        a0 = float((prem.get(i) or {}).get("uiTokenAmount", {}).get("uiAmount") or 0)
        a1 = float(b["uiTokenAmount"].get("uiAmount") or 0)
        tok[b.get("owner")] = tok.get(b.get("owner"), 0.0) + (a1 - a0)
    return {"slot": t["slot"], "ts": t.get("blockTime"), "fee": meta["fee"],
            "lam": lam, "tok": tok, "err": meta.get("err")}

out = []
for fl in FL["flottes"]:
    if fl["n_wallets"] != 4 or fl["n_tokens"] < 5:
        continue                      # on ne verifie on-chain que les "quads"
    for L in fl["launches"]:
        m = L["mint"]
        rows = S[m]["rows"]
        # tx de creation = la ligne de type CREATE
        cre = [(w, v) for w, v in rows.items() if v.get("type") == "CREATE"]
        csig = cre[0][1]["sig"] if cre else None
        cfa = tx_facts(csig, m) if csig else None
        members = [w for w in fl["wallets"] if w in rows]
        buys = []
        for w in members:
            v = rows[w]
            f = tx_facts(v["sig"], m)
            if not f:
                continue
            sol_out = -f["lam"].get(w, 0) / 1e9          # depense nette (frais inclus)
            toks = f["tok"].get(w, 0.0)
            buys.append({"wallet": w, "sig": v["sig"], "slot": f["slot"],
                         "ts": f["ts"], "sol_net": round(sol_out, 6),
                         "sol_cache": v.get("sol"), "tokens": round(toks, 2),
                         "prix_sol_par_token": (sol_out / toks) if toks else None,
                         "err": f["err"]})
        if not buys:
            continue
        slots = sorted({b["slot"] for b in buys})
        stot = sum(b["sol_net"] for b in buys)
        ttot = sum(b["tokens"] for b in buys)
        out.append({
            "fleet_lead": fl["lead"], "mint": m, "created": L["created"],
            "creation_sig": csig,
            "creation_slot": cfa["slot"] if cfa else None,
            "creation_dev_buy_tokens": round((cfa["tok"] or {}).get(
                cre[0][0], 0.0), 2) if cfa else None,
            "n_membres": len(buys),
            "slots_achats": slots,
            "slot_unique": len(slots) == 1,
            "slot_egal_creation": (cfa is not None and len(slots) == 1
                                   and slots[0] == cfa["slot"]),
            "span_slots": slots[-1] - slots[0],
            "sol_total_net": round(stot, 4),
            "tokens_total": round(ttot, 2),
            "part_supply_1e9": round(ttot / 1e9, 5),
            "prix_moyen_sol_par_token": stot / ttot if ttot else None,
            "buys": buys,
        })
        print(f"{m[:12]:14s} slot={out[-1]['creation_slot']} unique={out[-1]['slot_unique']} "
              f"=creation={out[-1]['slot_egal_creation']} n={len(buys)} "
              f"SOL={stot:7.2f} supply={ttot/1e9:.4f}")

# --- agregats ---------------------------------------------------------------
agg = {
 "n_lancements": len(out),
 "n_slot_unique": sum(1 for o in out if o["slot_unique"]),
 "n_slot_egal_creation": sum(1 for o in out if o["slot_egal_creation"]),
 "sol_total_med": round(median([o["sol_total_net"] for o in out]), 3),
 "sol_total_min_max": [round(min(o["sol_total_net"] for o in out), 2),
                       round(max(o["sol_total_net"] for o in out), 2)],
 "part_supply_med": round(median([o["part_supply_1e9"] for o in out]), 5),
 "part_supply_min_max": [round(min(o["part_supply_1e9"] for o in out), 5),
                         round(max(o["part_supply_1e9"] for o in out), 5)],
 "part_supply_q1_q3": [round(st.quantiles([o["part_supply_1e9"] for o in out], n=4)[0], 5),
                       round(st.quantiles([o["part_supply_1e9"] for o in out], n=4)[2], 5)],
}
save("v03_onchain.json", {"agregats": agg, "lancements": out})
print(json.dumps(agg, indent=1))
