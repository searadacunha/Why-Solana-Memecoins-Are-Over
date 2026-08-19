#!/usr/bin/env python3
"""Briques communes a l'analyse OPTIMUS.

Trois regles :

1. Pagination. `getSignaturesForAddress` ne remonte que du present vers le passe. On pagine
   jusqu'a ce qu'une page revienne incomplete (ou vide) et on rend le drapeau
   `genesis_reached`. Une mesure sans ce drapeau ne vaut rien.
2. Delta de solde. Le financement passe souvent par la fermeture d'un compte wrappe : aucun
   transfert systeme n'apparait alors que les soldes bougent. On mesure par delta pre/post.
3. Aucune cle en dur. Tout vient de l'environnement (SOLANA_RPC_URL, HELIUS_API_KEY).
"""
from __future__ import annotations
import json, os, sys, time, urllib.request, urllib.error, datetime as dt

RPC = os.environ.get("SOLANA_RPC_URL", "")
HELIUS_KEY = os.environ.get("HELIUS_API_KEY", "")
LAMPORTS = 1_000_000_000

SYSTEM_ACCOUNTS = {
    "11111111111111111111111111111111",
    "ComputeBudget111111111111111111111111111111",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
    "SysvarRent111111111111111111111111111111111",
    "So11111111111111111111111111111111111111112",
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",   # programme pump.fun
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
}

# Terminaux d'infrastructure connus. Aboutir ici est un fait de routage, pas une preuve
# d'implication du service : tout capital entrant sur Solana passe par une telle porte.
KNOWN = {
    "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t": "service de swap G2Y (cible de l'enquete)",
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "Binance hot wallet",
    "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6": "echange hot wallet",
    "2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS": "pont (solveur)",
    "u6PJ8DtQuPFnfmwHbGFULQ4u4EgjDiyYKjVEsynXq2w": "service de swap",
    "is6MTRHEgyFLNTfYcuV4QBWLjrZBfmhVNYR6ccgr8KV": "echange hot wallet",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "echange hot wallet",
    "H8sMJSCQxfKiFTCfDR3DUMLPwcRbM61LGFJ8N4dK3WjS": "Coinbase hot wallet",
    "2AQdpHJ2JpcEgPiATUXjQxA8QmafFegfQwSLWSprPicm": "Coinbase hot wallet",
    "AC5RDfQFmDS1deWZos921JfqscXdByf8BKHs5ACWjtW2": "Bybit hot wallet",
    "5VCwKtCXgCJ6kit5FybXjvriW3xELsFDhYrPSqtJNmcD": "OKX hot wallet",
    "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE": "Coinbase 2",
    "6QJzieMYfp7yr3EdrePaQoG3Ghxs2wM98xSLRu8Xh56U": "Kraken",
    "FWznbcNXWQuHTawe9RxvQ2LdCENssh12dsznf4RiouN5": "Kraken hot wallet",
    "ASTyfSima4LLAdDgoFGkgqoKowG1LZFDr9fAQrg7iaJZ": "MEXC hot wallet",
    "AobVSwdW9BbpMdJvTqeCN4hPAmh4rHm7vwLnQ5ATSyrS": "Robinhood",
    "3gd3dqgtJ4jWfBfLYTX67DALFetjc5iS72sCgRhCkW2u": "Bitget",
}


def _post(url, body, tries=6, timeout=60):
    data = json.dumps(body).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={
                "Content-Type": "application/json", "User-Agent": "trace-optimus/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(1.0 + 1.5 * i)
                continue
            time.sleep(0.8 * (i + 1))
        except Exception:
            time.sleep(0.8 * (i + 1))
    return None


def rpc(method, params, tries=6):
    if not RPC:
        sys.exit("SOLANA_RPC_URL non defini.")
    out = _post(RPC, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, tries)
    if isinstance(out, dict) and "result" in out:
        return out["result"]
    return None


def get_transactions(signatures, chunk=100, pause=0.12, progress=None):
    """Transactions parsees par paquets de cent, via l'API enrichie de Helius.

    Le JSON-RPC par lots est refuse par le plan gratuit. Cet endpoint rend cent transactions d'un
    coup, avec `accountData[].nativeBalanceChange`, le delta de solde deja calcule, qui capte les
    financements obfusques par fermeture de compte wrappe.

    Rend {signature: tx_parsee}. Une signature absente de la reponse est absente de la table
    rendue : jamais de zero silencieux.
    """
    if not HELIUS_KEY:
        sys.exit("HELIUS_API_KEY non defini.")
    # 2026-07-30 : api.helius.xyz repond 403 (error code 1010) sur toutes les cles.
    # C'est Cloudflare qui bloque l'hote, pas un refus d'auth : meme requete, meme
    # cle, sur api-mainnet.helius-rpc.com, ca passe. Ne pas rediagnostiquer ca en
    # "cle invalide", c'est le mauvais hote.
    # Sans le correctif, _post rend None sur 403, get_transactions rend {} sans
    # lever, et on lit "0 acheteur" partout. Zero silencieux.
    url = f"https://api-mainnet.helius-rpc.com/v0/transactions?api-key={HELIUS_KEY}"
    got, n_chunks_failed = {}, 0
    for i in range(0, len(signatures), chunk):
        sl = signatures[i:i + chunk]
        out = _post(url, {"transactions": sl})
        if not isinstance(out, list):
            n_chunks_failed += 1
        else:
            for tx in out:
                if isinstance(tx, dict) and tx.get("signature"):
                    got[tx["signature"]] = tx
        if progress:
            progress(len(got), len(signatures))
        time.sleep(pause)
    # Un lot perdu ne doit jamais passer pour un lot vide. On le rend visible a l'appelant.
    get_transactions.last_chunks_failed = n_chunks_failed
    if n_chunks_failed:
        print(f"      ⚠️ {n_chunks_failed} lot(s) de transactions non recuperes "
              f"({len(got)}/{len(signatures)} obtenues) — mesure incomplete", flush=True)
    return got


def all_signatures(addr, max_pages=2000, label="", verbose=True, stop_ts=None):
    """Signatures d'une adresse, de la plus ancienne a la plus recente.

    Rend (signatures triees, genesis_reached, n_pages). genesis_reached=False signifie que le debut
    de l'historique n'a pas ete vu : toute conclusion negative tiree de ces seules donnees est un
    echec de mesure, pas un resultat.

    `stop_ts` arrete la pagination des qu'une page contient une transaction anterieure a cet
    horodatage. Quand la mesure ne porte que sur une fenetre datee, la fenetre est alors
    entierement couverte et `genesis_reached` reste False sans que cela invalide la mesure,
    l'appelant distingue les deux cas.
    """
    out, before, genesis = [], None, False
    pages, newest, capped_by_projection = 0, None, False
    for i in range(max_pages):
        pg = None
        for attempt in range(3):                    # une page perdue ne doit pas passer pour la fin
            pg = rpc("getSignaturesForAddress", [addr, {"limit": 1000, "before": before}], tries=8)
            if pg is not None:
                break
            print(f"      ⚠️ {label} page {pages+1} illisible, nouvelle tentative", flush=True)
            time.sleep(3.0 * (attempt + 1))
        if pg is None:
            # Erreur reseau persistante : on ne declare pas la genese. L'appelant verra
            # genesis_reached=False et traitera le portefeuille comme non mesure.
            print(f"      ⚠️ {label} pagination interrompue par erreur reseau", flush=True)
            break
        pages += 1
        if not pg:
            genesis = True
            break
        out.extend(pg)
        if newest is None:
            newest = max((s.get("blockTime") or 0) for s in pg) or 0
        if len(pg) < 1000:
            genesis = True
            break
        oldest_page = min((s.get("blockTime") or 0) for s in pg if s.get("blockTime")) or 0
        if stop_ts and oldest_page and oldest_page <= stop_ts:
            break                                   # fenetre datee entierement couverte
        # Arret par projection : on ne s'arrete que si le plafond `max_pages` serait de toute
        # facon depasse d'au moins 50 %. La frontiere de decision est donc inchangee, seul le
        # temps de pagination est economise. Le motif est rendu a l'appelant.
        if stop_ts and oldest_page and pages >= 12:
            span_days = max((newest - oldest_page) / 86400.0, 0.01)
            rate = len(out) / span_days                       # signatures par jour
            days_left = (oldest_page - stop_ts) / 86400.0
            need = days_left * rate / 1000.0
            if need > 1.5 * max(max_pages - pages, 1):
                print(f"      ⚠️ {label} hyperactif : ~{rate:,.0f} sigs/jour, il faudrait "
                      f"~{need:,.0f} pages de plus pour couvrir la fenetre (plafond {max_pages}). "
                      f"Arret : portefeuille NON MESURE.", flush=True)
                capped_by_projection = True
                break
        before = pg[-1]["signature"]
        if verbose and i % 10 == 9:
            print(f"      … {label} {len(out)} sigs, remonte a "
                  f"{dt.datetime.fromtimestamp(oldest_page, dt.UTC):%Y-%m-%d}", flush=True)
        time.sleep(0.05)
    all_signatures.last_capped_by_projection = capped_by_projection
    return sorted(out, key=lambda s: (s.get("blockTime") or 0, s["signature"])), genesis, pages


def balance_deltas(tx):
    """{compte: delta_SOL} d'une transaction parsee, lu depuis accountData.

    Mesure par delta de solde, jamais par les seuls transferts systeme : un financement livre par
    fermeture d'un compte wrappe ne produit aucun transfert systeme alors que les soldes bougent.
    """
    out = {}
    for ad in (tx.get("accountData") or []):
        acc = ad.get("account")
        if acc:
            out[acc] = (ad.get("nativeBalanceChange") or 0) / LAMPORTS
    return out


def token_delta(tx, owner, mint):
    """Variation du solde du token `mint` pour le proprietaire `owner`, en unites entieres."""
    tot = 0.0
    for ad in (tx.get("accountData") or []):
        for tb in (ad.get("tokenBalanceChanges") or []):
            if tb.get("mint") != mint or tb.get("userAccount") != owner:
                continue
            raw = tb.get("rawTokenAmount") or {}
            try:
                tot += float(raw.get("tokenAmount") or 0) / (10 ** int(raw.get("decimals") or 0))
            except Exception:
                pass
    return tot


def tx_ts(tx):
    """Horodatage d'une transaction parsee."""
    return tx.get("timestamp") or 0


def signer_of(tx):
    """Le payeur de frais est le signataire principal : c'est l'acteur de la transaction."""
    return tx.get("feePayer")


def utc(ts):
    return dt.datetime.fromtimestamp(ts, dt.UTC).strftime("%Y-%m-%d %H:%M:%S") if ts else "?"


def helius_parsed(addr, before=None, limit=100, tries=5):
    """API de transactions parsees : cent transferts decodes par appel, deux ordres de grandeur
    plus efficace que getTransaction sur les adresses tres actives."""
    if not HELIUS_KEY:
        return []
    url = (f"https://api.helius.xyz/v0/addresses/{addr}/transactions"
           f"?api-key={HELIUS_KEY}&limit={limit}")
    if before:
        url += f"&before={before}"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json", "User-Agent": "trace-optimus/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return []
            time.sleep(1.2 * (i + 1))
        except Exception:
            time.sleep(1.2 * (i + 1))
    return []
