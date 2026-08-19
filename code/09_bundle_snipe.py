#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La courbe est-elle rachetee des le slot de creation, et cela depend-il de la date ?

Pour un token pump.fun, on lit les premieres signatures de sa bonding curve, on
identifie le slot de creation et on somme le SOL qui y entre : sol_first_slot (pendant
le slot de creation), sol_window_30s (dans les 30 s suivant la 1re transaction),
n_buyers_* (portefeuilles distincts a l'origine de ce SOL). La courbe se remplit avec
~85 SOL avant de migrer ; a partir de FULL_SNIPE_SOL (60 SOL des le slot de creation)
elle est deja prise au moment ou la creation devient visible. Seuil en SOL et non en
dollars, pour rester comparable entre epoques.

<< La Matrice >> designe les flottes de portefeuilles partageant une origine de
financement, une methode d'execution et des circuits de sortie : une infrastructure
observee, pas une personne ni une organisation identifiee. Plusieurs operateurs
distincts appliquent la meme methode ; savoir s'ils partagent un controle unique
depasse ce que la chaine permet d'etablir.

Trois echantillons aux biais differents, tenus separes :
  L  legacy, n=70, ATH >= 500 k$, crees du 2026-06-27 au 2026-07-04 ; corpus local du
     collecteur, selection non aleatoire (ordre du fichier source).
  F  cadre stratifie par mois de creation dans le classement all-time de l'API pump
     (sort=ath_market_cap) ; utilisable de 2025-05 a 2026-07, avant quoi le champ
     ath_market_cap n'existe pas (plus ancien ath_market_cap_timestamp : mai 2025).
  C  serie de cas : les 46 tokens du meme classement crees avant 2025-05. Leur ATH
     d'API est un pic de 2025-2026, pas leur pic de lancement ; ils figurent au
     classement parce qu'ils ont survecu. Serie de cas, donc, et pas un taux.

Limites : le script ne dit pas qui achete, ni si les acheteurs d'un meme slot relevent
du meme operateur (chapitres 3 et 6) ; un rachat au slot 0 n'est pas en soi une
infraction, seulement une mesure de ce qui reste achetable par un tiers ; aucune des
trois populations n'est un tirage aleatoire dans les tokens >= 500 k$, donc les taux se
comparent entre mois d'un meme echantillon et pas d'un echantillon a l'autre.

Usage:
    python3 code/09_bundle_snipe.py                 # rapport, hors ligne
    python3 code/09_bundle_snipe.py --frame         # (re)telecharge le cadre
    python3 code/09_bundle_snipe.py --measure       # mesure on-chain (Helius)
    python3 code/09_bundle_snipe.py --measure --per-month 12 --workers 10

Mesure on-chain mise en cache token par token dans data/bundle/cache/ : une re-execution
ne redemande que ce qui manque. Les fichiers publies dans data/bundle/ suffisent a
refaire tous les chiffres du rapport sans reseau.
"""

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import random
import statistics as st
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import settings  # noqa: E402
import rpc_client  # noqa: E402

OUTDIR = settings.data("bundle")
CACHEDIR = os.path.join(OUTDIR, "cache")
FRAME = os.path.join(OUTDIR, "frame_ath.json")
LEGACY = os.path.join(OUTDIR, "legacy_70.json")
MEASURES = os.path.join(OUTDIR, "measures.json")
REPORT = os.path.join(OUTDIR, "09_bundle_snipe.json")

# --- definition de la mesure (identique a la mesure gelee du 2026-07-29) -----
SNIPE_WINDOW = 30        # s apres la 1re transaction de la courbe
FULL_SNIPE_SOL = 60.0    # seuil << courbe rachetee >> (la courbe entiere ~85 SOL)
MAX_TX_PARSED = 60       # nb max de transactions decodees par token
MAX_SIG_PAGES = 80       # profondeur de pagination (1000 signatures / page)
CREATED_TOL = 300        # s : ecart tolere entre pump.created et la 1re signature

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Comptes qui ne sont jamais un acheteur humain (programmes, vaults de pourboire).
NON_PARTICIPANT = {
    "11111111111111111111111111111111",
    "ComputeBudget111111111111111111111111111111",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
    PUMP_PROGRAM,
}


# --------------------------------------------------------------------------- #
# base58 + PDA (pur stdlib) : permet de verifier que l'adresse de courbe
# fournie par l'API pump est bien PDA(["bonding-curve", mint], programme pump).
# --------------------------------------------------------------------------- #
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + raw


def b58encode(b):
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\x00"))) + out


_P = 2 ** 255 - 19
_D = (-121665 * pow(121666, _P - 2, _P)) % _P


def _on_curve(b):
    """True si les 32 octets encodent un point ed25519 valide (donc pas une PDA)."""
    y = int.from_bytes(b, "little") & ((1 << 255) - 1)
    if y >= _P:
        return False
    y2 = (y * y) % _P
    u, v = (y2 - 1) % _P, (_D * y2 + 1) % _P
    x2 = (u * pow(v, _P - 2, _P)) % _P
    if x2 == 0:
        return True
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = (x * pow(2, (_P - 1) // 4, _P)) % _P
    return (x * x - x2) % _P == 0


def bonding_curve_pda(mint):
    seeds = b"bonding-curve" + b58decode(mint)
    prog = b58decode(PUMP_PROGRAM)
    for bump in range(255, -1, -1):
        h = hashlib.sha256(seeds + bytes([bump]) + prog + b"ProgramDerivedAddress").digest()
        if not _on_curve(h):
            return b58encode(h)
    raise ValueError("no PDA")


# --------------------------------------------------------------------------- #
# client Helius : stdlib, rotation des cles, backoff sur 429/5xx
# --------------------------------------------------------------------------- #
class Rpc:
    def __init__(self, rps=12.0):
        self.keys = settings.require_helius()
        self.lock = threading.Lock()
        self.i = 0
        self.min_gap = 1.0 / rps
        self.last = 0.0
        self.n_calls = 0

    def _throttle(self):
        """Espacement local entre appels (rate-limit par instance) + compteur
        d'appels pour l'affichage de progression. Le transport lui-meme (envoi,
        rotation des cles, cooldown 429, reprises 5xx) appartient a rpc_client."""
        with self.lock:
            gap = self.min_gap - (time.time() - self.last)
            if gap > 0:
                time.sleep(gap)
            self.last = time.time()
            self.n_calls += 1

    def call(self, method, params, tries=7):
        # Transport delegue a rpc_client : il possede la rotation des cles, le
        # cooldown apres un 429 et les reprises bornees, et il leve HeliusError
        # plutot que de rendre un None/[]/{} confondable avec un vide. On ne garde
        # ici que le petit espacement local entre appels. tries reste dans la
        # signature pour ne pas toucher aux appelants, mais n'est plus utilise.
        self._throttle()
        return rpc_client.rpc(method, params)

    def sigs(self, addr, before=None):
        # rpc_client.sigs leve si le RPC renvoie null (un null est une panne, pas
        # une page vide) ; une page reellement vide reste []. Plus de "or []" qui
        # transformait une panne de quota en "courbe sans transaction".
        self._throttle()
        return rpc_client.sigs(addr, 1000, before)

    def tx(self, sig):
        self._throttle()
        return rpc_client.tx(sig)


# --------------------------------------------------------------------------- #
# decodage d'une transaction : qui envoie du SOL DANS la courbe
# --------------------------------------------------------------------------- #
def _keys(tx):
    out = []
    msg = (tx.get("transaction") or {}).get("message") or {}
    for k in msg.get("accountKeys") or []:
        out.append(k["pubkey"] if isinstance(k, dict) else k)
    la = (tx.get("meta") or {}).get("loadedAddresses") or {}
    return out + (la.get("writable") or []) + (la.get("readonly") or [])


def _instructions(tx):
    msg = (tx.get("transaction") or {}).get("message") or {}
    for ix in msg.get("instructions") or []:
        yield ix
    for inner in (tx.get("meta") or {}).get("innerInstructions") or []:
        for ix in inner.get("instructions") or []:
            yield ix


def buyers_of_tx(tx, bc):
    """{portefeuille: lamports} pour tout SOL entrant dans la bonding curve.

    On somme les transferts System vers la courbe plutot que de retenir le seul
    signataire : un bundle pump.fun est frequemment une seule transaction
    co-signee par plusieurs portefeuilles, qui payent chacun leur part.
    """
    out = {}
    for ix in _instructions(tx):
        if ix.get("program") != "system":
            continue
        p = ix.get("parsed") or {}
        info = p.get("info") or {}
        if p.get("type") in ("transfer", "transferWithSeed"):
            src, dst, lp = info.get("source"), info.get("destination"), info.get("lamports")
        elif p.get("type") in ("createAccount", "createAccountWithSeed"):
            src, dst, lp = info.get("source"), info.get("newAccount"), info.get("lamports")
        else:
            continue
        try:
            lp = int(lp or 0)
        except (TypeError, ValueError):
            continue
        if dst == bc and src and src != bc and lp > 0 and src not in NON_PARTICIPANT:
            out[src] = out.get(src, 0) + lp
    return out


# --------------------------------------------------------------------------- #
# mesure d'un token
# --------------------------------------------------------------------------- #
def oldest_sigs(rpc, addr, stop_ts):
    """Pagine vers le passe jusqu'a depasser stop_ts. Retourne (sigs_asc, complet).

    Piege : sur une courbe tres active, une pagination bornee a deux pages ne lit
    que des transactions recentes et conclut a tort a l'absence d'achat initial.
    On ne s'arrete donc qu'une fois la creation atteinte.
    """
    out, before, complete = [], None, False
    for _ in range(MAX_SIG_PAGES):
        page = rpc.sigs(addr, before=before)
        if not page:
            complete = True
            break
        out.extend(page)
        ts = [s.get("blockTime") for s in page if s.get("blockTime")]
        if len(page) < 1000:
            complete = True
            break
        if stop_ts and ts and min(ts) <= stop_ts:
            complete = True
            break
        before = page[-1]["signature"]
    return sorted(out, key=lambda s: (s.get("blockTime") or 0, s.get("slot") or 0)), complete


def measure(rpc, rec):
    """rec = {mint, bonding_curve, created} -> dict de mesure."""
    mint = rec["mint"]
    bc = rec.get("bonding_curve") or bonding_curve_pda(mint)
    created = rec.get("created")
    sigs, complete = oldest_sigs(rpc, bc, (created - 60) if created else None)
    base = {"mint": mint, "created": created, "sample": rec.get("sample"),
            "month": rec.get("month"), "ath_api": rec.get("ath_api"),
            "n_sigs_total": len(sigs), "pagination_complete": complete}
    if not sigs:
        return {**base, "status": "no_sigs"}
    t0 = sigs[0].get("blockTime")
    slot0 = sigs[0].get("slot")
    if not t0:
        return {**base, "status": "no_blocktime"}
    if not complete:
        # on n'a pas atteint la genese : la 1re signature lue n'est pas la creation
        return {**base, "status": "pagination_incomplete"}
    base["dt_created"] = (t0 - created) if created else None
    window = [s for s in sigs if (s.get("blockTime") or 0) <= t0 + SNIPE_WINDOW]
    # on decode d'abord toutes les signatures du slot de creation, puis on
    # complete avec le reste de la fenetre : le chiffre << slot 0 >> ne peut
    # donc pas etre tronque par la borne de cout.
    in_slot0 = [s for s in window if s.get("slot") == slot0]
    rest = [s for s in window if s.get("slot") != slot0]
    todo = (in_slot0 + rest)[:MAX_TX_PARSED]
    b_slot0, b_win, n_parsed = {}, {}, 0
    for s in todo:
        tx = rpc.tx(s["signature"])
        if not tx:
            continue
        n_parsed += 1
        for w, lam in buyers_of_tx(tx, bc).items():
            b_win[w] = b_win.get(w, 0.0) + lam / 1e9
            if tx.get("slot") == slot0:
                b_slot0[w] = b_slot0.get(w, 0.0) + lam / 1e9
    sol_win = sum(b_win.values())
    sol_0 = sum(b_slot0.values())
    return {**base, "status": "ok",
            "slot0": slot0,
            "n_sigs_window": len(window), "n_sigs_slot0": len(in_slot0),
            "n_tx_parsed": n_parsed,
            "n_buyers_window": len(b_win), "n_buyers_slot0": len(b_slot0),
            "sol_window_30s": round(sol_win, 3), "sol_first_slot": round(sol_0, 3),
            "top_buyer_sol": round(max(b_win.values()), 3) if b_win else 0.0,
            "full_snipe": sol_win >= FULL_SNIPE_SOL,
            "snipe_in_first_slot": sol_0 >= FULL_SNIPE_SOL}


# --------------------------------------------------------------------------- #
# cadre d'echantillonnage
# --------------------------------------------------------------------------- #
def http_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def build_frame():
    """Classement all-time de l'API pump, pagine jusqu'a epuisement (~1050).

    C'est le seul point d'entree gratuit qui remonte au-dela de quelques
    dizaines de minutes : le listing par date de creation est plafonne a
    offset ~1000, soit environ 30 minutes de passe.
    """
    base = ("https://frontend-api-v3.pump.fun/coins"
            "?sort=ath_market_cap&order=DESC&limit=50&offset=%d")
    seen, rows = set(), []
    for off in range(0, 4000, 50):
        try:
            d = http_json(base % off)
        except Exception as e:
            print("  arret offset=%d : %s" % (off, e))
            break
        if not d:
            break
        for c in d:
            if c["mint"] in seen:
                continue
            seen.add(c["mint"])
            rows.append({
                "mint": c["mint"],
                "bonding_curve": c.get("bonding_curve"),
                "created": int(c["created_timestamp"] / 1000),
                "ath_api": c.get("ath_market_cap"),
                "ath_api_ts": int((c.get("ath_market_cap_timestamp") or 0) / 1000) or None,
                "complete": c.get("complete"),
            })
        time.sleep(0.3)
    rows.sort(key=lambda r: r["created"])
    doc = {"niveau": "MESURE",
           "source": "frontend-api-v3.pump.fun/coins?sort=ath_market_cap&order=DESC",
           "gele_le": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
           "n": len(rows), "tokens": rows}
    os.makedirs(OUTDIR, exist_ok=True)
    json.dump(doc, open(FRAME, "w"), indent=1)
    print("cadre : %d tokens -> %s" % (len(rows), os.path.relpath(FRAME, settings.ROOT)))
    return doc


def month_of(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m")


# 2025-05 = premier mois ou le champ ath_market_cap de l'API existe : avant, un
# token ne figure au classement que s'il a connu un pic bien apres son
# lancement, ce qui est une selection par la survie.
FRAME_START = "2025-05"


def select_targets(per_month, seed=20260729):
    """Cibles = serie de cas (avant FRAME_START) + tirage par mois ensuite."""
    doc = json.load(open(FRAME))
    by = defaultdict(list)
    for r in doc["tokens"]:
        by[month_of(r["created"])].append(r)
    out = []
    for m in sorted(by):
        rows = sorted(by[m], key=lambda r: r["mint"])
        if m < FRAME_START:
            for r in rows:                       # serie de cas : tout est pris
                out.append({**r, "month": m, "sample": "C_serie_cas"})
        else:
            rnd = random.Random("%s|%d" % (m, seed))
            pick = rows if len(rows) <= per_month else rnd.sample(rows, per_month)
            for r in sorted(pick, key=lambda r: r["mint"]):
                out.append({**r, "month": m, "sample": "F_cadre"})
    return out


def load_legacy():
    """Les 70 tokens ATH >= 500 k$ deja mesures (re-mesures ici au meme protocole).

    Lus depuis data/bundle/legacy_70.json (publie). Le fichier est reconstruit
    depuis l'etat brut du collecteur si $PUMP_PRIVATE_ROOT est defini.
    """
    if not os.path.exists(LEGACY):
        priv = settings.private_root(required=True)
        d = os.path.join(priv, "analysis_supervision")
        rows = {r["mint"]: r for r in json.load(open(os.path.join(d, "gros_tokens_signature.json")))}
        for r in json.load(open(os.path.join(d, "gros_tokens_deep.json"))):
            rows[r["mint"]] = r
        out = [{"mint": r["mint"], "created": int(r["created"]) if r.get("created") else None,
                "ath_usd": round(r["ath"], 2),
                "gele_sol_first_slot": r.get("sol_first_slot"),
                "gele_sol_window_30s": r.get("sol_window"),
                "gele_n_buyers": r.get("n_buyers"),
                "gele_snipe_in_first_slot": r.get("snipe_in_first_slot"),
                "gele_status": r.get("status")}
               for r in sorted(rows.values(), key=lambda x: x.get("created") or 0)]
        json.dump({"niveau": "MESURE", "gele_le": "2026-07-29",
                   "source": "pump_bundle_detector/analysis_supervision/"
                             "{gros_tokens_signature,gros_tokens_deep}.json",
                   "n": len(out), "tokens": out}, open(LEGACY, "w"), indent=1)
    return json.load(open(LEGACY))["tokens"]


# --------------------------------------------------------------------------- #
# collecte
# --------------------------------------------------------------------------- #
def cache_path(mint):
    return os.path.join(CACHEDIR, mint + ".json")


def run_measure(per_month, workers, only=None):
    os.makedirs(CACHEDIR, exist_ok=True)
    targets = select_targets(per_month)
    for r in load_legacy():
        targets.append({"mint": r["mint"], "bonding_curve": None,
                        "created": r["created"], "ath_api": r.get("ath_usd"),
                        "month": month_of(r["created"]) if r.get("created") else None,
                        "sample": "L_legacy_500k"})
    if only:
        targets = [t for t in targets if t["sample"] == only]
    todo = [t for t in targets if not os.path.exists(cache_path(t["mint"]))]
    print("cibles=%d  deja en cache=%d  a mesurer=%d"
          % (len(targets), len(targets) - len(todo), len(todo)))
    if not todo:
        return
    rpc = Rpc()
    done = [0]
    lock = threading.Lock()

    def one(t):
        try:
            m = measure(rpc, t)
        except Exception as e:
            m = {"mint": t["mint"], "created": t.get("created"), "month": t.get("month"),
                 "sample": t.get("sample"), "ath_api": t.get("ath_api"),
                 "status": "err:" + settings.redact_key(str(e))[:90]}
        json.dump(m, open(cache_path(t["mint"]), "w"), indent=1)
        with lock:
            done[0] += 1
            if done[0] % 10 == 0 or done[0] == len(todo):
                print("  %d/%d  (%d appels RPC)" % (done[0], len(todo), rpc.n_calls),
                      flush=True)
        return m

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, todo))
    collect(targets)


def collect(targets=None):
    """Rassemble le cache token par token dans data/bundle/measures.json."""
    if targets is None:
        targets = select_targets(12)
        for r in load_legacy():
            targets.append({"mint": r["mint"], "created": r["created"],
                            "ath_api": r.get("ath_usd"), "sample": "L_legacy_500k",
                            "month": month_of(r["created"]) if r.get("created") else None})
    rows = []
    for t in targets:
        p = cache_path(t["mint"])
        if os.path.exists(p):
            rows.append(json.load(open(p)))
    rows.sort(key=lambda r: (r.get("sample") or "", r.get("created") or 0))
    json.dump({"niveau": "MESURE",
               "definition": {
                   "fenetre_s": SNIPE_WINDOW, "seuil_SOL": FULL_SNIPE_SOL,
                   "max_tx_decodees": MAX_TX_PARSED,
                   "snipe_in_first_slot": "SOL entre dans la courbe pendant le "
                                          "slot de creation >= seuil",
                   "mesurable": "pagination remontee jusqu'a la creation, 1re "
                                "signature a moins de %d s du created de l'API, "
                                "et au moins un versement decode" % CREATED_TOL},
               "n": len(rows), "tokens": rows}, open(MEASURES, "w"), indent=1)
    print("mesures : %d -> %s" % (len(rows), os.path.relpath(MEASURES, settings.ROOT)))
    return rows


# --------------------------------------------------------------------------- #
# agregation
# --------------------------------------------------------------------------- #
def wilson(k, n, z=1.96):
    """Wilson 95 % interval as a rounded percentage. The interval itself is the
    single definition in statlib.wilson; this only scales it to percent and
    rounds for the table."""
    from statlib import wilson as _wilson_frac
    lo, hi = _wilson_frac(k, n, z)
    if lo is None:
        return (None, None)
    return (round(100 * lo, 1), round(100 * hi, 1))


def fisher(a, b, c, d):
    """p bilaterale du test exact de Fisher sur [[a,b],[c,d]] (stdlib)."""
    from math import comb
    n = a + b + c + d
    r1, c1 = a + b, a + c
    def pr(x):
        return comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)
    p0 = pr(a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return round(sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 * 1.000001), 5)


def measurable(r):
    if r.get("status") != "ok":
        return False
    if r.get("dt_created") is not None and abs(r["dt_created"]) > CREATED_TOL:
        return False
    return (r.get("sol_window_30s") or 0) > 0


def stats(rows):
    m = [r for r in rows if measurable(r)]
    if not m:
        return {"n_cibles": len(rows), "n_mesurables": 0}
    k = sum(1 for r in m if r["snipe_in_first_slot"])
    lo, hi = wilson(k, len(m))
    return {
        "n_cibles": len(rows), "n_mesurables": len(m),
        "n_slot0": k, "pct_slot0": round(100 * k / len(m), 1), "ic95": [lo, hi],
        "med_sol_first_slot": round(st.median([r["sol_first_slot"] for r in m]), 1),
        "med_sol_window_30s": round(st.median([r["sol_window_30s"] for r in m]), 1),
        "med_n_buyers_slot0": st.median([r["n_buyers_slot0"] for r in m]),
        "med_n_buyers_window": st.median([r["n_buyers_window"] for r in m]),
        "rejets": dict(Counter(r.get("status", "?") if r.get("status") != "ok"
                               else "ok_non_mesurable"
                               for r in rows if not measurable(r))),
    }


def report():
    doc = json.load(open(MEASURES))
    rows = doc["tokens"]
    by_sample = defaultdict(list)
    for r in rows:
        by_sample[r.get("sample") or "?"].append(r)

    out = {"niveau": "MESURE",
           "genere_le": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
           "definition": doc["definition"],
           "echantillons": {}, "par_mois_cadre": {}, "serie_de_cas": [],
           "tests": {}}

    print("=" * 78)
    print("CH.9 -- LA COURBE EST-ELLE RACHETEE DANS LE SLOT DE CREATION ?")
    print("=" * 78)
    for s in sorted(by_sample):
        d = stats(by_sample[s])
        out["echantillons"][s] = d
        if d.get("n_mesurables"):
            print("\n[%s]  n_cibles=%d  n_mesurables=%d" % (s, d["n_cibles"], d["n_mesurables"]))
            print("  rachetee au SLOT DE CREATION : %d/%d = %.1f %%  IC95 [%s ; %s]"
                  % (d["n_slot0"], d["n_mesurables"], d["pct_slot0"], *d["ic95"]))
            print("  SOL median au slot 0 : %.1f   |  30 s : %.1f"
                  % (d["med_sol_first_slot"], d["med_sol_window_30s"]))
            print("  acheteurs distincts medians : slot 0 = %g   |  30 s = %g"
                  % (d["med_n_buyers_slot0"], d["med_n_buyers_window"]))
            if d["rejets"]:
                print("  non mesurables : %s" % d["rejets"])
        else:
            print("\n[%s]  n_cibles=%d  AUCUN mesurable  %s"
                  % (s, d["n_cibles"], d.get("rejets", "")))

    # ---- taux par mois de creation, sur le cadre F uniquement ----
    frame = [r for r in rows if r.get("sample") == "F_cadre"]
    bym = defaultdict(list)
    for r in frame:
        bym[r.get("month")].append(r)
    print("\n" + "-" * 78)
    print("TAUX PAR MOIS DE CREATION -- cadre F (selection identique tous les mois)")
    print("-" * 78)
    print("%-9s %5s %5s %7s %-16s %7s %7s" %
          ("mois", "cibl", "mesu", "slot0", "IC95", "SOLmed", "acht0"))
    for m in sorted(bym):
        d = stats(bym[m])
        out["par_mois_cadre"][m] = d
        if d.get("n_mesurables"):
            print("%-9s %5d %5d %6.0f%% [%5s ; %5s]  %7.1f %7g"
                  % (m, d["n_cibles"], d["n_mesurables"], d["pct_slot0"],
                     d["ic95"][0], d["ic95"][1], d["med_sol_first_slot"],
                     d["med_n_buyers_slot0"]))
        else:
            print("%-9s %5d %5d       -" % (m, d["n_cibles"], d["n_mesurables"]))

    # ---- meme chose regroupee par trimestre (n par cellule plus utile) ----
    def quarter(m):
        y, mo = m.split("-")
        return "%s-T%d" % (y, (int(mo) - 1) // 3 + 1)

    byq = defaultdict(list)
    for r in frame:
        byq[quarter(r["month"])].append(r)
    out["par_trimestre_cadre"] = {}
    print("\nregroupe par trimestre :")
    for q in sorted(byq):
        d = stats(byq[q])
        out["par_trimestre_cadre"][q] = d
        if d.get("n_mesurables"):
            print("  %-8s %2d/%2d = %5.1f %%  IC95 [%s ; %s]   acheteurs slot0 med=%g"
                  % (q, d["n_slot0"], d["n_mesurables"], d["pct_slot0"],
                     d["ic95"][0], d["ic95"][1], d["med_n_buyers_slot0"]))

    # ---- premier vs dernier semestre du cadre : y a-t-il une tendance ? ----
    qs = sorted(k for k, v in out["par_trimestre_cadre"].items() if v.get("n_mesurables"))
    if len(qs) >= 2:
        first = [r for r in frame if quarter(r["month"]) in qs[:len(qs) // 2] and measurable(r)]
        last = [r for r in frame if quarter(r["month"]) in qs[len(qs) // 2:] and measurable(r)]
        a = sum(1 for r in first if r["snipe_in_first_slot"])
        c = sum(1 for r in last if r["snipe_in_first_slot"])
        p = fisher(a, len(first) - a, c, len(last) - c)
        out["tests"]["debut_vs_fin_cadre"] = {
            "trimestres_debut": qs[:len(qs) // 2], "trimestres_fin": qs[len(qs) // 2:],
            "debut": [a, len(first)], "fin": [c, len(last)], "fisher_p": p}
        print("\nTest debut (%s) vs fin (%s) du cadre : %d/%d contre %d/%d, "
              "Fisher exact p = %.4f"
              % (",".join(qs[:len(qs) // 2]), ",".join(qs[len(qs) // 2:]),
                 a, len(first), c, len(last), p))

    # ---- serie de cas : tokens crees avant l'existence du champ ATH ----
    cas = sorted([r for r in rows if r.get("sample") == "C_serie_cas"],
                 key=lambda r: r.get("created") or 0)
    print("\n" + "-" * 78)
    print("SERIE DE CAS -- tokens crees avant %s (selection PAR LA SURVIE, pas un taux)"
          % FRAME_START)
    print("-" * 78)
    print("%-10s %-46s %8s %8s %6s %6s" %
          ("cree", "mint", "SOLslot0", "SOL30s", "ach0", "ach30"))
    for r in cas:
        if not measurable(r):
            out["serie_de_cas"].append({"mint": r["mint"], "status": r.get("status"),
                                        "mesurable": False})
            continue
        d = dt.datetime.fromtimestamp(r["created"], dt.timezone.utc).strftime("%Y-%m-%d")
        print("%-10s %-46s %8.1f %8.1f %6d %6d"
              % (d, r["mint"], r["sol_first_slot"], r["sol_window_30s"],
                 r["n_buyers_slot0"], r["n_buyers_window"]))
        out["serie_de_cas"].append({
            "mint": r["mint"], "cree": d, "mesurable": True,
            "sol_first_slot": r["sol_first_slot"], "sol_window_30s": r["sol_window_30s"],
            "n_buyers_slot0": r["n_buyers_slot0"], "n_buyers_window": r["n_buyers_window"],
            "snipe_in_first_slot": r["snipe_in_first_slot"]})
    dcas = stats(cas)
    out["echantillons"]["C_serie_cas"] = dcas
    if dcas.get("n_mesurables"):
        print("  -> %d/%d de ces cas portent la signature slot 0 (%.0f %%). "
              "n petit, selection non aleatoire : a lire comme des cas, pas comme un taux."
              % (dcas["n_slot0"], dcas["n_mesurables"], dcas["pct_slot0"]))

    # ---- reproduction du chiffre gele ----
    leg = json.load(open(LEGACY))["tokens"]
    g = [r for r in leg if (r.get("gele_sol_window_30s") or 0) > 0]
    gk = sum(1 for r in g if r.get("gele_snipe_in_first_slot"))
    out["reproduction_mesure_gelee"] = {
        "n_total": len(leg), "n_mesurables": len(g), "n_slot0": gk,
        "pct": round(100 * gk / len(g), 1) if g else None,
        "ic95": wilson(gk, len(g)),
        "med_sol_first_slot": round(st.median([r["gele_sol_first_slot"] for r in g]), 1),
        "med_n_buyers": st.median([r["gele_n_buyers"] for r in g]),
        "note": "recompte a l'identique sur la mesure du 2026-07-29 ; les 4 tokens "
                "ecartes sont des ECHECS DE MESURE (aucun versement decode), pas "
                "des absences de signature."}
    print("\n" + "-" * 78)
    print("REPRODUCTION DU CHIFFRE GELE (mesure du 2026-07-29, ATH >= 500 k$)")
    print("-" * 78)
    print("  %d/%d mesurables = %.1f %%  IC95 [%s ; %s]  |  SOL slot0 median %.1f  "
          "|  acheteurs medians %g"
          % (gk, len(g), out["reproduction_mesure_gelee"]["pct"],
             *out["reproduction_mesure_gelee"]["ic95"],
             out["reproduction_mesure_gelee"]["med_sol_first_slot"],
             out["reproduction_mesure_gelee"]["med_n_buyers"]))

    json.dump(out, open(REPORT, "w"), indent=1)
    print("\n-> %s" % os.path.relpath(REPORT, settings.ROOT))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--frame", action="store_true", help="(re)telecharge le cadre pump")
    ap.add_argument("--measure", action="store_true", help="mesure on-chain (Helius)")
    ap.add_argument("--collect", action="store_true", help="regroupe le cache")
    ap.add_argument("--per-month", type=int, default=12)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--only", default=None, help="F_cadre | C_serie_cas | L_legacy_500k")
    a = ap.parse_args()
    if a.frame:
        build_frame()
    if a.measure:
        run_measure(a.per_month, a.workers, a.only)
    if a.collect:
        collect()
    if not (a.frame or a.measure or a.collect) or os.path.exists(MEASURES):
        if os.path.exists(MEASURES):
            report()


if __name__ == "__main__":
    main()
