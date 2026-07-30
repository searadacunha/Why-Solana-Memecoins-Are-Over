#!/usr/bin/env python3
"""h2w6gm6jz — premiers ACHETEURS, genese de chaque portefeuille, financement, decoupages.

Derive de 04_early_buyers_funding.py, avec trois corrections imposees par les pieges deja
rencontres :

1. Les premiers acheteurs sont lus sur le compte BONDING CURVE (toutes les tx de la courbe y
   passent), pas sur le mint. Pagination menee jusqu'a page incomplete = genese garantie.
2. Un acheteur est identifie par un test explicite : delta SOL du signataire < -0.002 ET solde en
   token du signataire en HAUSSE. Un simple signataire n'est pas un acheteur.
3. Le financement est mesure par DELTA DE SOLDE (pre/postBalances), jamais par les seuls transferts
   systeme : la fermeture d'un compte wrappe ne produit aucun transfert systeme.

Sortie : JSON complet + resume texte. Pour CHAQUE portefeuille on reporte si sa genese a ete
atteinte. Un "aucun decoupage" n'est valable que si toutes les geneses le sont.
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.request, datetime as dt
from collections import defaultdict, Counter

RPC = os.environ.get("SOLANA_RPC_URL", "")
LAMPORTS = 1_000_000_000
SYSVAR_PREFIXES = ("Sysvar", "11111111111111111111111111111111")

# Terminaux connus : services de swap / echanges / ponts deja identifies.
KNOWN = {
    "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t": "service de swap (G2Y)",
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "echange (hot wallet)",
    "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6": "echange (hot wallet)",
    "2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS": "pont (solveur)",
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w": "service de swap",
    "is6MTRHEgyFLNTfYcuV4QBWLjrZBfmhVNYR6ccgr8KV": "echange (hot wallet)",
    "HRS6JqXcFgWrWxaBPjhnThQiWmUMkE3GrYHWR86tbFqR": "distributeur ODIN (12 SOL -> 4x3 SOL)",
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P": "programme pump.fun",
}


def _post(body, tries=5, timeout=60):
    data = json.dumps(body).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC, data=data, headers={
                "Content-Type": "application/json", "User-Agent": "trace-h2w6/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                print(f"    ! RPC echec definitif: {e}", flush=True)
            time.sleep(1.2 * (i + 1))
    return None


def rpc(method, params):
    out = _post({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    return (out or {}).get("result")


def rpc_batch(calls):
    """calls = [(method, params), ...] -> [result|None, ...] dans l'ordre."""
    if not calls:
        return []
    body = [{"jsonrpc": "2.0", "id": i, "method": m, "params": p} for i, (m, p) in enumerate(calls)]
    out = _post(body)
    res = [None] * len(calls)
    if isinstance(out, list):
        for o in out:
            if isinstance(o, dict) and isinstance(o.get("id"), int) and "result" in o:
                res[o["id"]] = o["result"]
    return res


def get_txs(sigs, chunk=20):
    """getTransaction jsonParsed en lots. Renvoie dict sig -> tx."""
    out = {}
    for i in range(0, len(sigs), chunk):
        part = sigs[i:i + chunk]
        got = rpc_batch([("getTransaction",
                          [s, {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
                         for s in part])
        # une seule relance individuelle pour les trous
        for s, tx in zip(part, got):
            if tx is None:
                tx = rpc("getTransaction",
                         [s, {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
            if tx is not None:
                out[s] = tx
        time.sleep(0.05)
    return out


def all_signatures(addr, max_pages=300, label=""):
    """TOUTES les signatures, de la plus ancienne a la plus recente.

    On s'arrete uniquement sur une page incomplete (ou vide) : c'est la seule preuve que la genese
    est atteinte. Si le plafond de pages est touche avant, genese_atteinte = False et le resultat
    doit etre qualifie de non concluant pour ce portefeuille.
    """
    out, before, complete, pages = [], None, False, 0
    while pages < max_pages:
        page = rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}])
        pages += 1
        if page is None:            # echec reseau : on refuse de conclure
            return sorted(out, key=lambda s: s.get("blockTime") or 0), False, pages
        if not page:
            complete = True
            break
        out.extend(page)
        if len(page) < 1000:
            complete = True
            break
        before = page[-1]["signature"]
        if label and pages % 20 == 0:
            oldest = min((s.get("blockTime") or 0) for s in page)
            print(f"     … {label} {len(out)} sigs, plus ancienne "
                  f"{dt.datetime.fromtimestamp(oldest, dt.UTC):%Y-%m-%d}", flush=True)
        time.sleep(0.05)
    return sorted(out, key=lambda s: s.get("blockTime") or 0), complete, pages


# ----------------------------------------------------------------------------- acheteurs precoces

def deltas(tx):
    """{compte: delta SOL} par difference de solde — insensible a l'obfuscation par compte wrappe."""
    keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
    pre, post = tx["meta"]["preBalances"], tx["meta"]["postBalances"]
    return {k: (post[i] - pre[i]) / LAMPORTS for i, k in enumerate(keys) if i < len(pre)}


def signer_of(tx):
    for k in tx["transaction"]["message"]["accountKeys"]:
        if k.get("signer") and not k.get("pubkey", "").startswith("Sysvar"):
            return k["pubkey"]
    return None


def token_gain(tx, mint, owner):
    pre = {(b.get("owner"), b.get("mint")): float(b["uiTokenAmount"]["uiAmount"] or 0)
           for b in tx["meta"].get("preTokenBalances") or []}
    post = {(b.get("owner"), b.get("mint")): float(b["uiTokenAmount"]["uiAmount"] or 0)
            for b in tx["meta"].get("postTokenBalances") or []}
    return post.get((owner, mint), 0.0) - pre.get((owner, mint), 0.0)


def early_buyers(curve, mint, n_early, scan):
    sigs, complete, pages = all_signatures(curve, label="courbe")
    print(f"  courbe : {len(sigs)} signatures, genese atteinte = {complete} ({pages} pages)")
    ok = [s for s in sigs if not s.get("err")]
    scan_sigs = [s["signature"] for s in ok[:scan]]
    txs = get_txs(scan_sigs)
    print(f"  {len(txs)}/{len(scan_sigs)} transactions de tete recuperees", flush=True)

    buyers, order, trades = {}, [], []
    for rank, s in enumerate(ok[:scan]):
        tx = txs.get(s["signature"])
        if not tx:
            continue
        try:
            w = signer_of(tx)
            d = deltas(tx).get(w, 0.0)
            g = token_gain(tx, mint, w)
        except Exception:
            continue
        kind = "BUY" if (g > 0 and d < -0.002) else ("SELL" if g < 0 else "autre")
        trades.append({"rank": rank, "sig": s["signature"], "ts": s.get("blockTime"),
                       "signer": w, "sol_delta": round(d, 9), "token_delta": g, "kind": kind})
        if kind == "BUY" and w not in buyers:
            buyers[w] = {"first_buy_ts": s.get("blockTime"), "rank": rank,
                         "sol_spent": round(-d, 9), "sig": s["signature"]}
            order.append(w)
            if len(order) >= n_early:
                break
    return order, buyers, trades, complete


# ------------------------------------------------------------------------------------ financement

def funding_of(wallet, first_buy_ts, max_first=45):
    """Genese + entrees de SOL avant le premier achat, mesurees par delta de solde."""
    sigs, complete, pages = all_signatures(wallet)
    n = len(sigs)
    if not sigs:
        return {"genese_atteinte": complete, "n_tx_total": 0, "pages": pages,
                "genesis": None, "inflows": []}
    head = [s["signature"] for s in sigs[:max_first]]
    txs = get_txs(head)
    inflows, genesis = [], None
    for s in sigs[:max_first]:
        tx = txs.get(s["signature"])
        if not tx:
            continue
        ts = s.get("blockTime") or 0
        try:
            d = deltas(tx)
        except Exception:
            continue
        gain = d.get(wallet, 0.0)
        if gain <= 0.001:
            continue
        # source = compte le plus debiteur, hors le portefeuille et hors comptes systeme
        cands = [(v, k) for k, v in d.items()
                 if k != wallet and v < 0 and not k.startswith("Sysvar")
                 and k != "11111111111111111111111111111111"]
        src = min(cands)[1] if cands else None
        src_amt = -min(cands)[0] if cands else None
        signer = signer_of(tx)
        ev = {"ts": ts, "sig": s["signature"], "amount_sol": round(gain, 9),
              "source": src, "source_debit_sol": round(src_amt, 9) if src_amt else None,
              "source_known": KNOWN.get(src), "tx_signer": signer,
              "self_signed": signer == wallet,
              "before_first_buy": bool(first_buy_ts and ts <= first_buy_ts)}
        if genesis is None:
            ev["is_genesis_tx"] = (s["signature"] == sigs[0]["signature"])
            genesis = ev
        inflows.append(ev)
    return {"genese_atteinte": complete, "n_tx_total": n, "pages": pages,
            "first_ts": sigs[0].get("blockTime"), "first_sig": sigs[0]["signature"],
            "genesis": genesis, "inflows": inflows}


# --------------------------------------------------------------------------------------- clusters

def split_clusters(fund, rel_tol=1e-4, window_s=3600, min_wallets=2):
    rows = []
    for w, f in fund.items():
        for ev in f["inflows"]:
            rows.append((ev["amount_sol"], ev["ts"], w, ev["source"], ev["sig"]))
    rows.sort()
    used, clusters = set(), []
    for i, (amt, ts, w, src, sig) in enumerate(rows):
        if i in used or amt <= 0.01:
            continue
        grp = [i]
        for j in range(i + 1, len(rows)):
            a2, t2, w2, _, _ = rows[j]
            if abs(a2 - amt) > max(amt * rel_tol, 1e-7):
                break
            if j not in used and w2 != w and abs(t2 - ts) <= window_s:
                grp.append(j)
        wal = {rows[k][2] for k in grp}
        if len(wal) >= min_wallets + 1:   # >=3 portefeuilles
            used.update(grp)
            ts_all = [rows[k][1] for k in grp]
            clusters.append({
                "amount_sol": amt, "n_wallets": len(wal), "wallets": sorted(wal),
                "sources": sorted({rows[k][3] for k in grp if rows[k][3]}),
                "span_seconds": max(ts_all) - min(ts_all),
                "date_utc": dt.datetime.fromtimestamp(min(ts_all), dt.UTC).strftime("%Y-%m-%d %H:%M:%S")})
    return sorted(clusters, key=lambda c: -c["n_wallets"])


def source_clusters(fund):
    by = defaultdict(list)
    for w, f in fund.items():
        for ev in f["inflows"]:
            if ev["source"]:
                by[ev["source"]].append((w, ev["amount_sol"], ev["ts"]))
    out = []
    for src, lst in by.items():
        wal = {x[0] for x in lst}
        if len(wal) >= 2:
            amts = Counter(round(x[1], 6) for x in lst)
            ts_all = [x[2] for x in lst]
            out.append({"source": src, "known": KNOWN.get(src), "n_wallets": len(wal),
                        "wallets": sorted(wal), "n_events": len(lst),
                        "amounts_repeated": [[a, c] for a, c in amts.most_common(8)],
                        "first_utc": dt.datetime.fromtimestamp(min(ts_all), dt.UTC).strftime("%Y-%m-%d %H:%M:%S"),
                        "last_utc": dt.datetime.fromtimestamp(max(ts_all), dt.UTC).strftime("%Y-%m-%d %H:%M:%S"),
                        "span_seconds": max(ts_all) - min(ts_all)})
    return sorted(out, key=lambda c: -c["n_wallets"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mint", default="FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump")
    ap.add_argument("--curve", default="5TSu3vPcYC1vrxoan9DJK9uQAAHUqmGTMBvnd1iLwzAg")
    ap.add_argument("--n-early", type=int, default=40)
    ap.add_argument("--scan", type=int, default=140, help="tx de tete de la courbe a examiner")
    ap.add_argument("--out", default="data/trace_h2w6/h2w6_early_funding.json")
    a = ap.parse_args()
    if not RPC:
        sys.exit("SOLANA_RPC_URL non defini.")

    print(f"=== h2w6gm6jz {a.mint} ===", flush=True)
    order, buyers, trades, curve_complete = early_buyers(a.curve, a.mint, a.n_early, a.scan)
    print(f"  {len(order)} ACHETEURS distincts precoces identifies "
          f"(sur {len(trades)} tx de tete analysees)\n", flush=True)

    fund = {}
    for k, w in enumerate(order, 1):
        fund[w] = funding_of(w, buyers[w]["first_buy_ts"])
        f = fund[w]
        flag = "" if f["genese_atteinte"] else "  ⚠️ GENESE NON ATTEINTE"
        g = f["genesis"]
        gs = (f"{g['amount_sol']:.9f} SOL de {(g['source'] or '?')[:12]}… "
              f"{dt.datetime.fromtimestamp(g['ts'], dt.UTC):%Y-%m-%d %H:%M}") if g else "aucune entree"
        print(f"  [{k}/{len(order)}] {w[:12]}… {f['n_tx_total']:>6d} tx | {gs}{flag}", flush=True)

    clus = split_clusters(fund)
    srcs = source_clusters(fund)
    n_ok = sum(1 for f in fund.values() if f["genese_atteinte"])

    res = {"mint": a.mint, "curve": a.curve, "genere_le": dt.datetime.now(dt.UTC).isoformat(),
           "courbe_genese_atteinte": curve_complete,
           "n_tx_tete_analysees": len(trades),
           "n_acheteurs_distincts": len(order),
           "n_geneses_atteintes": n_ok,
           "validite": ("resultat valable : toutes les geneses atteintes" if n_ok == len(order)
                        else f"ECHEC DE MESURE PARTIEL : {len(order)-n_ok} portefeuille(s) sans genese"),
           "buyers": buyers, "funding": fund,
           "clusters_montant": clus, "clusters_source": srcs,
           "trades_tete": trades}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)

    print(f"\n=== GENESES : {n_ok}/{len(order)} atteintes ===")
    print(f"=== {len(clus)} decoupages par MONTANT (>=3 portefeuilles, meme montant, <1h) ===")
    for c in clus[:15]:
        print(f"  {c['date_utc']}  {c['amount_sol']:.9f} SOL x {c['n_wallets']} "
              f"({c['span_seconds']}s) sources={[s[:8] for s in c['sources']]}")
    print(f"\n=== {len(srcs)} SOURCES alimentant >=2 acheteurs ===")
    for c in srcs[:20]:
        print(f"  {c['n_wallets']:>2d} portefeuilles  {c['source']}  {c['known'] or ''}"
              f"  {c['first_utc']} -> {c['last_utc']}  montants={c['amounts_repeated'][:3]}")
    print(f"\n  -> {a.out}")


if __name__ == "__main__":
    main()
