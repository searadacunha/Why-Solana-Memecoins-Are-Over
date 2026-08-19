#!/usr/bin/env python3
"""Presence test on the traded tokens, part by part, for the pattern as the author described it.

The split detector of `splitlib.py` asks three generic questions: were two early buyers funded in
the same transaction (A), did three or more receive the same amount within an hour (B), do two share
a private funder (C). The author describes four properties at once: fresh buying wallets (created
shortly before they buy, no prior history), several of them receiving near-identical amounts close
together in time, those amounts coming from a single funding step, then sequential buys early on the
same curve. The conjunction can hold where B is absent, since B needs three wallets at one amount
inside one hour.

That funding step comes in two calibres, one link apart in the same chain: a swap output (an amount
like 1.393934883 SOL, precise to nine decimals) or a round payment from an intermediate distributor
(4 x 3.000000000 SOL). The first version required a swap output and returned 0 tokens out of 15, the
reference case included: its four wallets each got exactly 3.000000000 SOL from a distributor. The
calibre is now reported per cluster instead of gating the search, and the reference case serves as
positive control, so any change that makes it disappear is a bug here.

"Fresh" and "near-identical" are the only free parameters, so both are swept rather than picked, the
freshness cut over several values and the tolerance over four orders of magnitude, with the whole
sweep printed. A conclusion holding at one setting only shows up as such. Scope is presence, not
prevalence: see `code/a4_selection_bias.py`.

Usage:
    python3 code/a5_author_pattern.py
Reads only committed files under ./data/. No network, no key.
"""
from __future__ import annotations
import glob, json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# Traded tokens only. The controls are irrelevant to a presence test and are not read here.
CIBLES = [os.path.join(DATA, "trace_cohorte", "e2_funding_*.json"),
          os.path.join(DATA, "trace_optimus", "e2_funding_OPTIMUS.json"),
          os.path.join(DATA, "trace_optimus", "e2_funding_ODIN_POSITIF.json"),
          os.path.join(DATA, "trace_h2w6", "e2_funding_h2w6gm6jz.json"),
          os.path.join(DATA, "trace_polmrkt", "e2_funding_POLMRKTBOT.json")]

FRESH_DAYS = 7.0        # "fresh wallet": swept below
REL_TOL = 1e-3          # "near-identical": swept below
WINDOW_S = 6 * 3600     # funded close together
MIN_WALLETS = 2         # the author describes "several wallets", not a fixed count

# A second, stricter tier. Two wallets receiving a common round amount five hours apart is the kind
# of coincidence any active week produces; the same amount reaching three or more fresh wallets
# inside two minutes is a dispatch. Both tiers are reported, so the gap between them shows how much
# of the result rests on the loose reading.
FRANC_MIN_WALLETS = 3
FRANC_MAX_SPAN_S = 120


def est_swap(inf):
    """Reported, not required: does this funding step look like a conversion output?

    Two independent markers: the amount has the shape of a swap output (nine significant decimals
    rather than a round figure), or the counterparty is a known swap service. Kept as an attribute
    of each cluster so the two links of the chain can be told apart in the output.
    """
    return (inf.get("calibre") == "precis_swap"
            or "swap" in (inf.get("source_known") or "").lower())


def load(patterns):
    out = {}
    for pat in patterns:
        for path in sorted(glob.glob(pat)):
            d = json.load(open(path))
            out.setdefault(d["label"], d)
    return out


def analyse(d, fresh_days, rel_tol):
    """Wallets satisfying parts 1+2, then the amount clusters satisfying part 3."""
    frais = []
    for w in d["wallets"]:
        age = w.get("days_alive_before_first_buy")
        est_frais = (w.get("born_within_prebuy_window") is True
                     or (age is not None and age <= fresh_days))
        if not est_frais:
            continue
        for inf in w.get("inflows", []):
            if inf.get("nature") != "financement":
                continue
            frais.append({"wallet": w["wallet"], "amount": inf["amount_sol"], "ts": inf["ts"],
                          "utc": inf.get("utc"), "calibre": inf.get("calibre"),
                          "source": inf.get("source"), "known": inf.get("source_known"),
                          "swap": est_swap(inf), "age_days": age})

    frais.sort(key=lambda r: (r["amount"], r["ts"]))
    clusters, used = [], set()
    for i, r in enumerate(frais):
        if i in used or r["amount"] <= 0:
            continue
        grp = [r]
        idx = [i]
        for j in range(i + 1, len(frais)):
            if j in used:
                continue
            s = frais[j]
            if abs(s["amount"] - r["amount"]) > r["amount"] * rel_tol:
                break
            if s["wallet"] != r["wallet"] and abs(s["ts"] - r["ts"]) <= WINDOW_S:
                grp.append(s)
                idx.append(j)
        wallets = {g["wallet"] for g in grp}
        if len(wallets) >= MIN_WALLETS:
            used.update(idx)
            ts = [g["ts"] for g in grp]
            clusters.append({
                "montant_sol": round(r["amount"], 9), "n_portefeuilles": len(wallets),
                "portefeuilles": sorted(wallets), "etendue_s": max(ts) - min(ts),
                "utc_premier": min(g["utc"] for g in grp),
                "calibres": sorted({g["calibre"] for g in grp}),
                "forme_sortie_de_swap": any(g["swap"] for g in grp),
                "sources": sorted({g["source"] for g in grp if g["source"]}),
                "services_identifies": sorted({g["known"] for g in grp if g["known"]}),
                "ages_jours": [round(g["age_days"], 2) for g in grp
                               if g["age_days"] is not None],
            })
    clusters.sort(key=lambda c: -c["n_portefeuilles"])
    for c in clusters:
        c["franc"] = (c["n_portefeuilles"] >= FRANC_MIN_WALLETS
                      and c["etendue_s"] <= FRANC_MAX_SPAN_S)
    return frais, clusters


tokens = load(CIBLES)
print(f"{len(tokens)} tokens tradés analysés\n")

# --- main pass at the declared thresholds --------------------------------------------------------
rows = []
for lab in sorted(tokens):
    d = tokens[lab]
    frais, clusters = analyse(d, FRESH_DAYS, REL_TOL)
    n_w = d["n_wallets"]
    n_gen = d.get("n_genesis_reached")
    rows.append({
        "token": lab, "mint": d.get("mint"),
        "n_premiers_acheteurs": n_w, "n_genese_atteinte": n_gen,
        "n_portefeuilles_frais": len({f["wallet"] for f in frais}),
        "n_clusters_montants_voisins": len(clusters),
        "plus_gros_cluster": clusters[0]["n_portefeuilles"] if clusters else 0,
        "motif_present": bool(clusters),
        "n_clusters_francs": sum(1 for c in clusters if c["franc"]),
        "motif_franc": any(c["franc"] for c in clusters),
        "clusters": clusters[:6],
    })

pres = [r for r in rows if r["motif_present"]]
franc = [r for r in rows if r["motif_franc"]]
print(f"{'token':<12} {'acheteurs':>9} {'genese':>7} {'frais':>6} "
      f"{'clusters':>8} {'max':>4}  motif  franc")
for r in rows:
    print(f"{r['token']:<12} {r['n_premiers_acheteurs']:>9} {r['n_genese_atteinte']:>7} "
          f"{r['n_portefeuilles_frais']:>6} {r['n_clusters_montants_voisins']:>8} "
          f"{r['plus_gros_cluster']:>4}  {'OUI' if r['motif_present'] else 'non':<5}  "
          f"{'OUI' if r['motif_franc'] else 'non'}")
print(f"\nMOTIF PRESENT (lecture large)  : {len(pres)}/{len(rows)} tokens tradés")
print(f"MOTIF FRANC  (>={FRANC_MIN_WALLETS} ptf en <={FRANC_MAX_SPAN_S}s) : "
      f"{len(franc)}/{len(rows)} tokens tradés")
ctrl = next((r for r in rows if r["token"] == "ODIN_POSITIF"), None)
if ctrl:
    print(f"CONTROLE POSITIF (cas de reference) : "
          f"{'OK, retrouve' if ctrl['motif_franc'] else 'ECHEC, detecteur casse'}")

# --- sensitivity: both free parameters swept, so neither carries the conclusion alone ------------
print("\nBalayage des deux seuils libres (nombre de tokens où le motif est présent) :")
print(f"{'fraicheur':>10} " + " ".join(f"{t:>9.0e}" for t in (1e-4, 1e-3, 1e-2, 1e-1)))
sweep = {}
for fd in (1.0, 3.0, 7.0, 14.0, 30.0):
    line, row = [], {}
    for tol in (1e-4, 1e-3, 1e-2, 1e-1):
        n = sum(1 for lab in tokens if analyse(tokens[lab], fd, tol)[1])
        row[f"{tol:.0e}"] = n
        line.append(f"{n:>9d}")
    sweep[f"{fd:g}j"] = row
    print(f"{fd:>9g}j " + " ".join(line))

out = os.path.join(DATA, "adverse", "a5_author_pattern.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump({
    "objet": "Test de presence du motif tel que l'auteur le decrit : portefeuilles frais, "
             "finances par une sortie de swap, montants voisins, sur les tokens qu'il a tradés.",
    "motif_teste": {
        "1_portefeuille_frais": f"cree moins de {FRESH_DAYS:g} jours avant son premier achat, "
                                f"ou dont la naissance tombe dans la fenetre pre-achat",
        "2_calibre_du_versement": "rapporte, pas exige : 'precis_swap' (sortie de conversion) "
                                  "ou montant rond (versement d'un distributeur intermediaire). "
                                  "Exiger l'un excluait le cas de reference, qui utilise l'autre.",
        "3_montants_voisins": f"au moins {MIN_WALLETS} portefeuilles distincts a "
                              f"{REL_TOL:.0e} pres, dans une fenetre de {WINDOW_S//3600} h",
        "4_achats_sequentiels": "les portefeuilles retenus figurent parmi les premiers acheteurs "
                                "de la courbe, par construction du corpus",
    },
    "difference_avec_le_detecteur_generique": "Le critere B de splitlib.py exige 3 "
        "portefeuilles au meme montant en 1 h, sans regarder ni la fraicheur du portefeuille ni "
        "l'origine du versement. Il peut donc manquer le motif decrit ici, et inversement.",
    "portee": "Presence, pas prevalence. Cet echantillon est choisi sur l'issue "
              "(voir a4_selection_bias.py) : il peut montrer que le mecanisme est la, jamais "
              "combien il est repandu.",
    "controle_positif": "Le cas de reference (ODIN_POSITIF) doit ressortir positif. S'il ne "
                        "ressort pas, le detecteur est casse et aucune conclusion n'est lisible. "
                        "La premiere version de ce script le manquait, ce qui a revele le defaut.",
    "n_tokens": len(rows), "n_motif_present": len(pres), "n_motif_franc": len(franc),
    "palier_franc": {"min_portefeuilles": FRANC_MIN_WALLETS, "etendue_max_s": FRANC_MAX_SPAN_S},
    "seuils": {"fraicheur_jours": FRESH_DAYS, "tolerance_relative": REL_TOL,
               "fenetre_s": WINDOW_S, "min_portefeuilles": MIN_WALLETS},
    "balayage_des_seuils": sweep,
    "tokens": rows,
}, open(out, "w"), indent=1, ensure_ascii=False)
print(f"\n-> {out}")
