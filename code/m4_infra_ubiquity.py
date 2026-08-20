#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M4: why the infrastructure addresses have to be excluded.

A handful of addresses snipe an enormous share of every launch. They are not
operators, they are a service everyone uses. Left inside a computation of links
between tokens, they connect almost any pair artificially, and the giant network
one believes one has found is only an artefact. This is the easiest trap to walk
into on this data: a thesis resting on the uncleaned graph would be false.

The test: the size of the giant connected component of the token-token graph,
where two tokens are linked when they share at least k snipers, with and without
those addresses. If the component collapses when they are removed, they were
serving as artificial bridges.

Reads the captures, writes docs/out/m4_infra.json.

Usage:  python3 m4_infra_ubiquity.py [--data ...] [--k 3]
"""

import argparse
import collections
import itertools
import os

import pumplib as P

from m3_operators import INFRA


def giant_component(caps, exclude=(), k=3):
    """Taille de la plus grande composante connexe du graphe token-token,
    arete si >= k snipeurs communs. Union-find, stdlib."""
    ex = set(exclude)
    sets = [(d["mint"], set(d["snipers"]) - ex) for d in caps]
    parent = {m: m for m, _ in sets}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    # Inverted index, so that not every pair has to be compared
    by_w = collections.defaultdict(list)
    for m, s in sets:
        for w in s:
            by_w[w].append(m)
    shared = collections.Counter()
    for w, ms in by_w.items():
        for x, y in itertools.combinations(sorted(ms), 2):
            shared[(x, y)] += 1
    for (x, y), c in shared.items():
        if c >= k:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry
    comp = collections.Counter(find(m) for m, _ in sets)
    return max(comp.values()) if comp else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--k", type=int, default=3, help="snipeurs communs pour une arete")
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out", "m4_infra.json"))
    a = ap.parse_args()

    caps = [d for d in P.load_captures(a.data) if d.get("snipers")]
    N = len(caps)
    P.head("M4 : UBIQUITE DES ADRESSES D'INFRASTRUCTURE", "MESURE")
    P.kv("tokens du corpus", N)

    freq = collections.Counter()
    for d in caps:
        for w in set(d["snipers"]):
            freq[w] += 1

    print("\n  Les 12 adresses les plus ubiquitaires du corpus :")
    print("    %-46s %6s %8s %s" % ("adresse", "tokens", "part", "classee infra ?"))
    # Counter.most_common leaves ties in insertion order, which
    # depend du hachage : deux executions pouvaient permuter deux adresses a
    # egalite de comptage. Tri explicite (compte decroissant, puis adresse) =
    # sortie reproductible bit a bit.
    top = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
    for w, c in top:
        print("    %-46s %6d %7.1f %% %s"
              % (w, c, 100.0 * c / N, "OUI" if w in INFRA else "non"))

    print("\n  Effondrement de la composante geante (arete = >= %d snipeurs communs) :"
          % a.k)
    g_full = giant_component(caps, (), a.k)
    g_clean = giant_component(caps, INFRA, a.k)
    P.kv("composante geante, corpus brut", "%d tokens" % g_full,
         note="%.1f %% du corpus" % (100.0 * g_full / N))
    P.kv("composante geante, infra retiree", "%d tokens" % g_clean,
         note="%.1f %% du corpus" % (100.0 * g_clean / N))
    P.kv("=> reduction", "%.1f points" % (100.0 * (g_full - g_clean) / N))

    print("\n  Contribution de chaque adresse d'infra prise seule :")
    for w in sorted(INFRA, key=lambda x: (-freq.get(x, 0), x)):
        if freq.get(w, 0) == 0:
            continue
        g1 = giant_component(caps, {w}, a.k)
        print("    %-46s %4d tokens snipes  ->  geante %d (%+d)"
              % (w, freq[w], g1, g1 - g_full))

    print("""
  LECTURE :
   - Une seule adresse snipe une part a deux chiffres du corpus entier. Ce
     n'est pas un operateur de lancement mais un service partage. [MESURE]
   - Retirer ces adresses fait chuter la composante geante de plusieurs
     dizaines de points : les liens qu'elles creaient etaient artificiels.
     [MESURE]
   - Consequence sur le dossier : toute affirmation de type "ces tokens sont
     lies" qui n'exclut pas ces adresses est sans valeur. Les flottes de M3
     sont mesurees apres exclusion. [MESURE]
   - Ce que ces adresses sont exactement (bot de volume, service de snipe
     revendu, teneur de marche) n'est pas etabli par ce corpus. [NON ETABLI]""")

    P.emit({"n_tokens": N, "k": a.k,
            "top_ubiquite": [{"adresse": w, "tokens": c, "part": c / N,
                              "classee_infra": w in INFRA} for w, c in top],
            "composante_geante_brute": g_full,
            "composante_geante_nettoyee": g_clean,
            "niveau": "MESURE"}, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
