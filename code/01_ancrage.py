#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_ancrage.py -- ancrage du recit dans des tokens REELS et chronologie du marche.

Ce script repond a trois questions, et a elles seules :

  (A) SYMBOLES CITES. Les tokens nommes dans le recit (EPEP, TEST, la famille
      << orbit >>) existent-ils ? Combien de mints DISTINCTS portent chacun de
      ces symboles ? Lequel, s'il y en a un, correspond a la capitalisation
      maximale annoncee ? La reponse est souvent << plusieurs dizaines de
      candidats, aucun ne correspond >> : c'est une MESURE, pas un echec, et
      c'est deja le materiau du chapitre sur les leurres.

  (B) FAITS ON-CHAIN. Pour chaque candidat retenu : date de creation lue sur la
      chaine (plus ancienne signature du compte de mint), programme d'origine,
      statut. La chaine est la seule source qui remonte a 2024 : verifie a la
      main que les API tierces ne couvrent pas cette periode (voir
      docs/ancrage_sources.md et le champ `couverture_api` du rapport).

  (C) CHRONOLOGIE MENSUELLE. Combien de tokens crees par mois, quelle part
      graduee, quelle distribution d'ATH -- de janvier 2024 a aujourd'hui.
      Objectif : situer les << epoques >> du recit sur une base chiffree.

METHODE DE LA CHRONOLOGIE (le point non evident)
------------------------------------------------
Aucune API publique ne rend le nombre de tokens crees un mois donne, et la
pagination par offset de l'API pump.fun ne permet pas de remonter a 2024
(il faudrait des millions de pages). On passe donc par la chaine.

Toute creation de token pump.fun signe une instruction ou intervient l'autorite
de mint du programme (PDA constant, cf. MINT_AUTHORITY). L'historique des
signatures de ce seul compte EST donc l'index exhaustif des creations, dans
l'ordre chronologique inverse. Deux consequences :

  * getSignaturesForAddress(MINT_AUTHORITY, before=S) rend les 1000 creations
    qui precedent immediatement la signature S. L'ecart de temps entre la
    premiere et la derniere de ces 1000 creations donne un TAUX DE CREATION
    instantane, mesure, sans echantillonnage biaise.
  * `before` accepte n'importe quelle signature du ledger, pas seulement une
    du compte interroge. On peut donc s'ancrer sur une DATE : on convertit la
    date en slot, on lit une signature quelconque de ce bloc, et on s'en sert
    d'ancre. C'est ce qui rend la mesure possible a n'importe quelle profondeur.

Le total mensuel est donc une ESTIMATION par integration de taux mesures a
N ancres reparties dans le mois, pas un comptage exhaustif ; l'incertitude est
rapportee (dispersion inter-ancres). Les tokens echantillonnes a ces memes
ancres sont, eux, un tirage sans biais de selection : on prend les creations
telles qu'elles se presentent dans l'index, jamais une liste << top >> d'une API.

NIVEAUX DE PREUVE
  [MESURE]  recalcule par ce script depuis la chaine ou une API publique.
  [ESTIME]  extrapolation explicite d'une mesure (totaux mensuels).
  [NON ETABLI] jamais chiffre comme un fait.

Usage :
    python3 code/01_ancrage.py search     # (A) symboles cites
    python3 code/01_ancrage.py onchain    # (B) faits on-chain des candidats
    python3 code/01_ancrage.py chrono     # (C) chronologie mensuelle
    python3 code/01_ancrage.py report     # assemble data/ancrage/ancrage.json
    python3 code/01_ancrage.py all

Aucune cle n'est ecrite sur disque ni dans les sorties (cf. settings.py).
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
# PDA autorite de mint du programme pump.fun. Present dans CHAQUE creation de
# token pump.fun et (verifie plus bas, cf. `verif_creations`) dans rien d'autre.
MINT_AUTHORITY = "TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Deux ancres slot/temps mesurees sur la chaine, servant d'amorce a la
# conversion date -> slot. Elles sont raffinees par getBlockTime a chaque appel :
# une derive de l'estimation initiale n'introduit aucune erreur, seulement des
# iterations supplementaires.
ANCHOR_HI = (435964490, 1785335387)
ANCHOR_LO = (306215569, 1733674757)
SLOTS_PER_SEC = (ANCHOR_HI[0] - ANCHOR_LO[0]) / (ANCHOR_HI[1] - ANCHOR_LO[1])

# Fenetre du << regime 1 >> telle que decrite par le temoignage, en UTC.
REGIME1 = (dt.datetime(2024, 10, 1, tzinfo=dt.timezone.utc),
           dt.datetime(2025, 3, 1, tzinfo=dt.timezone.utc))

# Symboles a ancrer. `attendu_usd` = capitalisation maximale annoncee par le
# temoignage ; sert UNIQUEMENT de cible a confronter, jamais de filtre.
CIBLES = [
    {"terme": "EPEP", "symbole": "EPEP", "attendu_usd": 40e6},
    {"terme": "TEST", "symbole": "TEST", "attendu_usd": 10e6},
    {"terme": "orbit", "symbole": None, "attendu_usd": 100e6},
]
# Familles temoins : des mots aussi banals que << orbit >>, tires d'un champ
# lexical sans rapport (objets, nature), pour disposer d'un taux de base du
# nombre de mints homonymes et de la forme de la distribution d'ATH.
FAMILLES_TEMOIN = ["lantern", "pebble", "marble", "willow", "compass"]


def utcday(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def utcmonth(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m")


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()


# ------------------------------------------------------------------ http ----
class Http:
    """Adaptateur mince. Le transport Solana JSON-RPC est delegue au client
    partage rpc_client (rotation de cles, cooldown apres 429, reprises bornees) ;
    on ne conserve ici que la traduction vers le contrat (resultat, erreur)
    attendu par les appelants, plus le petit GET web() vers les frontends
    pump/dexscreener/jup, qui ne sont PAS des endpoints Helius.

    Le comptage n'est pas cosmetique : le budget d'appels est rapporte dans la
    sortie pour que le cout de reproduction soit connu avant de relancer.
    """

    def __init__(self):
        self.n_rpc = 0
        self.n_web = 0

    # -- Solana JSON-RPC (transport delegue a rpc_client) -------------------
    def rpc(self, method, params):
        """Rend (resultat, erreur). L'erreur n'est JAMAIS confondue avec une
        reponse vide : c'est exactement le piege qui a fait croire, en cours de
        mise au point, que l'historique du mint EPEP s'arretait en 2024-12.
        rpc_client.rpc leve HeliusError sur un echec (transport ou objet `error`
        JSON-RPC) ; on le retraduit en tuple pour ne rien changer aux appelants."""
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

    # -- web (frontends pump/dexscreener/jup ; PAS un endpoint Helius) -------
    def web(self, url, tries=5, timeout=60):
        """Petit GET local. Retente 429/5xx et erreurs de transport ; rend
        {"_error": ...} sur un statut HTTP definitif non rejouable (ex. 404 =
        token absent : une reponse, pas une panne), mais LEVE quand les essais
        sont epuises -- une panne reseau ne doit pas se cacher en page vide."""
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
    """Cache disque des appels reseau (data/cache/, non publie : c'est un
    miroir exact de donnees publiques)."""
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
    """Tous les mints pump.fun dont le nom ou le symbole contient `term`.

    L'API pump.fun expose une recherche plein-texte paginee qui, elle, couvre
    TOUT l'historique du programme (verifie : des tokens de mars 2024
    remontent). C'est la seule source qui rende `ath_market_cap`, la
    capitalisation maximale atteinte, pour un token mort depuis longtemps.
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
    """Champs retenus d'un token pump.fun. On ne recopie pas la reponse brute :
    elle contient des URLs d'images et des descriptions libres."""
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
    """(A) Enumere les candidats pour chaque symbole cite, toutes sources."""
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

        # sources hors pump.fun : un token de 2024 pouvait etre lance
        # directement sur Raydium, auquel cas il n'est dans aucune API pump.
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
    """Slot dont l'horodatage est a moins de `tol` secondes de `ts`.

    Iteration point-fixe sur getBlockTime : le taux de slots par seconde est
    localement stable, deux a quatre iterations suffisent. Les slots sautes
    (pas de bloc produit) rendent None : on recule d'un slot et on recommence.
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
    """Une signature quelconque du ledger proche de `ts`, utilisable comme
    borne `before`. Elle n'a aucun rapport avec les comptes interroges : elle
    ne sert qu'a positionner la recherche dans le temps."""
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
    """Plus ancienne signature d'un compte = sa creation on-chain.

    Pagination profonde obligatoire : une seule page (1000 signatures) ne
    remonte PAS a la genese d'un compte actif, et s'arreter la produit une date
    de creation fausse -- de plusieurs mois sur les mints etudies ici.
    `n_pages_epuise` dit si la marche s'est arretee faute de pages, auquel cas
    la date rendue est une BORNE SUPERIEURE, pas la genese.
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
    """Mint cree par une transaction de creation pump.fun.

    On lit `meta.postTokenBalances`, et non les cles de compte : la position du
    mint dans la liste des comptes a change entre les versions successives de
    l'instruction (Create, CreateV2), et beaucoup de mints de 2024 ne se
    terminent pas par << pump >> -- l'heuristique du suffixe rate justement les
    tokens les plus anciens, ceux qui nous interessent.
    """
    for b in ((t.get("meta") or {}).get("postTokenBalances") or []):
        m = b.get("mint")
        if m and m != "So11111111111111111111111111111111111111112":
            return m
    return None


def cmd_onchain():
    """(B) Faits on-chain des candidats retenus."""
    src = json.load(open(os.path.join(OUT, "symboles.json")))
    cands = []
    for c in src["cibles"]:
        # 3 meilleurs ATH pump.fun + tous les mints hors pump.fun trouves :
        # ce sont les seuls candidats plausibles pour une capitalisation de
        # plusieurs dizaines de millions.
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
        # que dit le premier tx du compte ?
        if pa.get("signature"):
            t = tx(pa["signature"])
            logs = [l for l in ((t.get("meta") or {}).get("logMessages") or [])
                    if "Instruction:" in l][:6]
            rec["genese_instructions"] = logs
        out.append(rec)
        time.sleep(0.1)

    dump({"candidats": out, "fenetre_regime1": [REGIME1[0].isoformat(),
                                                REGIME1[1].isoformat()]},
         "candidats_onchain.json")
    return out


# =========================================================== (C) CHRONOLOGIE =
def ancres_du_mois(y, m, n=6):
    """n instants repartis dans le mois, a distance des bords (un ancrage le
    1er a 00:00 tomberait sur la queue du mois precedent)."""
    d0 = dt.datetime(y, m, 1, tzinfo=dt.timezone.utc)
    d1 = (dt.datetime(y + (m == 12), (m % 12) + 1, 1, tzinfo=dt.timezone.utc))
    t0, t1 = d0.timestamp(), d1.timestamp()
    span = t1 - t0
    return [int(t0 + span * (k + 0.5) / n) for k in range(n)], t0, t1


def mesure_ancre(ts, n_ech):
    """Taux de creation instantane + echantillon de mints, a l'instant `ts`.

    Le taux est mesure sur 1000 creations consecutives : c'est un comptage
    exact sur une petite fenetre, pas une estimation. La fenetre couverte par
    ces 1000 creations est rendue (`fenetre_s`) : quand elle depasse quelques
    heures, le taux est plutot celui de la journee que de l'instant.
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

        # echantillon de mints : resoudre les signatures -> mint, puis
        # interroger l'API pump pour ATH / graduation.
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
