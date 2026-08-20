#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Anchor the account in real tokens, and date the pump.fun market.

(A) symbols: do the tokens the account names (EPEP, TEST, the "orbit" family)
exist, how many distinct mints carry each symbol, and which one reaches the
market cap being claimed. The frequent result is dozens of homonyms and none
that matches. That is a measurement, not a failure.
(B) on-chain facts per retained candidate: the creation date read from the chain
(the mint account's oldest signature), the originating program, and the status.
The chain is the only source reaching back to 2024, third-party APIs stop before
it (the report's `couverture_api` field).
(C) monthly chronology since January 2024: creations per month, share graduated,
distribution of highs.

The method behind (C): no public API returns how many tokens were created in a
given month, and pump.fun's offset pagination does not reach 2024, which would
take millions of pages. But every pump.fun creation involves the program's mint
authority, a constant PDA (see MINT_AUTHORITY), so the signatures of that single
account are the exhaustive index of creations, in reverse chronological order. A
page of getSignaturesForAddress taken before a signature S returns the 1000
creations preceding S, and the time they span gives an instantaneous rate;
`before` accepts any signature on the ledger, which is what allows anchoring to
a date (date -> slot -> any signature in that block). The monthly total is
therefore an extrapolation, the integration of rates measured at N anchors
spread through the month, with the dispersion between anchors reported. The
mints sampled at those anchors, on the other hand, are drawn with no selection
bias: taken from the index as it comes, not from some API's "top" list.

Evidence levels: [MESURE] recomputed by this script from the chain or a public
API, [ESTIME] an explicit extrapolation from a measurement (the monthly totals),
[NON ETABLI] never quoted as a fact.

Usage:
    python3 code/01_ancrage.py search     # (A) the symbols quoted
    python3 code/01_ancrage.py onchain    # (B) the candidates' on-chain facts
    python3 code/01_ancrage.py chrono     # (C) the monthly chronology
    python3 code/01_ancrage.py report     # assembles data/ancrage/ancrage.json
    python3 code/01_ancrage.py all

No key is written to disk or into any output (see settings.py).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import redact
import rpc_client
import settings

# --------------------------------------------------------------------- paths
OUT = settings.data("ancrage")
CACHE = os.path.join(settings.CACHE, "ancrage")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

# ------------------------------------------------------------------ constants
# The pump.fun program's mint-authority PDA. Present in every pump.fun token
# creation and, as `verif_creations` checks below, in nothing else.
MINT_AUTHORITY = "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Two slot/time anchors measured on the chain, seeding the date -> slot
# conversion. getBlockTime refines them on every call, so a drift in the initial
# estimate introduces no error, only extra iterations.
ANCHOR_HI = (435964490, 1785335387)
ANCHOR_LO = (306215569, 1733674757)
SLOTS_PER_SEC = (ANCHOR_HI[0] - ANCHOR_LO[0]) / (ANCHOR_HI[1] - ANCHOR_LO[1])

# The window of "regime 1" as the account describes it, in UTC.
REGIME1 = (dt.datetime(2024, 10, 1, tzinfo=dt.timezone.utc),
           dt.datetime(2025, 3, 1, tzinfo=dt.timezone.utc))

# Symbols to anchor. `attendu_usd` is the highest market cap the account
# claims; it is a target to confront, never a filter.
CIBLES = [
    {"terme": "EPEP", "symbole": "EPEP", "attendu_usd": 40e6},
    {"terme": "TEST", "symbole": "TEST", "attendu_usd": 10e6},
    {"terme": "orbit", "symbole": None, "attendu_usd": 100e6},
]
# Control families: words as ordinary as "orbit", drawn from an unrelated
# lexical field of objects and nature, to have a base rate for the number of
# homonymous mints and for the shape of the distribution of highs.
FAMILLES_TEMOIN = ["lantern", "pebble", "marble", "willow", "compass"]


def utcday(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()


# ------------------------------------------------------------------ http ----
class Http:
    """A thin adapter. The Solana JSON-RPC transport is delegated to the shared
    rpc_client (key rotation, cooldown after a 429, bounded retries); what is
    kept here is the translation to the (result, error) contract the callers
    expect, plus the small web() GET towards the pump, dexscreener and jup
    frontends, which are not Helius endpoints.

    The calls are counted and the total is reported in the output, so that the
    cost of reproducing this is known before anyone re-runs it.
    """

    def __init__(self):
        self.n_rpc = 0
        self.n_web = 0

    # -- Solana JSON-RPC (transport delegue a rpc_client) -------------------
    def rpc(self, method, params):
        """Returns (result, error). An error must not be confused with an empty
        answer: that confusion made it look, while this was being written, as
        though the EPEP mint's history stopped in 2024-12. rpc_client.rpc raises
        HeliusError on a failure, whether transport or a JSON-RPC `error` object,
        and it is translated back into a tuple so the callers do not change.
        """
        self.n_rpc += 1
        try:
            return rpc_client.rpc(method, params), None
        except rpc_client.HeliusError as e:
            return None, settings.redact_key(str(e))

    def sigs(self, addr, limit=1000, before=None):
        self.n_rpc += 1
        try:
            return rpc_client.sigs(addr, limit, before), None
        except rpc_client.HeliusError as e:
            return None, settings.redact_key(str(e))

    # -- web (the pump / dexscreener / jup frontends, not a Helius endpoint) --
    def web(self, url, tries=5, timeout=60):
        """A small local GET. It retries on 429, 5xx and transport errors, returns
        {"_error": ...} on a final HTTP status that cannot be replayed (404, for
        instance: an absent token is an answer, not an outage), but raises once the
        attempts are exhausted, a network outage having no business hiding as an
        empty page.
        """
        self.n_web += 1
        last = None
        for t in range(tries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                last = "HTTP %d" % e.code
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(min(8.0, 0.8 * (t + 1) ** 2))
                    continue
                return {"_error": last}
            except Exception as e:                      # noqa: BLE001
                last = type(e).__name__ + ": " + str(e)[:120]
                time.sleep(min(8.0, 0.8 * (t + 1)))
        raise RuntimeError("web GET epuise apres %d essais : %s"
                           % (tries, settings.redact_key(str(last))))


H = Http()


def cached(name, fn):
    """Disk cache of the network calls, under data/cache/, which is not published:
    it is an exact mirror of public data.
    """
    p = os.path.join(CACHE, name + ".json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:                                # noqa: BLE001
            pass
    v = fn()
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(v, f)
    os.replace(tmp, p)
    return v


def dump(obj, name):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(redact.scrub(obj), f, indent=1, sort_keys=True)
    print("  -> %s" % os.path.relpath(path, settings.ROOT))
    return path


# ============================================================== (A) SYMBOLES =
def pump_search(term, max_pages=40, limit=50):
    """Every pump.fun mint whose name or symbol contains `term`.

    The pump.fun API's paginated full-text search covers the whole history of
    the program; this was checked, tokens from March 2024 come back. It is the
    only source that returns `ath_market_cap`, the highest market cap reached,
    for a token long dead.
    """
    out, off = {}, 0
    for _ in range(max_pages):
        url = ("https://frontend-api-v3.pump.fun/coins?searchTerm=%s&limit=%d"
               "&offset=%d&sort=market_cap&order=DESC&includeNsfw=true"
               % (urllib.parse.quote(term), limit, off))
        d = cached("pumpsearch_%s_%d" % (term.replace(" ", "_"), off),
                   lambda u=url: H.web(u))
        if not isinstance(d, list) or not d:
            break
        for c in d:
            if c.get("mint"):
                out[c["mint"]] = c
        if len(d) < limit:
            break
        off += limit
        time.sleep(0.15)
    return out


def pump_coin(mint):
    url = "https://frontend-api-v3.pump.fun/coins/" + mint
    d = cached("pumpcoin_" + mint, lambda: H.web(url))
    return d if isinstance(d, dict) and d.get("mint") else None


def dexscreener_search(term):
    url = "https://api.dexscreener.com/latest/dex/search?q=" + urllib.parse.quote(term)
    d = cached("dex_%s" % term.replace(" ", "_"), lambda: H.web(url))
    return (d or {}).get("pairs") or []


def jup_search(term):
    url = "https://lite-api.jup.ag/tokens/v2/search?query=" + urllib.parse.quote(term)
    d = cached("jup_%s" % term.replace(" ", "_"), lambda: H.web(url))
    return d if isinstance(d, list) else []


def _slim(c):
    """The fields kept from a pump.fun token. The raw reply is not copied over:
    it carries image URLs and free-text descriptions.
    """
    ts = (c.get("created_timestamp") or 0) / 1000.0
    return {
        "mint": c.get("mint"),
        "symbole": c.get("symbol"),
        "nom": c.get("name"),
        "cree_ts": int(ts),
        "cree": utcday(ts) if ts else None,
        "createur": c.get("creator"),
        "ath_mc_usd": c.get("ath_market_cap"),
        "mc_usd_actuel": c.get("usd_market_cap"),
        "gradue": bool(c.get("complete")),
    }


def cmd_search():
    """(A) Enumerate the candidates for each symbol quoted, across all sources."""
    res = {"cibles": [], "familles_temoin": []}

    for cible in CIBLES:
        terme = cible["terme"]
        print("\n=== recherche << %s >> ===" % terme)
        pump = pump_search(terme)
        rows = [_slim(c) for c in pump.values()]
        rows = [r for r in rows if r["mint"]]
        rows.sort(key=lambda r: -(r["ath_mc_usd"] or 0))

        sym = (cible["symbole"] or "").lower()
        exacts = [r for r in rows
                  if sym and (r["symbole"] or "").lower() == sym]
        dans_fenetre = [r for r in rows
                        if REGIME1[0].timestamp() <= r["cree_ts"] < REGIME1[1].timestamp()]

        # Sources outside pump.fun: a 2024 token could have been launched
        # straight on Raydium, in which case it is in no pump API at all.
        dex = []
        for p in dexscreener_search(terme):
            if p.get("chainId") != "solana":
                continue
            bt = p.get("baseToken") or {}
            if terme.lower() not in ((bt.get("symbol") or "") + " " +
                                     (bt.get("name") or "")).lower():
                continue
            dex.append({
                "mint": bt.get("address"), "symbole": bt.get("symbol"),
                "nom": bt.get("name"), "dex": p.get("dexId"),
                "pool": p.get("pairAddress"),
                "pool_cree": utcday((p.get("pairCreatedAt") or 0) / 1000.0)
                             if p.get("pairCreatedAt") else None,
                "fdv_usd_actuel": p.get("fdv"),
                "liquidite_usd": (p.get("liquidity") or {}).get("usd"),
            })
        jup = [{"mint": t.get("id"), "symbole": t.get("symbol"),
                "nom": t.get("name"), "launchpad": t.get("launchpad"),
                "fdv_usd_actuel": t.get("fdv")}
               for t in jup_search(terme)]

        hors_pump = {}
        for r in dex + jup:
            if r.get("mint") and not r["mint"].endswith("pump"):
                hors_pump.setdefault(r["mint"], {}).update(r)

        atteint = [r for r in rows
                   if (r["ath_mc_usd"] or 0) >= 0.5 * cible["attendu_usd"]]
        top = rows[:15]
        print("  pump.fun : %d mints distincts ; symbole exact : %d ; "
              "crees dans la fenetre du regime 1 : %d"
              % (len(rows), len(exacts), len(dans_fenetre)))
        print("  ATH max observe : %s USD (cible du temoignage : %s USD)"
              % (round(top[0]["ath_mc_usd"] or 0) if top else None,
                 int(cible["attendu_usd"])))
        print("  candidats atteignant >= 50%% de la cible : %d" % len(atteint))
        print("  mints hors pump.fun trouves : %d" % len(hors_pump))

        res["cibles"].append({
            "terme": terme,
            "symbole_exact": cible["symbole"],
            "ath_annonce_usd": cible["attendu_usd"],
            "n_mints_pump": len(rows),
            "n_symbole_exact": len(exacts),
            "n_crees_fenetre_regime1": len(dans_fenetre),
            "n_atteignant_moitie_cible": len(atteint),
            "ath_max_observe_usd": (top[0]["ath_mc_usd"] if top else None),
            "top15_par_ath": top,
            "top_fenetre_regime1": sorted(
                dans_fenetre, key=lambda r: -(r["ath_mc_usd"] or 0))[:10],
            "hors_pump": list(hors_pump.values()),
            "tous_mints_pump": [r["mint"] for r in rows],
        })

    for f in FAMILLES_TEMOIN:
        pump = pump_search(f, max_pages=40)
        rows = sorted((_slim(c) for c in pump.values()),
                      key=lambda r: -(r["ath_mc_usd"] or 0))
        aths = [r["ath_mc_usd"] or 0 for r in rows]
        res["familles_temoin"].append({
            "terme": f, "n_mints_pump": len(rows),
            "ath_max_usd": max(aths) if aths else None,
            "ath_median_usd": statistics.median(aths) if aths else None,
            "part_gradues": (sum(1 for r in rows if r["gradue"]) / len(rows))
                            if rows else None,
        })
        print("temoin %-10s n=%-5d ath_max=%s" % (f, len(rows),
                                                  round(max(aths)) if aths else None))

    res["appels"] = {"web": H.n_web, "rpc": H.n_rpc}
    dump(res, "symboles.json")
    return res


# ============================================================== (B) ON-CHAIN =
def slot_for_ts(ts, tol=90):
    """The slot whose timestamp is within `tol` seconds of `ts`.

    A fixed-point iteration on getBlockTime: the slots-per-second rate is
    locally stable, so two to four iterations suffice. Skipped slots, where no
    block was produced, return None: step back one slot and try again.
    """
    def _f():
        s = int(ANCHOR_HI[0] + (ts - ANCHOR_HI[1]) * SLOTS_PER_SEC)
        for _ in range(60):
            bt, err = H.rpc("getBlockTime", [s])
            if err or bt is None:
                s -= 1
                continue
            d = ts - bt
            if abs(d) <= tol:
                return {"slot": s, "block_time": bt}
            s = int(s + d * SLOTS_PER_SEC)
        return {"slot": None, "block_time": None}
    return cached("slot_%d" % ts, _f)


def sig_at_ts(ts):
    """Any signature on the ledger near `ts`, usable as a `before` bound. It has
    no relation to the accounts being queried: it only positions the search in
    time.
    """
    def _f():
        sl = slot_for_ts(ts)
        s = sl["slot"]
        if s is None:
            return {"sig": None, "slot": None, "block_time": None}
        for _ in range(40):
            blk, err = H.rpc("getBlock", [s, {
                "transactionDetails": "signatures", "rewards": False,
                "maxSupportedTransactionVersion": 0}])
            if err or not blk or not blk.get("signatures"):
                s -= 1
                continue
            return {"sig": blk["signatures"][0], "slot": s,
                    "block_time": blk.get("blockTime")}
        return {"sig": None, "slot": None, "block_time": None}
    return cached("sigat_%d" % ts, _f)


def genese(addr, max_pages=400):
    """An account's oldest signature, which is its on-chain creation.

    Deep pagination is mandatory: a single page of 1000 signatures does not
    reach the genesis of an active account, and stopping there produces a false
    creation date, off by several months on the mints studied here.
    `n_pages_epuise` says whether the walk stopped for want of pages, in which
    case the date returned is an upper bound, not the genesis.
    """
    def _f():
        before, total, pages, old = None, 0, 0, None
        while pages < max_pages:
            page, err = H.sigs(addr, 1000, before)
            if err is not None:
                return {"erreur": err, "n_signatures_vues": total,
                        "n_pages": pages, "epuise": False,
                        "plus_ancienne": old}
            pages += 1
            if not page:
                break
            total += len(page)
            old = page[-1]
            before = old["signature"]
            if len(page) < 1000:
                break
        return {
            "erreur": None,
            "n_signatures_vues": total,
            "n_pages": pages,
            "epuise": pages < max_pages,
            "plus_ancienne": ({"signature": old["signature"], "slot": old["slot"],
                               "block_time": old.get("blockTime")} if old else None),
        }
    return cached("genese_" + addr, _f)


def tx(sig, parsed=True):
    def _f():
        r, err = H.rpc("getTransaction", [sig, {
            "encoding": "jsonParsed" if parsed else "json",
            "maxSupportedTransactionVersion": 0}])
        if err or not r:
            return {"_error": err or "vide"}
        return r
    return cached("tx_" + sig, _f)


def mint_de_creation(t):
    """The mint created by a pump.fun creation transaction.

    `meta.postTokenBalances` is read rather than the account keys: the mint's
    position in the account list changed between successive versions of the
    instruction, Create and CreateV2. Many 2024 mints do not end in "pump", so
    the suffix heuristic misses the oldest tokens, which are the ones of
    interest here.
    """
    for b in ((t.get("meta") or {}).get("postTokenBalances") or []):
        m = b.get("mint")
        if m and m != "So11111111111111111111111111111111111111112":
            return m
    return None


def cmd_onchain():
    """(B) The on-chain facts of the retained candidates."""
    src = json.load(open(os.path.join(OUT, "symboles.json")))
    cands = []
    for c in src["cibles"]:
        # The 3 best pump.fun highs plus every non-pump.fun mint found: those
        # are the only plausible candidates for a market cap of several tens of
        # millions.
        for r in c["top15_par_ath"][:3]:
            cands.append({"terme": c["terme"], "source": "pump.fun", **r})
        for r in c["hors_pump"]:
            cands.append({"terme": c["terme"], "source": "hors_pump", **r})

    out = []
    for r in cands:
        m = r.get("mint")
        if not m:
            continue
        print("  genese %s (%s)" % (m, r.get("symbole")))
        g = genese(m)
        pa = g.get("plus_ancienne") or {}
        bt = pa.get("block_time")
        rec = dict(r)
        rec.update({
            "genese_block_time": bt,
            "genese_date_utc": iso(bt) if bt else None,
            "genese_slot": pa.get("slot"),
            "genese_signature": pa.get("signature"),
            "genese_pagination_epuisee": g.get("epuise"),
            "n_signatures_mint": g.get("n_signatures_vues"),
            "erreur": g.get("erreur"),
        })
        if bt:
            rec["dans_fenetre_regime1"] = (
                REGIME1[0].timestamp() <= bt < REGIME1[1].timestamp())
        # What does the account's first transaction say?
        if pa.get("signature"):
            t = tx(pa["signature"])
            logs = [line for line in ((t.get("meta") or {}).get("logMessages") or [])
                    if "Instruction:" in line][:6]
            rec["genese_instructions"] = logs
        out.append(rec)
        time.sleep(0.1)

    dump({"candidats": out, "fenetre_regime1": [REGIME1[0].isoformat(),
                                                REGIME1[1].isoformat()]},
         "candidats_onchain.json")
    return out


# =========================================================== (C) CHRONOLOGIE =
def ancres_du_mois(y, m, n=6):
    """n instants spread through the month, away from its edges: an anchor on the
    1st at 00:00 would land in the tail of the previous month.
    """
    d0 = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    d1 = (dt.datetime(y + (m == 12), (m % 12) + 1, 1, tzinfo=dt.timezone.utc))
    t0, t1 = d0.timestamp(), d1.timestamp()
    span = t1 - t0
    return [int(t0 + span * (k + 0.5) / n) for k in range(n)], t0, t1


def mesure_ancre(ts, n_ech):
    """The instantaneous creation rate and a sample of mints, at instant `ts`.

    The rate is measured over 1000 consecutive creations: an exact count over a
    small window, not an estimate. The span those 1000 creations cover is
    returned (`fenetre_s`); once it exceeds a few hours, the rate is the day's
    rather than the instant's.
    """
    def _f():
        a = sig_at_ts(ts)
        if not a.get("sig"):
            return {"erreur": "pas de signature d'ancrage"}
        page, err = H.sigs(MINT_AUTHORITY, 1000, a["sig"])
        if err is not None:
            return {"erreur": err}
        page = [p for p in page if p.get("blockTime")]
        if len(page) < 50:
            return {"erreur": "page trop courte (%d)" % len(page),
                    "n": len(page)}
        span = page[0]["blockTime"] - page[-1]["blockTime"]
        return {
            "erreur": None,
            "ancre_ts": ts,
            "ancre_slot": a.get("slot"),
            "n_creations": len(page),
            "fenetre_s": span,
            "creations_par_s": (len(page) - 1) / span if span > 0 else None,
            "ts_min": page[-1]["blockTime"], "ts_max": page[0]["blockTime"],
            "echantillon": [page[i]["signature"] for i in
                            sorted({int(round(k * (len(page) - 1) / max(1, n_ech - 1)))
                                    for k in range(n_ech)})],
        }
    return cached("ancre_%d_%d" % (ts, n_ech), _f)


def cmd_chrono(debut="2024-01", fin=None, n_ancres=6, n_ech=18):
    """(C) Chronologie mensuelle : creations, graduations, distribution d'ATH."""
    now = dt.datetime.now(dt.timezone.utc)
    if fin is None:
        fin = now.strftime("%Y-%m")
    y0, m0 = (int(x) for x in debut.split("-"))
    y1, m1 = (int(x) for x in fin.split("-"))

    mois = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        mois.append((y, m))
        y, m = (y + (m == 12), (m % 12) + 1)

    lignes = []
    for (y, m) in mois:
        label = "%04d-%02d" % (y, m)
        ancres, t0, t1 = ancres_du_mois(y, m, n_ancres)
        ancres = [a for a in ancres if a < now.timestamp() - 3600]
        if not ancres:
            continue
        mes, sigs_ech = [], []
        for a in ancres:
            r = mesure_ancre(a, n_ech)
            if r.get("erreur"):
                print("    %s ancre %s : %s" % (label, utcday(a), r["erreur"]))
                continue
            mes.append(r)
            sigs_ech.extend(r["echantillon"])
        if not mes:
            print("  %s : aucune ancre exploitable" % label)
            continue

        taux = [r["creations_par_s"] for r in mes if r["creations_par_s"]]
        taux_med = statistics.median(taux)
        # part du mois reellement couverte (mois en cours = partiel)
        t1e = min(t1, now.timestamp())
        total_est = taux_med * (t1e - t0)

        # Sample of mints: resolve the signatures to mints, then query the
        # pump API for the high and for graduation.
        mints, echecs = [], 0
        for s in sigs_ech:
            t = tx(s)
            if t.get("_error"):
                echecs += 1
                continue
            mm = mint_de_creation(t)
            if mm:
                mints.append(mm)
            else:
                echecs += 1
        mints = sorted(set(mints))

        infos = []
        for mm in mints:
            c = pump_coin(mm)
            if c:
                infos.append(_slim(c))
            time.sleep(0.05)

        aths = sorted((i["ath_mc_usd"] or 0.0) for i in infos)
        n = len(infos)
        grad = sum(1 for i in infos if i["gradue"])

        def part(seuil):
            return (sum(1 for a in aths if a >= seuil) / n) if n else None

        ligne = {
            "mois": label,
            "n_ancres": len(mes),
            "creations_par_s_median": taux_med,
            "creations_par_s_min": min(taux), "creations_par_s_max": max(taux),
            "creations_par_jour_median": taux_med * 86400,
            "total_mois_estime": int(total_est),
            "mois_partiel": t1e < t1,
            "n_echantillon": n,
            "n_sig_non_resolues": echecs,
            "part_graduee": (grad / n) if n else None,
            "n_graduee": grad,
            "ath_median_usd": statistics.median(aths) if aths else None,
            "ath_p90_usd": aths[int(0.90 * (len(aths) - 1))] if aths else None,
            "ath_p99_usd": aths[int(0.99 * (len(aths) - 1))] if aths else None,
            "ath_max_usd": aths[-1] if aths else None,
            "part_ath_ge_100k": part(1e5),
            "part_ath_ge_500k": part(5e5),
            "part_ath_ge_1M": part(1e6),
            "mints_echantillon": mints,
        }
        lignes.append(ligne)
        print("  %s  taux=%8.2f/j  total_est=%9d  n=%3d  grad=%.1f%%  "
              "ATH_med=%8.0f  p99=%10.0f"
              % (label, ligne["creations_par_jour_median"],
                 ligne["total_mois_estime"], n,
                 100 * (ligne["part_graduee"] or 0),
                 ligne["ath_median_usd"] or 0, ligne["ath_p99_usd"] or 0))
        dump({"mois": lignes, "appels": {"rpc": H.n_rpc, "web": H.n_web}},
             "chronologie_mensuelle.json")

    return lignes


# ================================================================== rapport ==
def cmd_report():
    sym = json.load(open(os.path.join(OUT, "symboles.json")))
    try:
        onc = json.load(open(os.path.join(OUT, "candidats_onchain.json")))
    except Exception:                                    # noqa: BLE001
        onc = {"candidats": []}
    try:
        chr_ = json.load(open(os.path.join(OUT, "chronologie_mensuelle.json")))
    except Exception:                                    # noqa: BLE001
        chr_ = {"mois": []}

    verdicts = []
    for c in sym["cibles"]:
        atteint = c["n_atteignant_moitie_cible"] > 0
        verdicts.append({
            "terme": c["terme"],
            "ath_annonce_usd": c["ath_annonce_usd"],
            "n_mints_homonymes_pump": c["n_mints_pump"],
            "ath_max_verifiable_usd": c["ath_max_observe_usd"],
            "candidat_conforme_trouve": atteint,
            "conclusion": ("un candidat au moins atteint l'ordre de grandeur annonce"
                           if atteint else
                           "AUCUN mint homonyme verifiable n'approche l'ordre de "
                           "grandeur annonce ; le token cite reste NON IDENTIFIE"),
        })

    rep = {
        "objet": "ancrage du recit dans des tokens reels + chronologie du marche",
        "fenetre_regime1_temoignage": [REGIME1[0].isoformat(), REGIME1[1].isoformat()],
        "couverture_api": {
            "geckoterminal": "public : 180 jours maximum (verifie : HTTP 401 "
                             "explicite au-dela). INUTILISABLE pour 2024-2025.",
            "pump.fun": "recherche plein-texte et /coins/{mint} couvrent tout "
                        "l'historique du programme ; `ath_market_cap` disponible "
                        "meme sur un token mort. Ne couvre QUE les tokens pump.fun.",
            "dexscreener": "pools actuels, pas d'ATH historique.",
            "chaine (RPC)": "seule source integrale ; signatures et transactions "
                            "sont permanentes.",
        },
        "verdicts_symboles": verdicts,
        "candidats_onchain": onc.get("candidats", []),
        "chronologie": chr_.get("mois", []),
        "familles_temoin": sym.get("familles_temoin", []),
    }
    dump(rep, "ancrage.json")
    return rep


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    t0 = time.time()
    if cmd in ("search", "all"):
        cmd_search()
    if cmd in ("onchain", "all"):
        cmd_onchain()
    if cmd in ("chrono", "all"):
        cmd_chrono(*(sys.argv[2:4] or []))
    if cmd in ("report", "all"):
        cmd_report()
    print("\n%.0f s, %d appels RPC, %d appels web"
          % (time.time() - t0, H.n_rpc, H.n_web))


if __name__ == "__main__":
    main()
