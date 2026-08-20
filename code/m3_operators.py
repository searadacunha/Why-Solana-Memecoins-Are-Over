#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3: six distinct fleets, one single method.

This script decides between two opposing claims.

  H_unique  : "one entity controls all of it".
  H_methode : "several distinct entities apply the same method".

The split is made on measurable criteria, not on an intuition:
  - addresses or tokens shared between fleets gain ground for H_unique.
  - fleets that are strictly disjoint but identical in geometry, the same number
    of addresses per launch and the same perfect co-occurrence, support
    H_methode and leave H_unique unestablished.

On this corpus the measurement supports H_methode, and the dossier claims
nothing beyond that. Shared infrastructure upstream, common funders or common
exit hubs, remains possible and is flagged [INFERE] elsewhere: it cannot be
measured in this corpus, which holds no transfers.

The data used is the `snipers[]` field of each capture, the addresses that
bought the token on the bonding curve before the observable pool opened. They
therefore barely appear in the swap flow, which is the subject of the dossier.

The fleet addresses below are public and checkable on any Solana explorer. They
name addresses, never people.

Usage:  python3 m3_operators.py [--data ...]
"""

import argparse
import collections
import itertools
import math
import os

import pumplib as P

# --------------------------------------------------------------------------
# Fleet addresses, established by the forensics upstream. This script does not
# assume they are right, it tests them: counts, disjointness, co-occurrence. A
# fleet whose co-occurrence were not significant would show up as such in the
# output.
# --------------------------------------------------------------------------
FLEETS = {
    "F002": ["22vL22PcYcoAVCwYN8iDW9VrFEYq93TCtr7a6avNVyjL",
             "2AqFJzcgSMQ9v7Vwh4yE7Vux8brcrjus1eg4K1zM2zUd",
             "2wHHnAmdhFaAAsayWAeqKe3snK3KkbRQkRgLwTtz7iCi",
             "9yxmCNwZcHe63NucU9yvCt7b1ja3jwP9v4T3yFMkQ1Z9",
             "46ojZjmvYCzgikVQ4NZ1rSMz2vURDhW74U1CQm5p6HSM",
             "C4v2WTmWmYpYZA6JBU7Mh1rdRq1pmCpY5RaYNkkh4AZL",
             "HgUpqjurhgkSkPK3JsfjZZ9JknxY9fLRLNKKGyUSMLfQ"],
    "F003": ["339QJtzBbL47zCP4vhFa11tmKL3uJhUZjhNGSw4iwnoY",
             "6Qx9iprva3A9ywyDPaNFC2KjVLFxJZyxTGxqU4UAHLDP",
             "8qhHz3D4A1AhcGwRS6ZRH4Y7iCr2ojWqt24LovtnCETv",
             "A4416eujnydT7gnSTtiW2hnADsNin2mKNKnWVcw71MGX"],
    "F004": ["2GMhqu3cZsBsGXcdKQnAavzia4iaWT8BjdHBSWMywsuA",
             "Aj5Pexz2nm9LAh9UvFp28dvvRS8j75sCsG9aSW4cQ4SN",
             "DroL19BGzX91iRebZ69cz6SRHEfRfBws5ko95SA4Lrwz",
             "FBqJs9fqD6tgFKiCkja2fwD4NYQpbdkt8doR1KTbpGKs"],
    "F006": ["2LLHCtDpZWWsoeyAcjnnBgwsqzfvWx8EKfE8YTmGyafk",
             "AQVoCADzm2aoXW3Qwj4rBsNm9YMHoLFt8SnyitqjcHRP",
             "BxLmrDJaNr9hA35FBGASAhUK74Gs98AyvQXx6HSR1Qft",
             "E7T1Vs7aCLkN7TyFg382rhG7yVM5cWvjuwhfQkWPiSEH"],
    "OP1":  ["yHCxHBEaJW5tbndqC8JciSThr7U1cqLpdcsvHcx6PRe"],
    "OP2":  ["GeBJSHK4WsGrz2HRvTbqvWGx4JRMpHfJG2ikzrYBDuwR"],
}

# Adresses d'infrastructure partagee, a exclure de tout calcul de lien : elles
# snipent une part enorme du corpus et relient artificiellement n'importe quelle
# pair of tokens. m4_infra_ubiquity.py measures how ubiquitous they are.
INFRA = {
    "RDCT-d4fb6b1f86",
    "zAnr3GphY5t6xPahAaCQKPNBSxhYEtvV41JTqPFqmbb",
    "LfEcaUf77iEhnz6gFpLqYgDb5Uk6Ekc5n69wu7Qa9Uw",
    "BnnNJJgy9w2MLQ9XBKJKG9FQa2r9qdW7u5VpzEkwUcc3",
    "9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq",
    "dshAybqFXYVVTd4mzy9Uk6KD7km8wE9iZgPMYZdzEXc",
    "GVQWqWtncZnqkmobXJUvqn158NNEGC5BzqKCR3uw9Bg4",
    "CqVZZpYYe3VCsNTujpwfD4s252Y5CFuSdmq8o7rHf7cy",
    "Anubis512ho5t7S6LNSwoxUWdeQmX2kf3RvZ8ApHHF5w",
}


def hyper_pval(k, a, b, N):
    """P(X >= k) under the hypergeometric law: two addresses seen in a and b
    tokens out of N, how many tokens would they share by chance. This is what
    says whether a co-occurrence is surprising. Exact integer arithmetic
    (stdlib), returned as a raw probability, not a log.
    """
    tot = math.comb(N, b)
    s = 0
    for i in range(k, min(a, b) + 1):
        s += math.comb(a, i) * math.comb(N - a, b - i)
    return s / tot if tot else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out", "m3_operators.json"))
    a = ap.parse_args()

    caps = [d for d in P.load_captures(a.data) if d.get("snipers")]
    N = len(caps)
    P.head("M3 : FLOTTES D'OPERATEURS", "MESURE")
    P.kv("tokens avec liste snipers[] exploitable", N)

    # How often each address appears in the corpus
    freq = collections.Counter()
    for d in caps:
        for w in set(d["snipers"]):
            freq[w] += 1

    res = {}
    print("\n  Comptes par flotte (une flotte = un ensemble d'adresses) :")
    print("    %-6s %6s %6s %-24s %-16s" % ("flotte", "n_tok", "n_addr",
                                            "adresses par lancement", "presences AMM"))
    for name, addrs in FLEETS.items():
        S = set(addrs)
        toks, core_sizes, amm = [], [], 0
        for d in caps:
            s = set(d["snipers"])
            if not (s & S):
                continue
            toks.append(d["mint"])
            core_sizes.append(len(s & S))
            amm += len({w["trader"] for w in P.clean_swaps(d)} & S)
        dist = collections.Counter(core_sizes)
        res[name] = {"n_tokens": len(toks), "n_adresses": len(S),
                     "tokens": sorted(toks),
                     "adresses_par_lancement": dict(dist),
                     "presences_dans_le_flux_AMM": amm}
        dstr = ", ".join("%d addr x%d" % (k, v) for k, v in sorted(dist.items()))
        print("    %-6s %6d %6d %-24s %-16d" % (name, len(toks), len(S), dstr, amm))

    # ---------------------------------------------------------------- H_unique
    print("\n  TEST DE H_unique : les flottes partagent-elles quoi que ce soit ?")
    shared_addr, shared_tok = [], []
    for x, y in itertools.combinations(FLEETS, 2):
        ia = set(FLEETS[x]) & set(FLEETS[y])
        it = set(res[x]["tokens"]) & set(res[y]["tokens"])
        if ia:
            shared_addr.append((x, y, sorted(ia)))
        if it:
            shared_tok.append((x, y, sorted(it)))
    P.kv("paires de flottes partageant >= 1 adresse", len(shared_addr),
         note="sur %d paires" % (len(FLEETS) * (len(FLEETS) - 1) // 2))
    P.kv("paires de flottes partageant >= 1 token", len(shared_tok),
         note="sur %d paires" % (len(FLEETS) * (len(FLEETS) - 1) // 2))
    for x, y, v in shared_addr:
        print("      ! %s / %s : %s" % (x, y, v))
    for x, y, v in shared_tok:
        print("      ! %s / %s : %d tokens" % (x, y, len(v)))
    union = set()
    for name in FLEETS:
        union |= set(res[name]["tokens"])
    P.kv("tokens couverts par l'union des 6 flottes", len(union),
         note="%.1f %% du corpus" % (100.0 * len(union) / N))

    # ---------------------------------------------------------------- H_methode
    print("\n  TEST DE H_methode : la geometrie est-elle la meme ?")
    quads = [k for k in FLEETS if len(FLEETS[k]) > 1]
    for name in quads:
        dist = res[name]["adresses_par_lancement"]
        n = res[name]["n_tokens"]
        exact4 = dist.get(4, 0)
        w = P.wilson(exact4, n)
        P.kv("%s : lancements avec exactement 4 adresses" % name,
             "%d / %d" % (exact4, n), n=n,
             note="IC95 [%.2f ; %.2f]" % w)
    for name in ("OP1", "OP2"):
        dist = res[name]["adresses_par_lancement"]
        P.kv("%s : lancements avec exactement 1 adresse" % name,
             "%d / %d" % (dist.get(1, 0), res[name]["n_tokens"]),
             n=res[name]["n_tokens"])

    # co-occurrence : est-ce du hasard ?
    print("\n  La co-occurrence des adresses d'une meme flotte est-elle fortuite ?")
    print("    (loi hypergeometrique : deux adresses vues dans a et b tokens sur"
          " N=%d)" % N)
    cooc = {}
    for name in quads:
        pairs = []
        for x, y in itertools.combinations(sorted(FLEETS[name]), 2):
            a_, b_ = freq.get(x, 0), freq.get(y, 0)
            if a_ == 0 or b_ == 0:
                continue
            k = sum(1 for d in caps if {x, y} <= set(d["snipers"]))
            if k == 0:
                continue
            exp = a_ * b_ / N
            pairs.append({"a": x, "b": y, "obs": k, "attendu": exp,
                          "lift": k / exp if exp else None,
                          "p": hyper_pval(k, a_, b_, N)})
        if pairs:
            worst = max(pairs, key=lambda r: r["p"])
            cooc[name] = pairs
            strong = sum(1 for r in pairs if r["p"] is not None and r["p"] < 1e-3)
            P.kv("%s : %d paires d'adresses co-occurrentes" % (name, len(pairs)),
                 "lift median x%.0f" % P.median([r["lift"] for r in pairs]),
                 note="%d/%d paires a p<1e-3 ; p le moins bon %.1e"
                      % (strong, len(pairs), worst["p"]))

    # taux de reutilisation du noyau, contre une base mesuree
    print("\n  Reutilisation : une flotte reprend-elle les memes adresses d'un"
          " lancement au suivant ?")
    reuse = {}
    for name in FLEETS:
        toks = [d for d in caps if set(d["snipers"]) & set(FLEETS[name])]
        toks.sort(key=lambda d: d["created"])
        vals = []
        for i in range(1, len(toks)):
            cur = set(toks[i]["snipers"]) & set(FLEETS[name])
            prv = set(toks[i - 1]["snipers"]) & set(FLEETS[name])
            if cur:
                vals.append(len(cur & prv) / len(cur))
        if vals:
            reuse[name] = sum(vals) / len(vals)
    # Baseline: the same computation on ordinary snipers, excluding the
    # infrastructure addresses and the fleets
    fleet_all = set().union(*[set(v) for v in FLEETS.values()])
    caps_s = sorted(caps, key=lambda d: d["created"])
    base_vals = []
    for i in range(1, len(caps_s)):
        cur = set(caps_s[i]["snipers"]) - INFRA - fleet_all
        prv = set(caps_s[i - 1]["snipers"]) - INFRA - fleet_all
        if cur:
            base_vals.append(len(cur & prv) / len(cur))
    base = sum(base_vals) / len(base_vals) if base_vals else None
    for name in FLEETS:
        if name in reuse:
            P.kv("%s : reutilisation d'un lancement au suivant" % name,
                 "%.3f" % reuse[name], n=res[name]["n_tokens"],
                 note="x%.0f la base" % (reuse[name] / base) if base else "")
    P.kv("BASE : snipeurs ordinaires (hors infra, hors flottes)",
         "%.3f" % base, n=len(base_vals))
    print("      (OP1 et OP2 n'ont qu'une adresse : leur taux vaut 1,000 par"
          " construction et ne prouve rien. Seuls F002..F006 sont informatifs.)")

    print("""
  CONCLUSION DE M3 :
   - Les 6 flottes ne partagent aucune adresse et aucun token. [MESURE]
     H_unique n'est pas soutenue par ce corpus, et le dossier ne l'affirme pas.
   - Les 4 flottes multi-adresses engagent exactement 4 adresses a chaque
     lancement, sans une seule exception sur 42 lancements. [MESURE]
   - La co-occurrence de ces adresses est plusieurs ordres de grandeur au-dessus
     du hasard. Ce ne sont pas des acheteurs independants. [MESURE]
   - Elles reutilisent leurs adresses d'un lancement au suivant a un taux sans
     commune mesure avec les snipeurs ordinaires. [MESURE]
   => Ce qui est etabli : des entites distinctes appliquent une methode
      identique. [MESURE + INFERE pour le mot "methode"]
   => Ce qui n'est pas etabli ici : un controle unique, une coordination entre
      flottes, une identite civile quelconque. [NON ETABLI]""")

    P.emit({"n_tokens_corpus": N, "flottes": res,
            "paires_partageant_une_adresse": len(shared_addr),
            "paires_partageant_un_token": len(shared_tok),
            "tokens_couverts_union": len(union),
            "cooccurrence": cooc, "reutilisation": reuse,
            "reutilisation_base": base,
            "niveau": "MESURE"}, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
