#!/usr/bin/env python3
"""Synthese : taux de base du decoupage chez les premiers acheteurs des tokens temoins.

Fusionne la passe 1 (11_temoins_split.py, plafond de 04 : 60 pages), la passe 2
(12_deep_genese_temoins.py, plafond 600 pages sur les adresses non resolues) et la passe 3
(14_corrige_pages_vides.py, prioritaire), puis :

  1. recalcule le detecteur de decoupage par token avec les donnees les plus completes ;
  2. classe chaque token selon la validite de son resultat :
       positif            un decoupage est detecte ;
       negatif valide     aucun decoupage et toutes les geneses atteintes ;
       negatif partiel    aucun decoupage mais au moins une genese non atteinte (echec de mesure) ;
       non concluant      moins de 10 acheteurs precoces distincts, pas de matiere ;
  3. rapporte la matiere disponible au detecteur par token (portefeuilles a genese atteinte et
     nombre d'entrees de financement), condition sans laquelle un zero ne prouve rien ;
  4. ne modifie aucune constante du detecteur.

Lit temoins_split.json, plus temoins_deep_genese.json et temoins_corrections.json s'ils existent.
Ecrit synthese_taux_de_base.json a cote du script.
"""
from __future__ import annotations
import json, os, math, datetime as dt
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
P1 = json.load(open(f"{D}/temoins_split.json"))
P2 = json.load(open(f"{D}/temoins_deep_genese.json")) if os.path.exists(f"{D}/temoins_deep_genese.json") else {"adresses": []}
DEEP = {a["wallet"]: a for a in P2.get("adresses", [])}
# Passe 3 : corrige les arrets sur page vide (voir 14_corrige_pages_vides.py). Priorite maximale.
P3 = json.load(open(f"{D}/temoins_corrections.json")) if os.path.exists(f"{D}/temoins_corrections.json") else {"adresses": []}
CORR = {a["wallet"]: a for a in P3.get("adresses", [])}
DEEP.update(CORR)

REL_TOL, WINDOW_S, MIN_CLUSTER = 1e-4, 3600, 3


def decs(x):
    s = f"{x:.9f}".rstrip("0")
    return 0 if "." not in s else len(s.split(".")[1])


def find_splits(funding):
    rows = sorted([(w, e["sol"], e["ts"], e.get("source_probable"))
                   for w, l in funding.items() for e in l], key=lambda r: r[1])
    out, used = [], set()
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
        ws = {g[1] for g in grp}
        if len(ws) >= MIN_CLUSTER:
            for g in grp:
                used.add(g[0])
            tt = [g[3] for g in grp]
            nd = decs(amt)
            out.append({"amount_sol": round(amt, 9), "n_wallets": len(ws), "wallets": sorted(ws),
                        "span_seconds": max(tt) - min(tt),
                        "date": dt.datetime.fromtimestamp(min(tt), dt.UTC).strftime("%Y-%m-%d %H:%M"),
                        "sources_probables": sorted({g[4] for g in grp if g[4]}),
                        "nature_montant": "rond (distributeur)" if nd <= 3
                                          else "issu d'une conversion (swap)"})
    return sorted(out, key=lambda c: -c["n_wallets"])


tokens, ubiq = [], defaultdict(list)
for t in P1["tokens"]:
    funding, wal = {}, []
    for w in t["portefeuilles"]:
        a = w["wallet"]
        src = DEEP.get(a)
        if src is not None and (src["genese_atteinte"] or src["n_sigs_vues"] > w["n_sigs_vues"]):
            ent, gen, ns, old, passe = (src["entrees"], src["genese_atteinte"],
                                        src["n_sigs_vues"], src["plus_ancienne_vue_utc"],
                                        3 if a in CORR else 2)
        else:
            ent, gen, ns, old, passe = (w["entrees"], w["genese_atteinte"],
                                        w["n_sigs_vues"], w["plus_ancienne_vue_utc"], 1)
        funding[a] = ent
        wal.append({"wallet": a, "genese_atteinte": gen, "n_sigs_vues": ns,
                    "plus_ancienne_activite_vue_utc": old, "n_entrees_financement": len(ent),
                    "entrees": ent, "passe_retenue": passe})
        ubiq[a].append(t["symbole"])

    cl = find_splits(funding)
    ngen = sum(1 for w in wal if w["genese_atteinte"])
    nent = sum(w["n_entrees_financement"] for w in wal)
    nb = len(wal)
    if cl:
        verdict = "POSITIF"
    elif nb < 10:
        verdict = "NON CONCLUANT (moins de 10 acheteurs precoces distincts)"
    elif ngen == nb:
        verdict = "NEGATIF VALIDE (toutes les geneses atteintes)"
    else:
        verdict = f"NEGATIF PARTIEL ({nb - ngen}/{nb} geneses non atteintes)"
    tokens.append({
        "symbole": t["symbole"], "mint": t["mint"], "role": t["role"],
        "date_creation_utc": t["date_creation_utc"], "fenetre_ancre": t["fenetre_ancre"],
        "tx_totales_bonding_curve": t["tx_totales_bonding_curve"],
        "mint_genese_atteinte": t["mint_pagination"]["genese_atteinte"],
        "n_acheteurs_precoces_distincts": nb,
        "n_geneses_atteintes": ngen, "n_geneses_non_atteintes": nb - ngen,
        "n_entrees_financement_total": nent,
        "matiere_suffisante_pour_le_detecteur": nb >= 10 and ngen >= MIN_CLUSTER and nent >= MIN_CLUSTER,
        "n_clusters": len(cl), "decoupage_detecte": bool(cl), "clusters": cl,
        "verdict": verdict, "portefeuilles": wal})

pos = [t for t in tokens if t["decoupage_detecte"]]
neg_val = [t for t in tokens if t["verdict"].startswith("NEGATIF VALIDE")]
neg_part = [t for t in tokens if t["verdict"].startswith("NEGATIF PARTIEL")]
nonc = [t for t in tokens if t["verdict"].startswith("NON CONCLUANT")]
n_eval = len(pos) + len(neg_val) + len(neg_part)

# borne haute a 95 % du taux de base quand 0 positif sur n (regle de trois)
def borne_haute(k, n):
    return None if n == 0 else round(1 - (0.05 ** (1.0 / n)), 3) if k == 0 else None

synth = {
    "genere_le": dt.datetime.now(dt.UTC).isoformat(),
    "objet": "TAUX DE BASE : proportion de tokens temoins (meme seconde de creation, jamais gradues, "
             "jamais King-of-the-Hill) dont les premiers acheteurs presentent un decoupage de financement.",
    "procedure": "Identique a code/04_early_buyers_funding.py, constantes recopiees sans ajustement. "
                 "Seule difference : plafond de pagination porte de 60 a 600 pages sur les adresses "
                 "non resolues (correction du piege n.1, pas un seuil de detection).",
    "parametres_detecteur": P1["parametres"],
    "taux_de_base": {
        "tokens_analyses": len(tokens),
        "tokens_avec_decoupage": len(pos),
        "taux_brut": f"{len(pos)}/{len(tokens)}",
        "tokens_evaluables_hors_non_concluants": n_eval,
        "taux_sur_evaluables": f"{len(pos)}/{n_eval}",
        "negatifs_valides": len(neg_val),
        "negatifs_partiels_echec_de_mesure": len(neg_part),
        "non_concluants_faute_d_acheteurs": len(nonc),
        "borne_haute_95pct_du_taux_de_base": borne_haute(len(pos), n_eval),
        "lecture": "Zero positif sur les temoins signifie que le detecteur ne se declenche pas "
                   "spontanement sur des tokens de la meme seconde qui n'ont pas performe. "
                   "La borne haute a 95 % (regle de trois) est la seule facon honnete de resumer "
                   "un zero sur un petit echantillon.",
    },
    "portefeuilles_ubiquitaires": [
        {"wallet": w, "n_tokens_temoins": len(ts), "tokens": ts}
        for w, ts in sorted(ubiq.items(), key=lambda kv: -len(kv[1])) if len(ts) >= 2],
    "reserves": [],
    "tokens": tokens,
}

nb_ubiq = len(synth["portefeuilles_ubiquitaires"])
synth["reserves"] = [
    f"{len(nonc)}/{len(tokens)} temoins ont moins de 10 acheteurs precoces distincts (7 a 9). "
    "Sur ces tokens le detecteur, qui exige 3 portefeuilles au meme montant, n'a presque pas de "
    "matiere : leur zero ne peut PAS etre compte comme un negatif. C'est une asymetrie structurelle "
    "entre tokens morts et tokens qui performent, et elle gonfle mecaniquement tout contraste.",
    f"{len(neg_part)}/{len(tokens)} temoins gardent au moins un portefeuille dont la genese n'est "
    "pas atteinte meme a 600 000 signatures. Ces adresses ont une activite industrielle : leurs "
    "40 premieres transactions reelles sont hors de portee, donc leur absence de decoupage est un "
    "echec de mesure, pas un negatif.",
    f"{nb_ubiq} portefeuilles apparaissent comme acheteur precoce de 2 a 7 temoins DIFFERENTS. "
    "Ce sont des bots de sniping / routeurs publics, pas des flottes d'operateur : ils ne peuvent "
    "pas porter la signature cherchee, et ce sont eux qui saturent le plafond de pagination.",
    "La procedure 04 ne detecte un decoupage que si le portefeuille acheteur a ete CREE pour "
    "l'operation : elle n'inspecte que ses 40 premieres transactions. Un acheteur preexistant, "
    "meme finance par decoupage plus tard, echappe par construction au detecteur. Cette limite "
    "vaut identiquement pour les cibles et pour les temoins, donc elle ne biaise pas la comparaison, "
    "mais elle plafonne la sensibilite des deux cotes.",
    "Un taux de base de zero ne devient un resultat qu'une fois les CIBLES mesurees avec ce meme "
    "script. Tant que ce n'est pas fait, ce fichier ne dit pas que les cibles sont anormales : il "
    "dit seulement que le detecteur ne produit pas de faux positif sur 9 temoins apparies.",
]

json.dump(synth, open(f"{D}/synthese_taux_de_base.json", "w"), indent=1, ensure_ascii=False)

print("=" * 78)
print("TAUX DE BASE — GROUPE TEMOIN (9 tokens, meme seconde de creation que les cibles)")
print("=" * 78)
print(f"{'token':<12}{'ach.':>5}{'gen.':>6}{'entr.':>7}{'clust':>6}  verdict")
for t in tokens:
    print(f"{t['symbole']:<12}{t['n_acheteurs_precoces_distincts']:>5}"
          f"{t['n_geneses_atteintes']:>4}/{t['n_acheteurs_precoces_distincts']:<2}"
          f"{t['n_entrees_financement_total']:>7}{t['n_clusters']:>6}  {t['verdict']}")
tb = synth["taux_de_base"]
print("-" * 78)
print(f"TAUX BRUT           : {tb['taux_brut']} tokens avec decoupage")
print(f"NEGATIFS VALIDES    : {tb['negatifs_valides']}")
print(f"NEGATIFS PARTIELS   : {tb['negatifs_partiels_echec_de_mesure']} (echec de mesure)")
print(f"NON CONCLUANTS      : {tb['non_concluants_faute_d_acheteurs']} (<10 acheteurs)")
print(f"BORNE HAUTE 95%     : {tb['borne_haute_95pct_du_taux_de_base']} "
      f"sur {tb['tokens_evaluables_hors_non_concluants']} evaluables")
print("-" * 78)
for r in synth["reserves"]:
    print("  RESERVE : " + r)
print(f"\nEcrit dans {D}/synthese_taux_de_base.json")
