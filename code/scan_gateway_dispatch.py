#!/usr/bin/env python3
"""Live detector for the gateway-dispatch funding pattern on a pump.fun launch.

WHAT IT DOES
------------
Given a mint, it reads every buyer on the bonding curve, works out which of them are freshly
created wallets, and reports those funded by a swap gateway before the token existed — with the
amount, the timestamp and the counterparty for each. It also groups wallets that received the same
amount in one burst, which is the strongest form of the signal.

This automates a check that is otherwise done by hand, one wallet at a time, in an explorer.

WHAT MAKES IT A MEASUREMENT AND NOT A GUESS
-------------------------------------------
Four rules, each of which exists because breaking it produced a wrong answer in this project:

1. **Page to genesis, or say you did not.** `getSignaturesForAddress` walks present -> past. Bounded
   too short it returns only recent history and fails *without an error*. A wallet's funding lives
   in its first transactions, so a partial walk reports "no funding" for a funded wallet. Every
   wallet here carries an explicit status: measured, or unreadable.

2. **Errors raise.** A client returning None on error, with a caller writing `or []`, turns an
   exhausted quota into "this curve has no transactions". That produced a clean `0/14 tokens` in
   this project, from a wrong hostname. Here a failed call raises and the token is reported
   UNMEASURABLE, never as a zero.

3. **Chronology is enforced.** A gateway payment landing after the token was created cannot have
   funded its launch. Those are counted separately, never mixed into the total.

4. **Report the calibre, never require it.** A conversion output (nine significant decimals) and a
   round payment from an intermediate distributor are two links of one chain. Requiring the first
   misses every case that runs through the second.

USAGE
    export HELIUS_API_KEYS=key1[,key2,...]
    python3 code/scan_gateway_dispatch.py --mint <MINT> [--created 2024-12-13] [--json out.json]
    python3 code/scan_gateway_dispatch.py --mint <MINT> --gateway <ADDR> --fresh-days 7

No address is hard-coded as a gateway beyond the default below, and no service is named: a gateway
is an address through which capital enters the chain. Reaching one is a routing fact.
"""
from __future__ import annotations
import argparse, json, sys, time, urllib.error, urllib.request, datetime as dt
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import rpc_client
import settings

# Endpoint de decodage par LOT de signatures (POST /v0/transactions). Il n'a pas
# d'equivalent dans rpc_client (qui expose l'enhanced PAR ADRESSE, pas le lot par
# signatures), donc post_parsed() reste local. Le JSON-RPC et l'enhanced par
# adresse, eux, passent desormais par rpc_client.
PARSED_TX = "https://api-mainnet.helius-rpc.com/v0/transactions?api-key={key}"
LAMPORTS = 1e9
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
DEFAULT_GATEWAY = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"


class RpcError(Exception):
    """A call that did not complete. DISTINCT from an empty answer — see rule 2."""


def keys():
    ks = settings.helius_keys()
    if not ks:
        sys.exit("HELIUS_API_KEYS non defini. export HELIUS_API_KEYS=cle1[,cle2]")
    return ks


KEYS = None


def rpc(method, params, ki=0, tries=6):
    """Transport delegue a rpc_client (rotation de cles, cooldown 429, reprises
    bornees). On conserve RpcError : un echec LEVE, jamais un None confondu avec
    un vide (regle 2). ki/tries sont ignores -- rpc_client possede la rotation --
    mais gardes pour ne pas toucher aux appelants."""
    try:
        return rpc_client.rpc(method, params)
    except rpc_client.HeliusError as e:
        raise RpcError(f"{method} a echoue : {e}")


def post_parsed(sigs, ki=0, tries=5):
    last = None
    for i in range(tries):
        key = KEYS[(ki + i) % len(KEYS)]
        try:
            req = urllib.request.Request(
                PARSED_TX.format(key=key),
                data=json.dumps({"transactions": sigs}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(2.0 * (i + 1))
    raise RpcError(f"decodage d'un lot de {len(sigs)} tx impossible : {last}")


# ---------------------------------------------------------------------------- token -------------

def bonding_curve(mint):
    """The curve account, read from the pump API. Falls back to None, never guesses."""
    try:
        req = urllib.request.Request(
            f"https://frontend-api-v3.pump.fun/coins/{mint}",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        ts = d.get("created_timestamp")
        return d.get("bonding_curve"), (ts / 1000 if ts else None), d.get("symbol")
    except (urllib.error.URLError, TimeoutError, ValueError):
        # None ici = repli VOULU vers le drapeau --created (l'API pump ne repond
        # pas ou ne connait pas ce mint), pas une mesure a zero silencieuse.
        return None, None, None


def curve_buyers(curve):
    """Every distinct fee payer on the curve, oldest first. Raises rather than returning empty
    or truncated: a page budget exhausted before genesis is a failure, not a measurement."""
    try:
        sigs, _ = rpc_client.walk_sigs(curve, max_pages=60)
    except rpc_client.HeliusError as e:
        raise RpcError(f"courbe {curve[:12]}… : {e}")
    if not sigs:
        raise RpcError(f"courbe {curve[:12]}… : zero signature. Une courbe active en a "
                       f"des centaines — c'est une panne, pas une mesure.")
    sigs.sort(key=lambda s: s.get("blockTime") or 0)

    seen, order = set(), []
    for i in range(0, len(sigs), 100):
        for tx in post_parsed([s["signature"] for s in sigs[i:i + 100]], ki=i // 100):
            fp = tx.get("feePayer")
            if fp and fp not in seen:
                seen.add(fp)
                order.append(fp)
        time.sleep(0.25)
    return order, len(sigs)


# --------------------------------------------------------------------------- wallet -------------

def probe(args):
    """Fresh? And if so, funded by the gateway when?

    The early exit is what makes a full-curve scan affordable: a fresh wallet has no activity
    before the window, so the moment we see an older transaction the wallet is disqualified and we
    stop. Hyperactive addresses exit after one page instead of four hundred.
    """
    idx, wallet, cut_fresh, cut_token, gateway = args
    before, oldest, genesis = None, None, False
    for _ in range(40):
        try:
            page = rpc("getSignaturesForAddress",
                       [wallet, {"limit": 1000, "before": before}], ki=idx)
        except RpcError as e:
            return wallet, {"statut": "illisible", "detail": str(e)[:120]}
        if not page:
            genesis = True
            break
        o = min((s.get("blockTime") or 0) for s in page)
        oldest = o if oldest is None else min(oldest, o)
        if oldest < cut_fresh:
            return wallet, {"statut": "ancien", "plus_ancienne_activite": iso(oldest)}
        if len(page) < 1000:
            genesis = True
            break
        before = page[-1]["signature"]
        time.sleep(0.1)

    if not genesis or oldest is None:
        return wallet, {"statut": "illisible", "detail": "genese non atteinte"}

    hits, before2 = [], None
    for _ in range(20):
        try:
            batch = rpc_client.enhanced(wallet, before=before2)
        except rpc_client.HeliusError:
            return wallet, {"statut": "illisible", "detail": "transactions parsees illisibles"}
        if not batch:
            break
        for tx in batch:
            ts = tx.get("timestamp") or 0
            for t in (tx.get("nativeTransfers") or []):
                if t.get("fromUserAccount") == gateway and t.get("toUserAccount") == wallet:
                    amt = (t.get("amount") or 0) / LAMPORTS
                    hits.append({"sol": round(amt, 9), "ts": ts, "utc": iso(ts, True),
                                 "avant_token": ts <= cut_token,
                                 "calibre": calibre(amt)})
        if len(batch) < 100:
            break
        before2 = batch[-1].get("signature")
        time.sleep(0.1)

    return wallet, {"statut": "vierge", "naissance": iso(oldest),
                    "age_jours": round((cut_token - oldest) / 86400, 2),
                    "versements_guichet": sorted(hits, key=lambda h: h["ts"])}


def iso(ts, sec=False):
    if not ts:
        return None
    f = "%Y-%m-%d %H:%M:%S" if sec else "%Y-%m-%d"
    return dt.datetime.fromtimestamp(ts, dt.UTC).strftime(f)


def calibre(a):
    """A conversion output has nine significant decimals; a chosen payment is round."""
    for d in (0, 1, 2, 3):
        if abs(a - round(a, d)) < 1e-9:
            return f"rond_{d}" if d else "rond_SOL"
    return "sortie_de_swap"


def bursts(rows, rel_tol=1e-3, window_s=3600, min_wallets=2):
    """Wallets that received the same amount inside one window — the strongest form of the signal."""
    flat = sorted([(w, h["sol"], h["ts"], h["utc"]) for w, hs in rows for h in hs],
                  key=lambda r: (r[1], r[2]))
    out, used = [], set()
    for i, (w, amt, ts, u) in enumerate(flat):
        if i in used or amt <= 0:
            continue
        grp, idx = [(w, amt, ts, u)], [i]
        for j in range(i + 1, len(flat)):
            if j in used:
                continue
            w2, a2, t2, u2 = flat[j]
            if abs(a2 - amt) > amt * rel_tol:
                break
            if w2 != w and abs(t2 - ts) <= window_s:
                grp.append((w2, a2, t2, u2))
                idx.append(j)
        ws = {g[0] for g in grp}
        if len(ws) >= min_wallets:
            used.update(idx)
            times = [g[2] for g in grp]
            out.append({"montant_sol": round(amt, 9), "n_portefeuilles": len(ws),
                        "etendue_s": max(times) - min(times), "calibre": calibre(amt),
                        "premier": min(g[3] for g in grp), "portefeuilles": sorted(ws)})
    return sorted(out, key=lambda c: (-c["n_portefeuilles"], c["etendue_s"]))


def main():
    global KEYS
    ap = argparse.ArgumentParser()
    ap.add_argument("--mint", required=True)
    ap.add_argument("--gateway", default=DEFAULT_GATEWAY)
    ap.add_argument("--created", help="AAAA-MM-JJ si l'API pump ne repond pas")
    ap.add_argument("--fresh-days", type=float, default=7.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--json", help="ecrire le detail complet dans ce fichier")
    a = ap.parse_args()
    KEYS = keys()

    curve, created_ts, symbol = bonding_curve(a.mint)
    if a.created:
        created_ts = dt.datetime.strptime(a.created, "%Y-%m-%d").replace(
            tzinfo=dt.UTC).timestamp()
    if not curve or not created_ts:
        sys.exit("courbe ou date de creation introuvable — passer --created, ou mint hors pump.fun")

    cut_token = int(created_ts)
    cut_fresh = cut_token - int(a.fresh_days * 86400)
    print(f"{symbol or a.mint[:8]}  cree {iso(cut_token, True)} UTC")
    print(f"  courbe {curve}")

    try:
        buyers, n_tx = curve_buyers(curve)
    except RpcError as e:
        sys.exit(f"MESURE IMPOSSIBLE : {e}")
    print(f"  {n_tx} transactions de courbe, {len(buyers)} acheteurs distincts\n")

    out = {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i, (w, r) in enumerate(ex.map(
                probe, [(i, w, cut_fresh, cut_token, a.gateway) for i, w in enumerate(buyers)])):
            out[w] = r
            if (i + 1) % 50 == 0:
                print(f"  … {i + 1}/{len(buyers)}", flush=True)

    par_statut = defaultdict(int)
    for r in out.values():
        par_statut[r["statut"]] += 1
    vierges = {w: r for w, r in out.items() if r["statut"] == "vierge"}
    avant = {w: [h for h in r["versements_guichet"] if h["avant_token"]]
             for w, r in vierges.items() if any(h["avant_token"] for h in r["versements_guichet"])}
    apres = sum(1 for r in vierges.values()
                if r["versements_guichet"] and not any(h["avant_token"]
                                                       for h in r["versements_guichet"]))

    print(f"\n  acheteurs      : {len(buyers)}")
    print(f"  vierges        : {par_statut['vierge']}")
    print(f"  anciens        : {par_statut['ancien']}")
    print(f"  ILLISIBLES     : {par_statut['illisible']}   "
          f"(un negatif ne vaut rien pour ceux-la)")
    print(f"\n  >>> {len(avant)} portefeuille(s) VIERGE(S) finance(s) par le guichet "
          f"AVANT le token   ({apres} apres, ecarte(s))")
    for w, hs in sorted(avant.items(), key=lambda kv: kv[1][0]["ts"]):
        for h in hs:
            print(f"      {w}  {h['sol']:.9f} SOL  {h['utc']}  "
                  f"[{h['calibre']}, portefeuille ne il y a "
                  f"{vierges[w]['age_jours']:.1f} j]")

    b = bursts([(w, hs) for w, hs in avant.items()])
    if b:
        print(f"\n  RAFALES (meme montant, meme fenetre) :")
        for c in b:
            print(f"      {c['n_portefeuilles']} portefeuilles x {c['montant_sol']:.9f} SOL "
                  f"en {c['etendue_s']} s  [{c['calibre']}]  {c['premier']}")

    res = {"mint": a.mint, "symbole": symbol, "courbe": curve,
           "creation_utc": iso(cut_token, True), "guichet": a.gateway,
           "fraicheur_jours": a.fresh_days,
           "n_tx_courbe": n_tx, "n_acheteurs": len(buyers),
           "n_vierges": par_statut["vierge"], "n_anciens": par_statut["ancien"],
           "n_illisibles": par_statut["illisible"],
           "n_vierges_finances_avant_token": len(avant),
           "n_vierges_finances_apres_token": apres,
           "portefeuilles_confirmes": {w: {"versements": hs, "age_jours": vierges[w]["age_jours"],
                                           "naissance": vierges[w]["naissance"]}
                                       for w, hs in avant.items()},
           "rafales": b, "detail": out}
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1, ensure_ascii=False)
        print(f"\n-> {a.json}")


if __name__ == "__main__":
    main()
