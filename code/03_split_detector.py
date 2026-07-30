#!/usr/bin/env python3
"""Détecteur de SPLIT — la pièce centrale du dépôt.

HYPOTHÈSE TESTÉE
----------------
Un opérateur qui veut faire passer N portefeuilles pour N acheteurs indépendants doit d'abord les
financer. S'il le fait en découpant une somme via un service de swap, les portefeuilles reçoivent
des montants **quasi identiques** dans une **fenêtre temporelle courte**. Un montant précis à la
neuvième décimale (ex. 1.393934883 SOL) répété sur plusieurs adresses n'est pas une coïncidence :
c'est la signature d'un découpage unique.

CE QUE LE SCRIPT MESURE
-----------------------
1. Pour un ensemble de portefeuilles (ex. les principaux détenteurs d'un token), il collecte les
   entrées de SOL et les regroupe par quasi-égalité de montant + proximité temporelle.
2. Il calcule le **taux de faux positifs** sur un groupe témoin de portefeuilles sans lien.
   Sans cette mesure, le détecteur ne vaut rien : des montants proches se produisent naturellement.

USAGE
-----
    python3 03_split_detector.py --mint <MINT> --top 30
    python3 03_split_detector.py --wallets w1,w2,w3
    python3 03_split_detector.py --mint <MINT> --control 40   # + groupe témoin

Nécessite une clé RPC Solana dans la variable d'environnement SOLANA_RPC_URL
(ex. https://mainnet.helius-rpc.com/?api-key=VOTRE_CLE). Aucune clé n'est stockée dans ce dépôt.
"""
from __future__ import annotations
import argparse, json, os, random, sys, time, urllib.request
from collections import defaultdict

RPC = os.environ.get("SOLANA_RPC_URL", "")
LAMPORTS = 1_000_000_000

# Fenêtre de montants retenue : en dessous, on capte le bruit (dust, frais) ;
# au-dessus, les transferts deviennent trop rares et hétérogènes pour former un split.
MIN_SOL, MAX_SOL = 1.0, 20.0
REL_TOL = 1e-4        # tolérance relative d'égalité des montants (0,01 %)
WINDOW_S = 3600       # fenêtre temporelle d'un même découpage
MIN_CLUSTER = 3       # nb minimal de portefeuilles pour parler de split


def rpc(method: str, params: list, retries: int = 4):
    if not RPC:
        sys.exit("SOLANA_RPC_URL non defini. Voir l'en-tete du script.")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                RPC, data=body,
                headers={"Content-Type": "application/json", "User-Agent": "split-detector/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                out = json.load(r)
            if "result" in out:
                return out["result"]
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    return None


def top_holders(mint: str, n: int) -> list[str]:
    """Principaux détenteurs d'un token, via leurs comptes de token."""
    res = rpc("getTokenLargestAccounts", [mint]) or {}
    owners = []
    for acc in (res.get("value") or [])[:n]:
        info = rpc("getAccountInfo", [acc["address"], {"encoding": "jsonParsed"}]) or {}
        try:
            owners.append(info["value"]["data"]["parsed"]["info"]["owner"])
        except Exception:
            continue
        time.sleep(0.15)
    return owners


def incoming_sol(wallet: str, max_pages: int = 3) -> list[tuple[float, int]]:
    """Entrées de SOL d'un portefeuille : [(montant_sol, timestamp)].

    On lit le delta de solde du portefeuille dans chaque transaction plutôt que les transferts
    système : le financement est souvent obfusqué (closeAccount d'un compte wrappé), auquel cas
    aucun transfert système n'apparaît alors que le solde augmente bien.
    """
    sigs, before = [], None
    for _ in range(max_pages):
        page = rpc("getSignaturesForAddress", [wallet, {"limit": 1000, "before": before}]) or []
        if not page:
            break
        sigs.extend(page)
        if len(page) < 1000:
            break
        before = page[-1]["signature"]
    out = []
    for s in sigs[-60:]:                     # les plus anciennes = le financement initial
        tx = rpc("getTransaction", [s["signature"],
                                    {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            continue
        try:
            keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
            i = keys.index(wallet)
            delta = (tx["meta"]["postBalances"][i] - tx["meta"]["preBalances"][i]) / LAMPORTS
        except Exception:
            continue
        if MIN_SOL <= delta <= MAX_SOL:
            out.append((delta, tx.get("blockTime") or 0))
        time.sleep(0.12)
    return out


def find_splits(funding: dict[str, list[tuple[float, int]]]) -> list[dict]:
    """Regroupe les portefeuilles par montant quasi identique reçu dans une même fenêtre."""
    events = [(w, amt, ts) for w, lst in funding.items() for amt, ts in lst]
    events.sort(key=lambda e: e[1])
    clusters, used = [], set()
    for i, (w, amt, ts) in enumerate(events):
        if i in used:
            continue
        group = [(i, w, amt, ts)]
        for j in range(i + 1, len(events)):
            if j in used:
                continue
            w2, amt2, ts2 = events[j]
            if abs(amt2 - amt) > amt * REL_TOL:
                break                          # trié par montant : au-delà, plus rien ne colle
            if w2 != w and abs(ts2 - ts) <= WINDOW_S:
                group.append((j, w2, amt2, ts2))
        wallets = {g[1] for g in group}
        if len(wallets) >= MIN_CLUSTER:
            for g in group:
                used.add(g[0])
            times = [g[3] for g in group]
            clusters.append({
                "amount_sol": round(amt, 9),
                "n_wallets": len(wallets),
                "wallets": sorted(wallets),
                "span_seconds": max(times) - min(times),
                "first_ts": min(times),
            })
    return sorted(clusters, key=lambda c: -c["n_wallets"])


def collect(wallets: list[str], label: str) -> dict:
    funding = {}
    for k, w in enumerate(wallets, 1):
        funding[w] = incoming_sol(w)
        print(f"  [{label}] {k}/{len(wallets)} {w[:12]}… {len(funding[w])} entrées", flush=True)
    return funding


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mint")
    ap.add_argument("--wallets")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--control", type=int, default=0,
                    help="taille du groupe témoin (portefeuilles sans lien) pour le taux de faux positifs")
    ap.add_argument("--out", default="../data/split/result.json")
    a = ap.parse_args()

    if a.wallets:
        wallets = [w.strip() for w in a.wallets.split(",") if w.strip()]
    elif a.mint:
        wallets = top_holders(a.mint, a.top)
    else:
        sys.exit("Fournir --mint ou --wallets.")
    print(f"{len(wallets)} portefeuilles à analyser", flush=True)

    clusters = find_splits(collect(wallets, "cible"))
    result = {"mint": a.mint, "n_wallets": len(wallets), "clusters": clusters,
              "n_clusters": len(clusters),
              "wallets_in_cluster": len({w for c in clusters for w in c["wallets"]}),
              "params": {"min_sol": MIN_SOL, "max_sol": MAX_SOL, "rel_tol": REL_TOL,
                         "window_s": WINDOW_S, "min_cluster": MIN_CLUSTER}}

    # Groupe témoin : des portefeuilles pris au hasard parmi des transactions récentes non liées.
    # C'est ce qui distingue un détecteur d'une illusion.
    if a.control:
        slot = rpc("getSlot", [])
        blk = rpc("getBlock", [slot - 200, {"maxSupportedTransactionVersion": 0,
                                            "transactionDetails": "accounts", "rewards": False}]) or {}
        pool = []
        for tx in (blk.get("transactions") or []):
            for k in (tx.get("transaction", {}).get("accountKeys") or []):
                pk = k.get("pubkey") if isinstance(k, dict) else k
                if pk and pk not in wallets:
                    pool.append(pk)
        random.seed(0)
        ctrl = random.sample(pool, min(a.control, len(pool))) if pool else []
        if ctrl:
            cc = find_splits(collect(ctrl, "témoin"))
            result["control"] = {"n_wallets": len(ctrl), "n_clusters": len(cc),
                                 "wallets_in_cluster": len({w for c in cc for w in c["wallets"]})}

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(result, open(a.out, "w"), indent=1)

    print(f"\n=== {len(clusters)} splits détectés sur {len(wallets)} portefeuilles ===")
    for c in clusters[:10]:
        print(f"  {c['amount_sol']:.9f} SOL × {c['n_wallets']} portefeuilles "
              f"(étalés sur {c['span_seconds']}s)")
    if result.get("control"):
        k = result["control"]
        print(f"\n  GROUPE TÉMOIN : {k['n_clusters']} splits sur {k['n_wallets']} portefeuilles")
        print("  → l'écart entre cible et témoin est la seule mesure qui compte.")


if __name__ == "__main__":
    main()
