#!/usr/bin/env python3
"""GROUPE TEMOIN — taux de base du decoupage chez les premiers acheteurs.

CE QUE FAIT CE SCRIPT
---------------------
Il applique aux 9 tokens temoins EXACTEMENT la procedure de `code/04_early_buyers_funding.py`,
celle qui a produit le cas ODIN (4 portefeuilles nes de 12,0001 SOL decoupes en 4 x 3,000000000 SOL).
Aucun seuil n'est ajuste. Les constantes ci-dessous sont recopiees a l'identique de 04 :

    MIN_SOL = 0.5, MAX_SOL = 50.0      fenetre de montants d'une entree de financement
    REL_TOL = 1e-4                     tolerance d'egalite des montants (0,01 %)
    WINDOW_S = 3600                    fenetre temporelle d'un meme decoupage
    MIN_CLUSTER = 3                    nb minimal de portefeuilles pour parler de decoupage
    N_EARLY = 40                       premiers acheteurs distincts retenus
    EARLY_WINDOW_H = 48                fenetre apres la 1re tx du mint
    FIRST_TX_PER_WALLET = 40           nb de premieres tx inspectees par portefeuille
    MAX_PAGES_WALLET = 60              plafond de pagination par portefeuille (= 60 000 sigs)

SEULE DIFFERENCE AVEC 04 : la parallelisation (pool de threads + rotation de cles Helius).
Elle ne change aucune donnee mesuree, seulement le debit des appels RPC.

PIEGES TRAITES
--------------
1. PAGINATION SILENCIEUSE — chaque pagination s'arrete sur une page INCOMPLETE (genese atteinte)
   ou sur le plafond de pages. Le drapeau `genese_atteinte` est rapporte POUR CHAQUE PORTEFEUILLE
   et pour chaque mint. Un "aucun decoupage" sur un portefeuille dont la genese n'est pas atteinte
   n'est PAS un negatif : c'est un echec de mesure, et il est compte comme tel.
2. FINANCEMENT OBFUSQUE — les entrees sont mesurees par DELTA DE SOLDE (postBalances -
   preBalances), jamais par les transferts systeme, qui n'apparaissent pas lors d'une fermeture
   de compte wrappe.
3. MONTANT ROND vs MONTANT DE SWAP — chaque cluster detecte est classe : "rond" (versement
   delibere d'un distributeur) ou "issu d'une conversion" (>= 4 decimales significatives,
   signature d'un service de swap).
4. GROUPE TEMOIN — c'est precisement l'objet de ce script : il mesure le TAUX DE BASE.

USAGE
    python3 11_temoins_split.py --roles temoin
    python3 11_temoins_split.py --roles temoin,cible      # les deux, meme procedure
Les cles viennent de ~/Downloads/.env (lignes HELIUS_KEY). Aucune cle n'est ecrite dans le depot.
"""
from __future__ import annotations
import argparse, json, os, sys, threading, time, urllib.request, urllib.error
import datetime as dt
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- constantes recopiees a l'identique de 04_early_buyers_funding.py ----------------------------
LAMPORTS = 1_000_000_000
MIN_SOL, MAX_SOL = 0.5, 50.0
REL_TOL = 1e-4
WINDOW_S = 3600
MIN_CLUSTER = 3
N_EARLY = 40
EARLY_WINDOW_H = 48
FIRST_TX_PER_WALLET = 40
MAX_PAGES_WALLET = 60
MAX_PAGES_MINT = 400

BASE = ".."
CIBLES = f"{BASE}/data/cibles/cibles.json"
OUTDIR = f"{BASE}/data/trace_temoins"

# --- transport : rotation de cles + limiteur de debit par cle ------------------------------------
def load_keys() -> list[str]:
    keys, path = [], os.path.expanduser("~/Downloads/.env")
    env = os.environ.get("SOLANA_RPC_URL", "")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line.startswith("HELIUS_KEY="):
                k = line.split("=", 1)[1].strip()
                if k and k not in keys:
                    keys.append(k)
    urls = [f"https://mainnet.helius-rpc.com/?api-key={k}" for k in keys]
    if not urls and env:
        urls = [env]
    if not urls:
        sys.exit("Aucune cle RPC trouvee (HELIUS_KEY dans ~/Downloads/.env ou SOLANA_RPC_URL).")
    return urls


URLS = load_keys()
RPS_PER_KEY = 7.0
_locks = [threading.Lock() for _ in URLS]
_next_ok = [0.0 for _ in URLS]
_rr = threading.Semaphore(1)
_counter = [0]
_stats = {"calls": 0, "fails": 0}


def _pick() -> int:
    with _rr:
        i = _counter[0] % len(URLS)
        _counter[0] += 1
    return i


def rpc(method: str, params: list, tries: int = 5):
    """Appel RPC avec rotation de cles et limitation de debit. Rend None apres echec."""
    for attempt in range(tries):
        i = _pick()
        with _locks[i]:
            wait = _next_ok[i] - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            _next_ok[i] = time.monotonic() + 1.0 / RPS_PER_KEY
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        try:
            req = urllib.request.Request(URLS[i], data=body, headers={
                "Content-Type": "application/json", "User-Agent": "temoins-split/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            _stats["calls"] += 1
            if "result" in out:
                return out["result"]
        except Exception:
            pass
        time.sleep(0.6 * (attempt + 1))
    _stats["fails"] += 1
    return None


# --- pagination -----------------------------------------------------------------------------------
def paginate(addr: str, max_pages: int, stop_ts: int | None = None):
    """Signatures triees du plus ancien au plus recent + drapeau genese_atteinte.

    On ne s'arrete QUE sur une page vide ou incomplete (= genese atteinte), ou sur le plafond de
    pages (= genese NON atteinte, declaree comme telle). Si stop_ts est fourni, on peut aussi
    s'arreter des qu'on a depasse cette date vers le passe : la genese est alors couverte pour
    l'usage vise (les premieres tx du mint), ce qui est signale par `stop_ts_atteint`.
    """
    out, before, genesis, by_ts = [], None, False, False
    pages = 0
    for _ in range(max_pages):
        pg = rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}]) or []
        pages += 1
        if not pg:
            genesis = True
            break
        out.extend(pg)
        if len(pg) < 1000:
            genesis = True
            break
        oldest = min((s.get("blockTime") or 0) for s in pg)
        if stop_ts is not None and oldest and oldest <= stop_ts:
            by_ts = True
            break
        before = pg[-1]["signature"]
    return (sorted(out, key=lambda s: s.get("blockTime") or 0), genesis, by_ts, pages)


# --- etape 1 : premiers acheteurs d'un mint -------------------------------------------------------
def early_buyers(mint: str, created_ts: int):
    sigs, genesis, by_ts, pages = paginate(mint, MAX_PAGES_MINT, stop_ts=created_ts - 3600)
    if not sigs:
        return [], None, {"genese_atteinte": genesis, "pages": pages, "n_sigs": 0}
    t0 = sigs[0].get("blockTime")
    early = [s for s in sigs if (s.get("blockTime") or 0) <= t0 + EARLY_WINDOW_H * 3600]

    order, seen, sig_of = [], set(), {}
    def signer_of(s):
        tx = rpc("getTransaction", [s["signature"],
                                    {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            return None
        try:
            keys = tx["transaction"]["message"]["accountKeys"]
            return next(k["pubkey"] for k in keys if k.get("signer"))
        except Exception:
            return None

    # Les tx sont traitees dans l'ordre chronologique : identique a 04. Le fetch est parallelise
    # par blocs, mais l'ordre d'assignation reste chronologique strict.
    CH = 24
    for start in range(0, len(early), CH):
        if len(order) >= N_EARLY:
            break
        chunk = early[start:start + CH]
        with ThreadPoolExecutor(max_workers=12) as ex:
            signers = list(ex.map(signer_of, chunk))
        for s, sg in zip(chunk, signers):
            if len(order) >= N_EARLY:
                break
            if sg and sg not in seen:
                seen.add(sg)
                order.append(sg)
                sig_of[sg] = {"ts": s.get("blockTime"), "sig": s["signature"]}
    meta = {"genese_atteinte": genesis or by_ts, "genese_par_page_incomplete": genesis,
            "arret_par_date": by_ts, "pages": pages, "n_sigs": len(sigs),
            "n_sigs_fenetre_48h": len(early),
            "premiere_tx_utc": dt.datetime.fromtimestamp(t0, dt.UTC).isoformat()}
    return order, t0, {**meta, "premiere_apparition": sig_of}


# --- etape 2 : financement d'un portefeuille (delta de solde) -------------------------------------
def funding_events(wallet: str):
    sigs, genesis, _, pages = paginate(wallet, MAX_PAGES_WALLET)
    first = sigs[:FIRST_TX_PER_WALLET]

    def one(s):
        tx = rpc("getTransaction", [s["signature"],
                                    {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        if not tx:
            return None
        try:
            keys = [k["pubkey"] if isinstance(k, dict) else k
                    for k in tx["transaction"]["message"]["accountKeys"]]
            i = keys.index(wallet)
            pre, post = tx["meta"]["preBalances"], tx["meta"]["postBalances"]
            d = (post[i] - pre[i]) / LAMPORTS
        except Exception:
            return None
        if not (MIN_SOL <= d <= MAX_SOL):
            return None
        # source probable : le compte qui perd le plus dans la meme tx
        src, worst = None, 0.0
        for j, k in enumerate(keys):
            if j == i:
                continue
            dj = (post[j] - pre[j]) / LAMPORTS
            if dj < worst:
                worst, src = dj, k
        return {"sol": round(d, 9), "ts": tx.get("blockTime") or 0,
                "sig": s["signature"], "source_probable": src}

    with ThreadPoolExecutor(max_workers=10) as ex:
        res = [r for r in ex.map(one, first) if r]
    return res, {"genese_atteinte": genesis, "pages_paginees": pages,
                 "n_sigs_vues": len(sigs), "n_tx_inspectees": len(first),
                 "plus_ancienne_vue_utc": (dt.datetime.fromtimestamp(sigs[0]["blockTime"], dt.UTC)
                                           .isoformat() if sigs and sigs[0].get("blockTime") else None)}


# --- etape 3 : detection de decoupage (logique identique a 04) -------------------------------------
def decimales_significatives(x: float) -> int:
    s = f"{x:.9f}".rstrip("0")
    return 0 if "." not in s else len(s.split(".")[1])


def find_splits(funding: dict[str, list[dict]]) -> list[dict]:
    rows = sorted([(w, e["sol"], e["ts"], e.get("source_probable"))
                   for w, lst in funding.items() for e in lst], key=lambda r: r[1])
    clusters, used = [], set()
    for i, (w, amt, ts, src) in enumerate(rows):
        if i in used:
            continue
        grp = [(i, w, amt, ts, src)]
        for j in range(i + 1, len(rows)):
            if j in used:
                continue
            w2, a2, t2, s2 = rows[j]
            if abs(a2 - amt) > amt * REL_TOL:
                break
            if w2 != w and abs(t2 - ts) <= WINDOW_S:
                grp.append((j, w2, a2, t2, s2))
        wallets = {g[1] for g in grp}
        if len(wallets) >= MIN_CLUSTER:
            for g in grp:
                used.add(g[0])
            times = [g[3] for g in grp]
            nd = decimales_significatives(amt)
            clusters.append({
                "amount_sol": round(amt, 9), "n_wallets": len(wallets),
                "wallets": sorted(wallets), "span_seconds": max(times) - min(times),
                "date": dt.datetime.fromtimestamp(min(times), dt.UTC).strftime("%Y-%m-%d %H:%M"),
                "sources_probables": sorted({g[4] for g in grp if g[4]}),
                "decimales_significatives": nd,
                "nature_montant": "rond (versement delibere / distributeur)" if nd <= 3
                                  else "issu d'une conversion (signature de swap)"})
    return sorted(clusters, key=lambda c: -c["n_wallets"])


# --- pipeline par token ----------------------------------------------------------------------------
def analyse(tok: dict) -> dict:
    mint, sym = tok["mint"], tok.get("symbole") or tok["mint"][:8]
    created_ts = int(dt.datetime.fromisoformat(
        tok["date_creation_utc"].replace("Z", "+00:00")).timestamp())
    t_start = time.time()
    print(f"\n=== {sym} ({tok['role']}) {mint} ===", flush=True)
    buyers, t0, mint_meta = early_buyers(mint, created_ts)
    print(f"  mint : {mint_meta['n_sigs']} sigs, genese "
          f"{'ATTEINTE' if mint_meta['genese_atteinte'] else 'NON ATTEINTE'} | "
          f"{len(buyers)} acheteurs distincts precoces", flush=True)

    funding, wmeta = {}, {}
    def work(w):
        ev, m = funding_events(w)
        return w, ev, m
    with ThreadPoolExecutor(max_workers=10) as ex:
        for k, (w, ev, m) in enumerate(ex.map(work, buyers), 1):
            funding[w], wmeta[w] = ev, m
            flag = "" if m["genese_atteinte"] else "  << GENESE NON ATTEINTE"
            print(f"   [{k}/{len(buyers)}] {w[:14]}… {len(ev)} entrees, "
                  f"{m['n_sigs_vues']} sigs{flag}", flush=True)

    clusters = find_splits(funding)
    n_gen = sum(1 for m in wmeta.values() if m["genese_atteinte"])
    res = {
        "mint": mint, "symbole": sym, "role": tok["role"],
        "date_creation_utc": tok["date_creation_utc"],
        "fenetre_ancre": tok.get("fenetre_ancre"),
        "tx_totales_bonding_curve": tok.get("tx_totales_bonding_curve"),
        "premiere_tx_mint_utc": mint_meta.get("premiere_tx_utc"),
        "mint_pagination": {k: v for k, v in mint_meta.items() if k != "premiere_apparition"},
        "n_acheteurs_precoces_distincts": len(buyers),
        "acheteurs_insuffisants_moins_de_10": len(buyers) < 10,
        "n_portefeuilles_genese_atteinte": n_gen,
        "n_portefeuilles_genese_NON_atteinte": len(buyers) - n_gen,
        "part_genese_atteinte": round(n_gen / len(buyers), 3) if buyers else None,
        "n_clusters": len(clusters),
        "decoupage_detecte": bool(clusters),
        "portefeuilles_dans_un_cluster": sorted({w for c in clusters for w in c["wallets"]}),
        "clusters": clusters,
        "portefeuilles": [{"wallet": w, "premiere_apparition_ts":
                           mint_meta["premiere_apparition"].get(w, {}).get("ts"),
                           "n_entrees_financement": len(funding[w]),
                           "entrees": funding[w], **wmeta[w]} for w in buyers],
        "duree_analyse_s": round(time.time() - t_start, 1),
    }
    # Validite du negatif : un "aucun decoupage" ne vaut que si les geneses sont atteintes.
    if clusters:
        res["validite"] = "POSITIF — decoupage detecte"
    elif n_gen == len(buyers) and len(buyers) >= 10:
        res["validite"] = "NEGATIF VALIDE — toutes les geneses atteintes"
    elif len(buyers) < 10:
        res["validite"] = ("NON CONCLUANT — moins de 10 acheteurs precoces distincts : "
                           "le detecteur (MIN_CLUSTER=3) n'a pas de matiere")
    else:
        res["validite"] = (f"NEGATIF PARTIEL — {len(buyers)-n_gen}/{len(buyers)} portefeuilles "
                           "sans genese atteinte : echec de mesure sur ceux-la")
    print(f"  -> {res['n_clusters']} cluster(s) | geneses {n_gen}/{len(buyers)} | "
          f"{res['validite']}", flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roles", default="temoin")
    ap.add_argument("--only", default="", help="symboles separes par des virgules")
    ap.add_argument("--out", default=f"{OUTDIR}/temoins_split.json")
    a = ap.parse_args()

    cfg = json.load(open(CIBLES))
    roles = [r.strip() for r in a.roles.split(",")]
    toks = [t for t in (cfg["cibles"] + cfg["temoins"]) if t["role"] in roles]
    if a.only:
        keep = {s.strip() for s in a.only.split(",")}
        toks = [t for t in toks if t["symbole"] in keep]
    print(f"{len(toks)} tokens a analyser | {len(URLS)} cles RPC", flush=True)

    os.makedirs(OUTDIR, exist_ok=True)
    results = []
    for t in toks:
        r = analyse(t)
        results.append(r)
        json.dump({"genere_le": dt.datetime.now(dt.UTC).isoformat(),
                   "parametres": {"MIN_SOL": MIN_SOL, "MAX_SOL": MAX_SOL, "REL_TOL": REL_TOL,
                                  "WINDOW_S": WINDOW_S, "MIN_CLUSTER": MIN_CLUSTER,
                                  "N_EARLY": N_EARLY, "EARLY_WINDOW_H": EARLY_WINDOW_H,
                                  "FIRST_TX_PER_WALLET": FIRST_TX_PER_WALLET,
                                  "MAX_PAGES_WALLET": MAX_PAGES_WALLET,
                                  "source": "recopies a l'identique de code/04_early_buyers_funding.py"},
                   "rpc": {"appels": _stats["calls"], "echecs_definitifs": _stats["fails"]},
                   "tokens": results}, open(a.out, "w"), indent=1)

    pos = [r for r in results if r["decoupage_detecte"]]
    print(f"\n===== TAUX DE BASE : {len(pos)}/{len(results)} tokens avec decoupage =====")
    for r in results:
        print(f"  {r['symbole']:<12} {r['n_clusters']} cluster(s) | "
              f"{r['n_acheteurs_precoces_distincts']} acheteurs | "
              f"geneses {r['n_portefeuilles_genese_atteinte']}/"
              f"{r['n_acheteurs_precoces_distincts']} | {r['validite']}")
    print(f"\nEcrit dans {a.out}")


if __name__ == "__main__":
    main()
