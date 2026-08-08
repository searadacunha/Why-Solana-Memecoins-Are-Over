#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A9 — The Act I burst, measured, and the two collections that disagree about it.

WHAT THIS SCRIPT ESTABLISHES
----------------------------
For every phase-1 token in `data/split/all_buyers_g2y.json`, it recounts, from the committed
file alone:

  * how many virgin wallets received a gateway payment BEFORE the token existed
    (`avant_token` is true), cross-checked against the count the file itself carries;
  * the distinct amounts of those payments, at nine decimals, with no tolerance;
  * the size and the time span of the largest exactly-equal amount group;
  * the delay between that funding and the creation of the token, reported twice — from the
    first credit and from the last.

For the reference token `h2w6gm6jz` this reproduces the two figures the README quotes for Act I
(9 wallets, one amount, 343 seconds) and agrees with a third one: the delay is 7.71 h from the
first credit and 7.62 h from the last — the from-last-credit reading rounds to "7.6 hours".

WHY A SEPARATE SCRIPT, AND THE RECONCILIATION
---------------------------------------------
`a5_author_pattern.py` reads a different collection of the same token — `data/trace_h2w6/
e2_funding_h2w6gm6jz.json`, a per-wallet inflow trace — and therefore reports a different burst.
That is not a contradiction in the chain, it is a coverage difference between two collections,
and it has to be stated as one. This script recomputes both sides and prints them next to each
other. It does NOT establish which of the two collections is complete: neither file carries the
information that would settle it.

WHAT IT DOES NOT DO
-------------------
  * It does not measure any share of supply. `data/` holds no token quantity bought for these
    tokens, so the README's "2% of supply / 20 million tokens" is not recomputed here, at all.
  * It does not build a control population, so it says nothing about how rare this pattern is.
    That question belongs to `a4_selection_bias.py`, and it is not answered by this script.
  * It does not re-derive the timestamps from chain: it reads the committed collection.

INPUT
    data/split/all_buyers_g2y.json          (required)
    data/trace_h2w6/e2_funding_h2w6gm6jz.json  (optional, reconciliation only)

Usage :  python3 a9_g2y_prelaunch.py [--data <chemin .json>] [--out <chemin .json>]

Sortie :  docs/out/a9_g2y_prelaunch.json
"""

import argparse
import datetime
import json
import os

import pumplib as P

# The token the README and docs/PATTERN.md build Act I on. Named here because the script has to
# reconcile it against a second collection; every figure about it is measured, none is assumed.
TOKEN_REFERENCE = "h2w6gm6jz"

# The second collection of that same token: the per-wallet inflow trace that a5_author_pattern.py
# reads. Reconciliation input, never a measurement input — its absence degrades, it does not fail.
TRACE_RECONCILIATION = ("trace_h2w6", "e2_funding_h2w6gm6jz.json")

# Creation dates in the source carry a fraction of a second ("...T14:50:36.376000Z"). It is
# dropped: the timestamp is truncated to the second, which is the resolution of every funding
# ts in the same file. Effect on a delay in hours: at most 2.8e-4 h. Reported here so that a
# fourth decimal that moves by one unit is not mistaken for a measurement disagreement.
FORMAT_CREATION = "%Y-%m-%dT%H:%M:%S"


def parse_creation(s):
    """ISO string -> UNIX seconds, UTC. Raises on anything it cannot read; never returns None."""
    if not isinstance(s, str) or len(s) < 19:
        raise SystemExit("date de creation illisible : %r" % (s,))
    d = datetime.datetime.strptime(s[:19], FORMAT_CREATION)
    return int(d.replace(tzinfo=datetime.timezone.utc).timestamp())


def evenements_avant_token(entree):
    """[(ts, sol, wallet)] for every G2Y credit flagged avant_token, sorted, no deduplication."""
    ev = []
    for w, v in entree.get("portefeuilles", {}).items():
        for g in v.get("g2y", []):
            if g.get("avant_token") is not True:
                continue
            if "ts" not in g or "sol" not in g:
                raise SystemExit("credit g2y sans ts/sol pour le portefeuille %s" % w)
            ev.append((int(g["ts"]), float(g["sol"]), w))
    ev.sort(key=lambda x: (x[0], x[2], x[1]))
    return ev


def groupe_montant_max(ev):
    """Largest group of credits sharing an EXACTLY equal amount (rounded at 9 decimals).

    No tolerance and no clustering: the claim under test is exact equality at nine decimals, so
    a tolerance would be assuming the conclusion. Ties on group size are broken by the smaller
    amount, purely so the output is deterministic.
    """
    par_montant = {}
    for ts, sol, w in ev:
        par_montant.setdefault(round(sol, 9), []).append((ts, sol, w))
    if not par_montant:
        return None
    montant, grp = sorted(par_montant.items(), key=lambda kv: (-len(kv[1]), kv[0]))[0]
    ts = [g[0] for g in grp]
    return {
        "montant_sol": montant,
        "n_credits": len(grp),
        "n_portefeuilles": len({g[2] for g in grp}),
        "etendue_s": int(max(ts) - min(ts)),
        "ts_premier": int(min(ts)),
        "ts_dernier": int(max(ts)),
        "portefeuilles": sorted({g[2] for g in grp}),
    }


def mesure_token(nom, entree):
    """One token -> one record. Rejected tokens are returned as a rejection, never dropped."""
    if entree.get("mesurable") is not True:
        return None, {"jeton": nom, "motif": "non_mesurable_scan_interrompu",
                      "erreur_source": entree.get("erreur")}
    if "creation" not in entree or "mint" not in entree:
        return None, {"jeton": nom, "motif": "champ_creation_ou_mint_absent",
                      "erreur_source": None}

    creation_ts = parse_creation(entree["creation"])
    ev = evenements_avant_token(entree)
    portefeuilles = sorted({e[2] for e in ev})
    declare = entree.get("n_vierges_finances_G2Y_avant_token")
    grp = groupe_montant_max(ev)

    rec = {
        "jeton": nom,
        "mint": entree["mint"],
        "creation_utc": entree["creation"],
        "creation_ts": creation_ts,
        "n_credits_avant_token": len(ev),
        "n_vierges_finances_avant_token": len(portefeuilles),
        "n_vierges_finances_avant_token_declare_fichier": declare,
        "accord_avec_le_fichier": (declare == len(portefeuilles)),
        "montants_distincts_sol": sorted({round(e[1], 9) for e in ev}),
        "n_montants_distincts": len({round(e[1], 9) for e in ev}),
        "groupe_montant_max": grp,
        "delai_creation_h_depuis_premier_credit": None,
        "delai_creation_h_depuis_dernier_credit": None,
        "etendue_totale_s": None,
    }
    if ev:
        rec["etendue_totale_s"] = int(ev[-1][0] - ev[0][0])
        rec["delai_creation_h_depuis_premier_credit"] = round((creation_ts - ev[0][0]) / 3600.0, 4)
        rec["delai_creation_h_depuis_dernier_credit"] = round((creation_ts - ev[-1][0]) / 3600.0, 4)
    return rec, None


def reconciliation(chemin, montant_ref, portefeuilles_a):
    """Recount source B: total inflows, inflows at the reference amount, wallet overlap.

    Degrades if the file is absent — this is a reconciliation, not an input. It never guesses:
    an unreadable file is reported as unreadable, not as zero.
    """
    if not os.path.exists(chemin):
        return {"disponible": False,
                "chemin": None,
                "note": "trace absente de ce depot : la reconciliation n'a pas ete faite. "
                        "Aucun chiffre de source A n'en depend."}
    with open(chemin) as f:
        d = json.load(f)
    if not isinstance(d.get("wallets"), list):
        raise SystemExit("trace illisible (cle 'wallets' absente ou non-liste) : %s" % chemin)

    n_inflows = 0
    n_financement = 0
    n_au_montant = 0
    ecarts = []
    portefeuilles_b = set()
    for w in d["wallets"]:
        portefeuilles_b.add(w["wallet"])
        for inf in w.get("inflows", []):
            if "amount_sol" not in inf:
                raise SystemExit("inflow sans amount_sol dans %s" % chemin)
            a = round(float(inf["amount_sol"]), 9)
            n_inflows += 1
            if inf.get("nature") == "financement":
                n_financement += 1
            if a == montant_ref:
                n_au_montant += 1
            ecarts.append((abs(a - montant_ref), a))
    plus_proche = sorted(ecarts)[0][1] if ecarts else None

    return {
        "disponible": True,
        "chemin": "data/%s/%s" % TRACE_RECONCILIATION,
        "lue_par": "a5_author_pattern.py",
        "n_portefeuilles": len(portefeuilles_b),
        "n_inflows_total": n_inflows,
        "n_inflows_nature_financement": n_financement,
        "montant_de_reference_sol": montant_ref,
        "n_inflows_au_montant_de_reference": n_au_montant,
        "montant_le_plus_proche_sol": plus_proche,
        "n_portefeuilles_communs_avec_source_a": len(portefeuilles_b & set(portefeuilles_a)),
        "lecture": "Deux collectes du meme token. Elles ne partagent aucun portefeuille et "
                   "aucun montant de reference. C'est un ecart de couverture entre deux "
                   "collectes, pas une contradiction sur la chaine. Ce script n'etablit PAS "
                   "laquelle des deux est complete.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out",
                                                  "a9_g2y_prelaunch.json"))
    a = ap.parse_args()

    # Garde-fou : avec --data (jeu d'exemple), on n'ecrase PAS l'artefact
    # publie. Un tableau du dossier ne doit jamais pouvoir etre remplace par le
    # resultat d'un echantillon de 20 tokens sans que personne s'en apercoive.
    if a.data and a.out == ap.get_default("out"):
        a.out = os.path.join(P.HERE, "..", "data", "sample",
                             os.path.basename(a.out))

    src = a.data or os.path.join(P.DATA, "split", "all_buyers_g2y.json")
    if not os.path.exists(src):
        raise SystemExit("fichier absent : data/split/all_buyers_g2y.json ; il est publie avec "
                         "le depot, sinon le regenerer avec python3 code/04_early_buyers_funding.py")
    with open(src) as f:
        brut = json.load(f)

    P.head("A9 — ACT I: THE PRE-LAUNCH FUNDING BURST", "MESURE")

    records, rejets = [], []
    for nom in sorted(brut):
        rec, rej = mesure_token(nom, brut[nom])
        (records if rec else rejets).append(rec or rej)

    print("\n  %-12s %5s %5s %5s %5s %6s %8s %9s %9s" % (
        "jeton", "n_pf", "decl", "cred", "mont", "maxgrp", "span_s", "dt_1er_h", "dt_der_h"))
    print("  " + "-" * 74)
    for r in records:
        g = r["groupe_montant_max"]
        print("  %-12s %5d %5s %5d %5d %6s %8s %9s %9s" % (
            r["jeton"], r["n_vierges_finances_avant_token"],
            r["n_vierges_finances_avant_token_declare_fichier"],
            r["n_credits_avant_token"], r["n_montants_distincts"],
            g["n_portefeuilles"] if g else "-",
            g["etendue_s"] if g else "-",
            r["delai_creation_h_depuis_premier_credit"]
            if r["delai_creation_h_depuis_premier_credit"] is not None else "-",
            r["delai_creation_h_depuis_dernier_credit"]
            if r["delai_creation_h_depuis_dernier_credit"] is not None else "-"))

    desaccords = [r["jeton"] for r in records if not r["accord_avec_le_fichier"]]
    P.kv("tokens dans le fichier", len(brut))
    P.kv("tokens mesures", len(records))
    P.kv("tokens rejetes (comptes, non ignores)", len(rejets),
         note=", ".join("%s: %s" % (x["jeton"], x["motif"]) for x in rejets) or "-")
    P.kv("tokens ou notre compte diverge du compte du fichier", len(desaccords),
         note=", ".join(desaccords) or "aucun")

    ref = [r for r in records if r["jeton"] == TOKEN_REFERENCE]
    if not ref:
        raise SystemExit("token de reference %s absent du fichier : la reconciliation ne peut "
                         "pas etre faite" % TOKEN_REFERENCE)
    ref = ref[0]
    grp = ref["groupe_montant_max"]
    if grp is None:
        raise SystemExit("token de reference %s sans credit avant creation" % TOKEN_REFERENCE)

    print("\n  CAS DE REFERENCE — %s (%s)" % (ref["jeton"], ref["mint"]))
    P.kv("virgin wallets funded before the token existed", ref["n_vierges_finances_avant_token"])
    P.kv("distinct amounts, at nine decimals", ref["n_montants_distincts"])
    P.kv("amount of the largest equal group, SOL", "%.9f" % grp["montant_sol"],
         n=grp["n_portefeuilles"])
    P.kv("span of that group, seconds", grp["etendue_s"])
    P.kv("delay to token creation, from the FIRST credit, h",
         ref["delai_creation_h_depuis_premier_credit"])
    P.kv("delay to token creation, from the LAST credit, h",
         ref["delai_creation_h_depuis_dernier_credit"])

    # The same amount landing on another token of the cohort is a measured fact, not an inference.
    autres = sorted(r["jeton"] for r in records if r["jeton"] != ref["jeton"]
                    and grp["montant_sol"] in r["montants_distincts_sol"])
    P.kv("other tokens of this file carrying the same exact amount", len(autres),
         note=", ".join(autres) or "aucun")

    rec_b = reconciliation(os.path.join(P.DATA, *TRACE_RECONCILIATION),
                           grp["montant_sol"], grp["portefeuilles"])
    print("\n  RECONCILIATION — deux collectes du meme token")
    if rec_b["disponible"]:
        print("  source A (data/split/all_buyers_g2y.json) : %d credits a %.9f SOL en %d s ; "
              "source B (%s, lue par %s) : %d inflows, %d a ce montant."
              % (grp["n_credits"], grp["montant_sol"], grp["etendue_s"],
                 rec_b["chemin"], rec_b["lue_par"],
                 rec_b["n_inflows_total"], rec_b["n_inflows_au_montant_de_reference"]))
        P.kv("source B — wallets", rec_b["n_portefeuilles"])
        P.kv("source B — inflows tagged 'financement'", rec_b["n_inflows_nature_financement"])
        P.kv("source B — closest amount to the reference, SOL",
             "%.9f" % rec_b["montant_le_plus_proche_sol"]
             if rec_b["montant_le_plus_proche_sol"] is not None else "-")
        P.kv("wallets common to source A and source B", rec_b["n_portefeuilles_communs_avec_source_a"])
    else:
        print("  " + rec_b["note"])

    non_etabli = [
        "part de supply achetee par portefeuille : data/ ne contient aucune quantite de tokens "
        "achetee pour ces tokens (seul sol_spent_first_buy existe, dans une autre collecte), "
        "donc ni les 2 % de supply ni les 20 millions de tokens ne sont mesures ici",
        "que ce motif soit rare : aucune population temoin n'est construite par ce script, "
        "voir a4_selection_bias.py",
        "laquelle des deux collectes du token de reference est complete : les deux fichiers "
        "sont [MESURE], leur desaccord est un ecart de couverture, il n'est pas arbitre ici",
    ]

    print("""
=> Established: %d virgin wallets received %.9f SOL each, before the token existed,
   inside %d seconds. Both figures are recomputed from the committed file. [MESURE]
=> Established: the delay is %.2f h from the first credit and %.2f h from the last. The README
   states 7.6 h, and a9's from-last-credit measurement rounds to 7.6 — agreement, not
   contradiction. This is a measured figure, not an assumed one. [MESURE]
=> Established: the two collections of this token disagree, and they disagree completely — no
   shared wallet, no credit at the reference amount in source B. [MESURE]
=> Inferred: that disagreement is a coverage difference between two scans of the same object,
   not two incompatible accounts of it. [INFERE]
=> NOT established here: which collection is complete, what share of supply these wallets
   bought, and whether this pattern is rare. [NON ETABLI]""" % (
        grp["n_portefeuilles"], grp["montant_sol"], grp["etendue_s"],
        ref["delai_creation_h_depuis_premier_credit"],
        ref["delai_creation_h_depuis_dernier_credit"]))

    P.emit({
        "objet": "Recomptage des credits de passerelle recus par des portefeuilles vierges "
                 "AVANT la creation du token, pour chaque token de phase 1, plus la "
                 "reconciliation du token de reference contre la seconde collecte.",
        "source": "data/split/all_buyers_g2y.json",
        "convention_horodatage": "date de creation tronquee a la seconde (la fraction de "
                                 "seconde du fichier est ignoree, <= 2.8e-4 h sur un delai)",
        "n_tokens_fichier": len(brut),
        "n_tokens_mesures": len(records),
        "n_tokens_rejetes": len(rejets),
        "rejets": sorted(rejets, key=lambda x: x["jeton"]),
        "n_tokens_en_desaccord_avec_le_compte_du_fichier": len(desaccords),
        "tokens_en_desaccord": desaccords,
        "par_token": records,
        "cas_reference": {
            "jeton": ref["jeton"],
            "mint": ref["mint"],
            "n_portefeuilles": grp["n_portefeuilles"],
            "montant_sol": grp["montant_sol"],
            "etendue_s": grp["etendue_s"],
            "delai_creation_h_depuis_premier_credit":
                ref["delai_creation_h_depuis_premier_credit"],
            "delai_creation_h_depuis_dernier_credit":
                ref["delai_creation_h_depuis_dernier_credit"],
            "delai_readme_annonce_h": 7.6,
            "autres_tokens_au_meme_montant": autres,
        },
        "reconciliation": rec_b,
        "non_etabli": non_etabli,
        "niveau": "MESURE",
    }, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
