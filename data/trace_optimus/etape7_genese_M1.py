#!/usr/bin/env python3
"""Etape 7 : aller chercher les geneses manquantes des premiers acheteurs d'OPTIMUS.

Lit e2_funding_<label>.json et le cache de pagination cache_sigs/, ecrit cache_sigs_full/ et
e7_genese_M1_<label>.json.

A l'etape 2 la pagination s'arretait des que la fenetre pre-achat (21 jours) etait couverte
(`stop_ts` dans lib_trace.all_signatures). Legitime pour la mesure M2, mais 17 portefeuilles sur 40
ressortaient avec `genesis_reached=False` alors que, pour 16 d'entre eux, la genese n'etait pas hors
de portee : on avait simplement cesse de paginer. Or c'est la mesure M1 (financement de naissance)
qui porte la signature du cas ODIN, plusieurs portefeuilles nes dans la meme transaction quelques
jours avant le token. Tant que la genese n'est pas atteinte, cette signature n'est pas testee et un
« aucun decoupage » ne vaut rien sur ces portefeuilles.

Le script reprend la pagination la ou le cache de l'etape 2 l'a laissee (parametre `before` = plus
ancienne signature deja vue), jusqu'a ce qu'une page revienne incomplete (la genese) ou jusqu'a un
plafond declare. Chaque portefeuille est rapporte avec son drapeau `genesis_reached` final. Aucun
portefeuille n'est declare « sans financement de naissance » si sa genese n'est pas atteinte.

Puis, pour ceux dont la genese est atteinte, il lit les premieres transactions de leur vie et en
extrait les entrees de SOL par delta de solde (piege nº2 : un financement livre par fermeture de
compte wrappe ne produit aucun transfert systeme).

Les cles viennent de ~/Downloads/.env et ne sont jamais ecrites dans un fichier du depot.

Usage :
    python3 etape7_genese_M1.py [--max-pages 3000] [--budget-s 900] [--workers 5]
"""
from __future__ import annotations
import argparse, json, os, sys, threading, time, datetime as dt
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_trace as L
from etape2_financement import inflows_from, MIN_INFLOW

CACHE_IN = os.path.join(HERE, "cache_sigs")
CACHE_OUT = os.path.join(HERE, "cache_sigs_full")
HEAD_TX = 60

_print_lock = threading.Lock()


def log(msg):
    with _print_lock:
        print(msg, flush=True)


def load_keys():
    keys = []
    p = os.path.expanduser("~/Downloads/.env")
    for line in open(p):
        if line.startswith("HELIUS_KEY="):
            k = line.strip().split("=", 1)[1]
            if k and k not in keys:
                keys.append(k)
    if not keys:
        sys.exit("aucune cle HELIUS_KEY trouvee")
    return keys


def rpc_with(url, method, params, tries=6):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers={
                "Content-Type": "application/json", "User-Agent": "trace-optimus/e7"})
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.load(r)
            if "result" in out:
                return out["result"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(1.0 + 1.5 * i)
                continue
            time.sleep(0.8 * (i + 1))
        except Exception:
            time.sleep(0.8 * (i + 1))
    return None


def resume_pagination(w, url, max_pages, budget_s):
    """Reprend la pagination d'un portefeuille depuis le cache de l'etape 2.

    Rend (sigs tries du plus ancien au plus recent, genesis_reached, pages_ajoutees, motif_arret).
    `genesis_reached=True` signifie qu'une page est revenue incomplete ou vide : le debut de
    l'historique a reellement ete vu. Tout autre motif d'arret laisse le drapeau a False et la
    mesure M1 est declaree non testee pour ce portefeuille.
    """
    p_in = os.path.join(CACHE_IN, f"{w}.json")
    p_out = os.path.join(CACHE_OUT, f"{w}.json")
    sigs, genesis = [], False
    if os.path.exists(p_out):
        try:
            c = json.load(open(p_out))
            sigs, genesis = c["sigs"], c["genesis"]
            if genesis:
                return sigs, True, 0, "deja_complet_en_cache"
        except Exception:
            sigs, genesis = [], False
    if not sigs and os.path.exists(p_in):
        try:
            c = json.load(open(p_in))
            sigs, genesis = c["sigs"], c.get("genesis", False)
        except Exception:
            pass
    seen = {s["signature"] for s in sigs}
    before = sigs[0]["signature"] if sigs else None
    t0, pages, reason = time.time(), 0, "plafond_pages"
    while pages < max_pages:
        if time.time() - t0 > budget_s:
            reason = "budget_temps"
            break
        pg = rpc_with(url, "getSignaturesForAddress", [w, {"limit": 1000, "before": before}])
        if pg is None:
            reason = "erreur_reseau_persistante"
            break
        pages += 1
        if not pg:
            genesis = True
            reason = "page_vide_GENESE"
            break
        for s in pg:
            if s["signature"] not in seen:
                seen.add(s["signature"])
                sigs.append({"signature": s["signature"], "blockTime": s.get("blockTime")})
        if len(pg) < 1000:
            genesis = True
            reason = "page_incomplete_GENESE"
            break
        before = pg[-1]["signature"]
        if pages % 100 == 0:
            ob = pg[-1].get("blockTime") or 0
            log(f"      … {w[:10]} +{pages} pages, remonte a "
                f"{dt.datetime.fromtimestamp(ob, dt.UTC):%Y-%m-%d}")
    sigs.sort(key=lambda s: (s.get("blockTime") or 0, s["signature"]))
    os.makedirs(CACHE_OUT, exist_ok=True)
    json.dump({"genesis": genesis, "sigs": sigs}, open(p_out, "w"))
    return sigs, genesis, pages, reason


def get_transactions_with(key, signatures, chunk=100):
    """Transactions parsees par paquets de cent. Une signature absente de la reponse est absente de
    la table rendue : jamais de zero silencieux."""
    url = f"https://api.helius.xyz/v0/transactions?api-key={key}"
    got = {}
    for i in range(0, len(signatures), chunk):
        sl = signatures[i:i + chunk]
        out = None
        for attempt in range(5):
            try:
                req = urllib.request.Request(
                    url, data=json.dumps({"transactions": sl}).encode(),
                    headers={"Content-Type": "application/json", "User-Agent": "trace-optimus/e7"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    out = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    return {"__error__": "403 sur POST /v0/transactions"}
                time.sleep(1.0 + 1.5 * attempt)
            except Exception:
                time.sleep(1.0 + 1.5 * attempt)
        if isinstance(out, list):
            for tx in out:
                if isinstance(tx, dict) and tx.get("signature"):
                    got[tx["signature"]] = tx
        time.sleep(0.1)
    return got


def work(job):
    w, first_buy_ts, rank, key, max_pages, budget_s = job
    url = f"https://mainnet.helius-rpc.com/?api-key={key}"
    sigs, genesis, pages, reason = resume_pagination(w, url, max_pages, budget_s)
    oldest = sigs[0]["blockTime"] if sigs else None
    info = {"wallet": w, "buy_rank": rank, "n_signatures_total": len(sigs),
            "pages_added": pages, "stop_reason": reason,
            "genesis_reached": genesis,
            "oldest_seen_ts": oldest, "oldest_seen_utc": L.utc(oldest),
            "days_alive_before_first_buy": (round((first_buy_ts - oldest) / 86400.0, 2)
                                            if genesis and oldest else None),
            "M1_tested": genesis, "M1_inflows": []}
    if genesis and sigs:
        head = [s["signature"] for s in sigs[:HEAD_TX]]
        txs = get_transactions_with(key, head)
        if "__error__" in txs:
            info["M1_tested"] = False
            info["measurement_failure"] = txs["__error__"]
            return info
        info["n_tx_fetched"] = len(txs)
        for sig in head:
            info["M1_inflows"].extend(inflows_from(txs, [sig], w, MIN_INFLOW, "M1_naissance"))
        info["M1_inflows"].sort(key=lambda f: f["ts"])
    else:
        info["measurement_failure"] = f"genese non atteinte ({reason})"
    g = "GENESE ATTEINTE" if genesis else "genese hors atteinte"
    log(f"  #{rank:>2d} {w[:14]}… {len(sigs):>7d} sigs (+{pages} pages) · {g} · "
        f"naissance {info['oldest_seen_utc']} · {len(info['M1_inflows'])} entrees M1 · {reason}")
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=3000)
    ap.add_argument("--budget-s", type=int, default=900)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--only", default=None, help="liste de portefeuilles separes par des virgules")
    ap.add_argument("--funding", default=os.path.join(HERE, "e2_funding_OPTIMUS.json"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    keys = load_keys()
    d = json.load(open(a.funding))
    label = d.get("label", "OPTIMUS")
    OUT = a.out or os.path.join(HERE, f"e7_genese_M1_{label}.json")
    todo = [w for w in d["wallets"] if not w["genesis_reached"]]
    if a.only:
        keep = set(a.only.split(","))
        todo = [w for w in todo if w["wallet"] in keep]
    # les plus legers d'abord : on encaisse les geneses faciles avant de payer les bots
    todo.sort(key=lambda w: w["n_signatures_total"])
    log(f"{len(todo)} portefeuilles sans genese a reprendre "
        f"(plafond {a.max_pages} pages, budget {a.budget_s}s/portefeuille, {len(keys)} cles)")

    jobs = [(w["wallet"], w["first_buy_ts"], w["buy_rank"], keys[i % len(keys)],
             a.max_pages, a.budget_s) for i, w in enumerate(todo)]
    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(work, jobs):
            results.append(r)
            json.dump({"label": label, "mint": d["mint"], "wallets": results},
                      open(OUT, "w"), indent=1)

    n_ok = sum(1 for r in results if r["genesis_reached"])
    res = {"label": label, "mint": d["mint"],
           "n_reprises": len(results), "n_geneses_nouvellement_atteintes": n_ok,
           "n_toujours_hors_atteinte": len(results) - n_ok,
           "toujours_hors_atteinte": [{"wallet": r["wallet"], "buy_rank": r["buy_rank"],
                                       "n_signatures_vues": r["n_signatures_total"],
                                       "remonte_a": r["oldest_seen_utc"],
                                       "motif": r["stop_reason"]}
                                      for r in results if not r["genesis_reached"]],
           "wallets": results}
    json.dump(res, open(OUT, "w"), indent=1)
    log(f"\n  geneses nouvellement atteintes : {n_ok}/{len(results)} -> {OUT}")


if __name__ == "__main__":
    main()
