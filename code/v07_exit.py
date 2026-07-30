#!/usr/bin/env python3
"""v07 - LA SORTIE : transfert du sac vers un collecteur, puis liquidation.

Chaine mesuree, 100 % on-chain :
  1. depuis la tx d'achat du bloc, on releve le COMPTE DE TOKEN (ATA) de chaque
     wallet du bloc pour ce mint ;
  2. getSignaturesForAddress(ATA) donne TOUTE la vie de ce compte : l'achat,
     puis ce qui sort ;
  3. on classe chaque tx : SELL (l'ATA perd des tokens et le proprietaire gagne
     du SOL) ou TRANSFERT (l'ATA perd des tokens, un autre proprietaire en gagne
     autant, le proprietaire ne gagne pas de SOL) ;
  4. pour le premier TRANSFERT, on note le delai depuis l'achat et le
     destinataire (le "collecteur"), puis on compte les tranches de vente du
     collecteur sur le meme mint.

Sortie: data/v07_exit.json
"""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_verif import rpc, get_tx, get_sigs, save, med, DATA, CACHE

V6 = json.load(open(f"{DATA}/v06_curve_ladder.json"))["lancements"]
LIM = int(os.environ.get("LIM", "0"))

def ata_of(sig, mint, owner):
    t = get_tx(sig)
    msg = t["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
    la = t["meta"].get("loadedAddresses") or {}
    allk = keys + (la.get("writable") or []) + (la.get("readonly") or [])
    for x in t["meta"].get("postTokenBalances") or []:
        if x.get("mint") == mint and x.get("owner") == owner:
            i = x["accountIndex"]
            if i < len(allk):
                return allk[i]
    return None

def sigs_all(addr, cap=6):
    out, before = [], None
    for _ in range(cap):
        r = get_sigs(addr, 1000, before)
        if not r:
            break
        out += r
        if len(r) < 1000:
            break
        before = r[-1]["signature"]
    return out

def classify(sig, mint, owner, ata):
    t = get_tx(sig)
    if not t or t["meta"].get("err"):
        return None
    m = t["meta"]
    msg = t["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
    la = m.get("loadedAddresses") or {}
    allk = keys + (la.get("writable") or []) + (la.get("readonly") or [])
    prem = {x["accountIndex"]: x for x in m.get("preTokenBalances") or []}
    delta_owner, deltas = 0.0, {}
    idxs = set(prem) | {x["accountIndex"] for x in (m.get("postTokenBalances") or [])}
    for i in idxs:
        pre = prem.get(i); post = None
        for x in m.get("postTokenBalances") or []:
            if x["accountIndex"] == i:
                post = x
        ref = post or pre
        if ref.get("mint") != mint:
            continue
        a0 = float((pre or {}).get("uiTokenAmount", {}).get("uiAmount") or 0)
        a1 = float((post or {}).get("uiTokenAmount", {}).get("uiAmount") or 0)
        o = ref.get("owner")
        deltas[o] = deltas.get(o, 0.0) + (a1 - a0)
        if i < len(allk) and allk[i] == ata:
            delta_owner += (a1 - a0)
    try:
        j = allk.index(owner)
        dsol = (m["postBalances"][j] - m["preBalances"][j]) / 1e9
    except ValueError:
        dsol = 0.0
    kind = None
    if delta_owner > 1:
        kind = "BUY"
    elif delta_owner < -1:
        gain = {k: v for k, v in deltas.items() if v > 1 and k != owner}
        kind = "SELL" if dsol > 0.0005 else ("TRANSFER" if gain else "BURN/OTHER")
    return {"sig": sig, "ts": t.get("blockTime"), "slot": t["slot"], "kind": kind,
            "dtok": round(delta_owner, 2), "dsol": round(dsol, 5),
            "dest": (max({k: v for k, v in deltas.items() if v > 1 and k != owner}.items(),
                         key=lambda kv: kv[1])[0]
                     if kind == "TRANSFER" else None)}

res = []
for L in (V6[:LIM] if LIM else V6):
    mint = L["mint"]
    bloc = [x for x in L["ladder"] if x["sol"] >= 5.0]
    per = []
    for b in bloc:
        w, sig = b["signer"], b["sig"]
        ata = ata_of(sig, mint, w)
        if not ata:
            continue
        ev = []
        for s in sigs_all(ata):
            c = classify(s["signature"], mint, w, ata)
            if c:
                ev.append(c)
        ev.sort(key=lambda x: (x["slot"], x["ts"] or 0))
        buy = next((e for e in ev if e["kind"] == "BUY"), None)
        tr = [e for e in ev if e["kind"] == "TRANSFER"]
        sl = [e for e in ev if e["kind"] == "SELL"]
        per.append({
          "wallet": w, "ata": ata, "n_events": len(ev),
          "buy_ts": buy["ts"] if buy else None,
          "n_transferts": len(tr), "n_ventes_directes": len(sl),
          "tokens_transferes": round(sum(-e["dtok"] for e in tr), 2),
          "tokens_vendus": round(sum(-e["dtok"] for e in sl), 2),
          "sol_vendu": round(sum(e["dsol"] for e in sl), 4),
          "premier_transfert_delai_s": ((tr[0]["ts"] - buy["ts"]) if (tr and buy and tr[0]["ts"] and buy["ts"]) else None),
          "premier_transfert_sig": tr[0]["sig"] if tr else None,
          "collecteur": tr[0]["dest"] if tr else None,
        })
    if not per:
        continue
    dl = [p["premier_transfert_delai_s"] for p in per if p["premier_transfert_delai_s"] is not None]
    tt = sum(p["tokens_transferes"] for p in per)
    tv = sum(p["tokens_vendus"] for p in per)
    res.append({"mint": mint, "n_wallets": len(per),
                "n_avec_transfert": sum(1 for p in per if p["n_transferts"]),
                "n_avec_vente_directe": sum(1 for p in per if p["n_ventes_directes"]),
                "tokens_transferes": round(tt, 2), "tokens_vendus_directement": round(tv, 2),
                "part_transferee": round(tt / (tt + tv), 4) if (tt + tv) else None,
                "delai_transfert_s_med": med(dl), "delai_transfert_s_min_max": [min(dl), max(dl)] if dl else None,
                "collecteurs": sorted({p["collecteur"] for p in per if p["collecteur"]}),
                "wallets": per})
    print(f"{mint[:12]:14s} n={len(per)} transf={res[-1]['n_avec_transfert']} "
          f"vente_dir={res[-1]['n_avec_vente_directe']} part_transf={res[-1]['part_transferee']} "
          f"delai_med={res[-1]['delai_transfert_s_med']}s coll={len(res[-1]['collecteurs'])}")

alld = [p["premier_transfert_delai_s"] for r in res for p in r["wallets"]
        if p["premier_transfert_delai_s"] is not None]
nw = sum(r["n_wallets"] for r in res)
agg = {
 "n_lancements": len(res), "n_wallets_bloc": nw,
 "n_wallets_avec_transfert": sum(r["n_avec_transfert"] for r in res),
 "n_wallets_avec_vente_directe": sum(r["n_avec_vente_directe"] for r in res),
 "part_supply_transferee_med": round(med([r["part_transferee"] for r in res
                                          if r["part_transferee"] is not None]), 4),
 "delai_transfert_s_med": med(alld), "n_delais": len(alld),
 "delai_transfert_s_q1q3": [round(st.quantiles(alld, n=4)[0], 1),
                            round(st.quantiles(alld, n=4)[2], 1)] if len(alld) > 3 else None,
 "delai_transfert_s_min_max": [min(alld), max(alld)] if alld else None,
 "n_collecteurs_distincts": len({c for r in res for c in r["collecteurs"]}),
}
save("v07_exit.json", {"agregats": agg, "lancements": res})
print(json.dumps(agg, indent=1))
