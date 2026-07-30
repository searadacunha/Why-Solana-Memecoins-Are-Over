#!/usr/bin/env python3
"""Premiers acheteurs d'un token, puis recherche d'un SPLIT dans leur financement.

DÉMARCHE
--------
Les principaux détenteurs *actuels* d'un token ancien ne disent rien de son lancement : la supply a
changé de mains depuis. On remonte donc aux PREMIÈRES transactions du mint pour identifier ceux qui
étaient là au début, puis on regarde comment ces portefeuilles ont été financés.

Si un opérateur a découpé une somme via un service de swap pour alimenter N portefeuilles, ceux-ci
ont reçu des montants quasi identiques dans un intervalle court. C'est cette signature qu'on cherche.

USAGE
-----
    python3 04_early_buyers_funding.py --mint <MINT> --created 2024-11-22 --n-early 40

Nécessite SOLANA_RPC_URL dans l'environnement. Aucune clé n'est stockée dans ce dépôt.
"""
from __future__ import annotations
import argparse, json, os, sys, time, urllib.request, datetime as dt

RPC = os.environ.get("SOLANA_RPC_URL", "")
LAMPORTS = 1_000_000_000
MIN_SOL, MAX_SOL = 0.5, 50.0     # plus large ici : on ne connaît pas le calibre de l'époque
REL_TOL = 1e-4
WINDOW_S = 3600
MIN_CLUSTER = 3


def rpc(method, params, retries=4):
    if not RPC:
        sys.exit("SOLANA_RPC_URL non defini.")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(retries):
        try:
            req = urllib.request.Request(RPC, data=body, headers={
                "Content-Type": "application/json", "User-Agent": "early-buyers/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                out = json.load(r)
            if "result" in out:
                return out["result"]
        except Exception:
            pass
        time.sleep(1.5 * (i + 1))
    return None


def oldest_signatures(addr, stop_ts, max_pages=400):
    """Pagine jusqu'à atteindre stop_ts. Indispensable : une pagination bornée trop court ne
    remonte jamais à la création sur une adresse active, et fait conclure à tort."""
    out, before = [], None
    for i in range(max_pages):
        page = rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}]) or []
        if not page:
            break
        out.extend(page)
        oldest = min((s.get("blockTime") or 0) for s in page)
        if oldest and oldest <= stop_ts:
            break
        if len(page) < 1000:
            break
        before = page[-1]["signature"]
        if i % 20 == 19:
            print(f"  … {len(out)} signatures, plus ancienne "
                  f"{dt.datetime.fromtimestamp(oldest, dt.UTC):%Y-%m-%d}", flush=True)
        time.sleep(0.1)
    return sorted(out, key=lambda s: s.get("blockTime") or 0)


def early_buyers(mint, created_ts, n_early, window_h=48):
    """Signataires des premières transactions touchant le mint."""
    sigs = oldest_signatures(mint, created_ts - 3600)
    if not sigs:
        return [], None
    t0 = sigs[0].get("blockTime")
    print(f"  1re transaction du mint : {dt.datetime.fromtimestamp(t0, dt.UTC):%Y-%m-%d %H:%M} UTC")
    early = [s for s in sigs if (s.get("blockTime") or 0) <= t0 + window_h * 3600]
    buyers, order = {}, []
    for s in early:
        if len(order) >= n_early:
            break
        tx = rpc("getTransaction", [s["signature"],
                                    {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            continue
        try:
            keys = tx["transaction"]["message"]["accountKeys"]
            signer = next(k["pubkey"] for k in keys if k.get("signer"))
        except Exception:
            continue
        if signer not in buyers:
            buyers[signer] = s.get("blockTime")
            order.append(signer)
        time.sleep(0.1)
    return order, t0


def all_signatures(addr, max_pages=60):
    """TOUTES les signatures d'une adresse, de la plus ancienne à la plus récente.

    ⚠️ Ne pas borner cette pagination trop court. Le financement initial d'un portefeuille se trouve
    dans ses PREMIÈRES transactions ; une pagination partielle ne rend que les plus récentes et fait
    conclure à tort à l'absence de financement. On s'arrête quand une page revient incomplète —
    signe qu'on a atteint la genèse — et on signale si le plafond a été touché avant.
    """
    out, before, complete = [], None, False
    for _ in range(max_pages):
        page = rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}]) or []
        if not page:
            complete = True
            break
        out.extend(page)
        if len(page) < 1000:
            complete = True
            break
        before = page[-1]["signature"]
        time.sleep(0.08)
    return sorted(out, key=lambda s: s.get("blockTime") or 0), complete


def funding_events(wallet):
    """Entrées de SOL notables d'un portefeuille, mesurées par delta de solde.

    On lit les 40 PREMIÈRES transactions de son existence : c'est là que se trouve son financement.
    """
    sigs, complete = all_signatures(wallet)
    if not complete:
        print(f"     ⚠️ {wallet[:12]}… genese NON atteinte (trop actif) — resultat non concluant",
              flush=True)
    out = []
    for s in sigs[:40]:
        tx = rpc("getTransaction", [s["signature"],
                                    {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            continue
        try:
            keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
            i = keys.index(wallet)
            d = (tx["meta"]["postBalances"][i] - tx["meta"]["preBalances"][i]) / LAMPORTS
        except Exception:
            continue
        if MIN_SOL <= d <= MAX_SOL:
            out.append((d, tx.get("blockTime") or 0))
        time.sleep(0.08)
    return out


def find_splits(funding):
    rows = sorted([(w, a, t) for w, lst in funding.items() for a, t in lst], key=lambda r: r[1])
    clusters, used = [], set()
    for i, (w, amt, ts) in enumerate(rows):
        if i in used:
            continue
        grp = [(i, w, amt, ts)]
        for j in range(i + 1, len(rows)):
            if j in used:
                continue
            w2, a2, t2 = rows[j]
            if abs(a2 - amt) > amt * REL_TOL:
                break
            if w2 != w and abs(t2 - ts) <= WINDOW_S:
                grp.append((j, w2, a2, t2))
        wallets = {g[1] for g in grp}
        if len(wallets) >= MIN_CLUSTER:
            for g in grp:
                used.add(g[0])
            times = [g[3] for g in grp]
            clusters.append({"amount_sol": round(amt, 9), "n_wallets": len(wallets),
                             "wallets": sorted(wallets),
                             "span_seconds": max(times) - min(times),
                             "date": dt.datetime.fromtimestamp(min(times), dt.UTC)
                                       .strftime("%Y-%m-%d %H:%M")})
    return sorted(clusters, key=lambda c: -c["n_wallets"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mint", required=True)
    ap.add_argument("--created", required=True, help="date de creation approx., AAAA-MM-JJ")
    ap.add_argument("--n-early", type=int, default=40)
    ap.add_argument("--out", default="../data/split/early_buyers.json")
    a = ap.parse_args()

    created_ts = int(dt.datetime.strptime(a.created, "%Y-%m-%d")
                     .replace(tzinfo=dt.UTC).timestamp())
    print(f"Mint {a.mint[:16]}… — remontee jusqu'a {a.created}", flush=True)
    buyers, t0 = early_buyers(a.mint, created_ts, a.n_early)
    print(f"\n{len(buyers)} premiers signataires identifies", flush=True)

    funding = {}
    for k, w in enumerate(buyers, 1):
        funding[w] = funding_events(w)
        print(f"  [{k}/{len(buyers)}] {w[:14]}… {len(funding[w])} entrees", flush=True)

    clusters = find_splits(funding)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({"mint": a.mint, "first_tx_ts": t0, "n_early_buyers": len(buyers),
               "n_clusters": len(clusters), "clusters": clusters,
               "funding": {w: [[round(x, 9), t] for x, t in v] for w, v in funding.items()}},
              open(a.out, "w"), indent=1)

    print(f"\n=== {len(clusters)} splits detectes parmi les premiers acheteurs ===")
    for c in clusters[:12]:
        print(f"  {c['date']}  {c['amount_sol']:.9f} SOL x {c['n_wallets']} portefeuilles "
              f"({c['span_seconds']}s)")
    if not clusters:
        print("  Aucun. Resultat NEGATIF a conserver tel quel : soit le financement etait different,")
        print("  soit la fenetre/les seuils ne conviennent pas. Ne pas forcer les parametres.")


if __name__ == "__main__":
    main()
