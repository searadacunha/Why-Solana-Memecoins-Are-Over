#!/usr/bin/env python3
"""Etape 2 : comment chaque premier acheteur a-t-il ete finance, et par qui.

Lit e1_buyers_<label>.json, ecrit e2_funding_<label>.json et met la pagination en cache dans
cache_sigs/.

Deux mesures distinctes, qui ne portent pas sur la meme chose :
M1, financement de naissance. Les premieres transactions de la vie du portefeuille. C'est la mesure
    du cas ODIN, quatre portefeuilles nes dans la meme transaction, cinq jours avant le token. Elle
    n'a de sens que si la genese est atteinte.
M2, financement pre-achat. Les entrees de fonds dans la fenetre qui precede immediatement le
    premier achat (par defaut 21 jours). Un portefeuille ancien et tres actif peut avoir ete
    re-approvisionne juste avant l'operation sans etre « ne » pour elle. Cette mesure reste
    accessible meme quand la genese est hors de portee, tant que la pagination atteint la fenetre.

Piege nº1 : `getSignaturesForAddress` ne remonte que du present vers le passe, donc les
portefeuilles les plus actifs sont les plus difficiles a remonter et le biais va contre les bots de
sniping. Trois drapeaux sont rendus par portefeuille : `genesis_reached`, `prebuy_window_reached`,
`pages_paginated`. Un « aucun financement trouve » sur un portefeuille dont la fenetre n'est pas
atteinte est un echec de mesure, jamais un resultat negatif.

Piege nº2 : un financement livre par fermeture d'un compte wrappe ne produit aucun transfert
systeme alors que les soldes bougent. On lit donc `accountData[].nativeBalanceChange`, jamais les
seuls transferts.

Usage :
    python3 etape2_financement.py --buyers e1_buyers_OPTIMUS.json
"""
from __future__ import annotations
import argparse, json, os, time
import lib_trace as L

MIN_INFLOW = 0.05          # en dessous : frais, poussiere, rentes de comptes
MAX_PAGES = 400            # 400 000 signatures avant de declarer la genese hors de portee
PREBUY_DAYS = 21
PREBUY_MAX_TX = 150


def roundness(x):
    """Etiquette le calibre d'un montant.

    Un montant precis a la neuvieme decimale sort d'une conversion : signature d'un service de swap.
    Un montant rond est un versement delibere : signature d'un distributeur intermediaire.
    """
    lam = round(x * L.LAMPORTS)
    if lam % L.LAMPORTS == 0:
        return "rond_SOL"
    if lam % 100_000_000 == 0:
        return "rond_0.1"
    if lam % 10_000_000 == 0:
        return "rond_0.01"
    if lam % 1_000_000 == 0:
        return "rond_0.001"
    return "precis_swap"


def token_sold(tx, wallet):
    """Le portefeuille a-t-il cede des jetons dans cette transaction ?

    Distinction indispensable. Un bot de sniping encaisse des centaines de rentrees de SOL par jour
    qui sont des produits de vente, pas des financements. Les compter comme financements ferait
    apparaitre des « decoupages » partout : deux bots qui vendent au meme instant sur la meme courbe
    produisent mecaniquement des montants voisins au meme moment. Generateur de faux positifs
    elimine a la source.
    """
    for ad in (tx.get("accountData") or []):
        for tb in (ad.get("tokenBalanceChanges") or []):
            if tb.get("userAccount") != wallet:
                continue
            raw = tb.get("rawTokenAmount") or {}
            try:
                if float(raw.get("tokenAmount") or 0) < 0:
                    return True
            except Exception:
                pass
    return False


def inflows_from(txs, sig_list, wallet, min_inflow, phase, rank_offset=0):
    out = []
    for rank, sig in enumerate(sig_list, 1 + rank_offset):
        tx = txs.get(sig)
        if not tx:
            continue
        deltas = L.balance_deltas(tx)
        gain = deltas.get(wallet, 0.0)
        if gain < min_inflow:
            continue
        srcs = sorted(((k, -d) for k, d in deltas.items()
                       if k != wallet and d <= -min_inflow and k not in L.SYSTEM_ACCOUNTS),
                      key=lambda kv: -kv[1])
        # Nature de la rentree. On garde tout, mais etiquete : l'etape 3 ne cherche le decoupage
        # que dans les financements.
        if token_sold(tx, wallet):
            nature = "produit_de_vente"
        elif tx.get("type") == "TRANSFER":
            nature = "financement"
        elif not srcs:
            nature = "indetermine_sans_source"
        else:
            nature = "financement"          # gain de SOL sans cession de jeton : versement recu
        ts = L.tx_ts(tx)
        out.append({"phase": phase, "nature": nature,
                    "rank_in_wallet_history": rank, "ts": ts, "utc": L.utc(ts),
                    "amount_sol": round(gain, 9), "calibre": roundness(gain),
                    "source": srcs[0][0] if srcs else None,
                    "source_amount_sol": round(srcs[0][1], 9) if srcs else None,
                    "source_known": L.KNOWN.get(srcs[0][0]) if srcs else None,
                    "n_debited_accounts": len(srcs),
                    "tx_type": tx.get("type"), "tx_source": tx.get("source"),
                    "signature": sig})
    return out


SIGCACHE = "cache_sigs"


def paginate_cached(w, prebuy_start):
    """Pagination mise en cache sur disque, poste de cout dominant (jusqu'a 400 appels pour un
    bot), a ne payer qu'une fois. Seul un resultat couvrant la fenetre est mis en cache, un echec
    est toujours retente."""
    os.makedirs(SIGCACHE, exist_ok=True)
    p = os.path.join(SIGCACHE, f"{w}.json")
    if os.path.exists(p):
        try:
            c = json.load(open(p))
            if c.get("prebuy_start") == prebuy_start:
                return c["sigs"], c["genesis"], c["pages"], c["hyperactif"]
        except Exception:
            pass
    sigs, genesis, pages = L.all_signatures(w, max_pages=MAX_PAGES, label=w[:8],
                                            stop_ts=prebuy_start)
    hyper = bool(getattr(L.all_signatures, "last_capped_by_projection", False))
    slim = [{"signature": s["signature"], "blockTime": s.get("blockTime")} for s in sigs]
    oldest = slim[0]["blockTime"] if slim else None
    if slim and (genesis or (oldest and oldest <= prebuy_start)):
        json.dump({"prebuy_start": prebuy_start, "genesis": genesis, "pages": pages,
                   "hyperactif": hyper, "sigs": slim}, open(p, "w"))
    return slim, genesis, pages, hyper


def analyse_wallet(w, first_buy_ts, head_tx, min_inflow):
    prebuy_start = first_buy_ts - PREBUY_DAYS * 86400
    # On pagine jusqu'a la genese ou jusqu'a depasser le debut de la fenetre pre-achat, selon ce qui
    # arrive d'abord. Un bot a 300 000 transactions ne sera pas remonte jusqu'a sa naissance, mais la
    # fenetre datee sera entierement couverte, et les deux cas sont rapportes separement.
    sigs, genesis, pages, hyper_flag = paginate_cached(w, prebuy_start)
    oldest = sigs[0].get("blockTime") if sigs else None
    hyperactif = hyper_flag
    covered_days = (round((first_buy_ts - oldest) / 86400.0, 2)
                    if oldest and oldest <= first_buy_ts else 0.0)
    info = {"wallet": w, "n_signatures_total": len(sigs), "pages_paginated": pages,
            "genesis_reached": genesis,
            "pagination_capped": pages >= MAX_PAGES or hyperactif,
            "hyperactif_non_mesurable": hyperactif,
            "prebuy_window_days_requested": PREBUY_DAYS,
            "prebuy_window_days_covered": min(covered_days, float(PREBUY_DAYS)),
            "oldest_seen_ts": oldest, "oldest_seen_utc": L.utc(oldest),
            "newest_seen_utc": L.utc(sigs[-1].get("blockTime")) if sigs else None,
            "prebuy_window_start_utc": L.utc(prebuy_start),
            "prebuy_window_reached": bool(oldest and oldest <= prebuy_start) or genesis,
            "born_within_prebuy_window": bool(genesis and oldest and oldest >= prebuy_start),
            "days_alive_before_first_buy": (round((first_buy_ts - oldest) / 86400, 2)
                                            if genesis and oldest else None),
            "inflows": []}
    if not sigs:
        info["measurement_failure"] = "aucune signature"
        return info

    picks, phases = [], []
    if genesis:
        for s in sigs[:head_tx]:
            picks.append(s["signature"]); phases.append("M1_naissance")
    pre = [s for s in sigs
           if prebuy_start <= (s.get("blockTime") or 0) <= first_buy_ts]
    for s in pre[:PREBUY_MAX_TX]:
        if s["signature"] not in picks:
            picks.append(s["signature"]); phases.append("M2_prebuy")
    info["n_tx_in_prebuy_window"] = len(pre)
    info["n_tx_requested"] = len(picks)

    txs = L.get_transactions(picks)
    info["n_tx_fetched"] = len(txs)
    seen = set()
    for sig, ph in zip(picks, phases):
        if sig in seen:
            continue
        seen.add(sig)
        info["inflows"].extend(inflows_from(txs, [sig], w, min_inflow, ph))
    info["inflows"].sort(key=lambda f: f["ts"])
    info["measurement_failure"] = None if info["prebuy_window_reached"] else \
        "fenetre pre-achat non atteinte (plafond de pagination)"
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--buyers", required=True)
    ap.add_argument("--head-tx", type=int, default=60)
    ap.add_argument("--min-inflow", type=float, default=MIN_INFLOW)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    src = json.load(open(a.buyers))
    label = src["label"]
    out = a.out or f"e2_funding_{label}.json"
    cache = {}
    if os.path.exists(out):
        try:
            for w in json.load(open(out))["wallets"]:
                # On ne remet en cache qu'une mesure reussie : la fenetre visee a ete atteinte et
                # l'adresse a bien rendu des signatures. Un echec est toujours retente.
                if (w.get("n_signatures_total") or 0) > 0 and w.get("prebuy_window_reached"):
                    cache[w["wallet"]] = w
        except Exception:
            cache = {}

    wallets = []
    buyers = src["buyers"]
    for i, b in enumerate(buyers, 1):
        w = b["wallet"]
        info = cache.get(w) or analyse_wallet(w, b["first_buy_ts"], a.head_tx, a.min_inflow)
        info.update({"buy_rank": b["rank"], "first_buy_utc": b["first_buy_utc"],
                     "first_buy_ts": b["first_buy_ts"],
                     "sol_spent_first_buy": b["sol_spent_first_buy"]})
        wallets.append(info)
        g = "genese OK" if info["genesis_reached"] else "GENESE HORS ATTEINTE"
        p = "prebuy OK" if info["prebuy_window_reached"] else "PREBUY HORS ATTEINTE"
        print(f"  [{i}/{len(buyers)}] #{b['rank']:>2d} {w[:14]}… {info['n_signatures_total']:>7d} sigs"
              f" · {len(info['inflows'])} entrees · {g} · {p}", flush=True)
        json.dump({"label": label, "mint": src["mint"], "wallets": wallets}, open(out, "w"), indent=1)
        time.sleep(0.05)

    nf_g = sum(1 for w in wallets if not w["genesis_reached"])
    nf_p = sum(1 for w in wallets if not w["prebuy_window_reached"])
    res = {"label": label, "mint": src["mint"], "n_wallets": len(wallets),
           "n_genesis_reached": len(wallets) - nf_g, "n_genesis_NOT_reached": nf_g,
           "n_prebuy_window_reached": len(wallets) - nf_p, "n_prebuy_NOT_reached": nf_p,
           "wallets_without_genesis": [w["wallet"] for w in wallets if not w["genesis_reached"]],
           "wallets_without_prebuy": [w["wallet"] for w in wallets
                                      if not w["prebuy_window_reached"]],
           "validite": ("Toutes les fenetres atteintes : un resultat negatif serait interpretable."
                        if nf_p == 0 else
                        f"{nf_p} portefeuille(s) dont la fenetre pre-achat n'est pas atteinte : pour "
                        "EUX un resultat negatif est un echec de mesure."),
           "wallets": wallets}
    json.dump(res, open(out, "w"), indent=1)
    print(f"\n  geneses atteintes : {len(wallets)-nf_g}/{len(wallets)} · "
          f"fenetres pre-achat atteintes : {len(wallets)-nf_p}/{len(wallets)} -> {out}")


if __name__ == "__main__":
    main()
