#!/usr/bin/env python3
"""The exit ladder, stated as a policy — and measured against the alternatives.

THE POLICY
----------
    x2   -> sell 50 %      the stake is recovered; what remains rides at zero cost
    x5   -> sell a tranche
    x10  -> sell a tranche
    beyond -> manual

The first rung is the one that makes the rest possible. Once half is sold at x2 the position cannot
lose money, only make less — which is what allows a signal firing at 4 a.m. to be taken unattended.
The upper rungs exist because the return distribution has a long tail: on the executions in
docs/EXPLOITATION.md most trades land between +100 % and +700 % and one returned +28 465 %. A full
exit at x2 truncates that tail; holding for it gives back everything on the trades that never run.
The staircase keeps both, and pays for the option with the upside it forgoes.

WHY THIS FILE EXISTS
--------------------
A ladder is a set of numbers anyone can assert. This script does two things instead: it states the
policy as executable code, and it prints what the repository's own measurements say about applying
it to *current* launches — which is that it loses.

    x2/x5/x10 on the 2026 corpus:  0 of 15 exit policies have a positive mean return,
                                   0 of 15 have a 95 % CI clearing zero.

That is not a caveat attached to a strategy. It is the result, and it is the reason the repository
is titled the way it is.

USAGE
    python3 code/exit_ladder.py                 # the policy, and the verdict on it
    python3 code/exit_ladder.py --path 1 2.4 7 3   # apply it to a price path (multiples of entry)
"""
from __future__ import annotations
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

# (multiple of entry, share of the ORIGINAL position sold at that rung)
LADDER = [(2.0, 0.50), (5.0, 0.25), (10.0, 0.15)]
RESTE_MANUEL = 1.0 - sum(p for _, p in LADDER)


def simulate(path, ladder=LADDER):
    """Apply the ladder to a price path expressed in multiples of the entry price.

    Returns the realised multiple on the whole position. The unsold remainder is marked to the last
    price in the path — a convention, and stated as one: in reality that tranche is discretionary,
    and 'touched but not sold' is exactly the confusion PITFALLS P5 was written about.
    """
    vendu, produit, hauts = 0.0, 0.0, []
    for mult in path:
        for seuil, part in ladder:
            if mult >= seuil and seuil not in hauts:
                hauts.append(seuil)
                vendu += part
                produit += part * seuil
    reste = 1.0 - vendu
    produit += reste * path[-1]
    return {"multiple_realise": round(produit, 4), "part_vendue_sur_echelle": round(vendu, 4),
            "reste_marque_au_dernier_prix": round(reste, 4), "rungs_touches": hauts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", nargs="*", type=float,
                    help="trajectoire en multiples du prix d'entree, ex: 1 2.4 7 3")
    a = ap.parse_args()

    print("ECHELLE DE SORTIE")
    cum = 0.0
    for seuil, part in LADDER:
        cum += part
        print(f"  x{seuil:<5g} vendre {part:.0%}   (cumul {cum:.0%})")
    print(f"  au-dela  {RESTE_MANUEL:.0%} restant, discretionnaire")
    print("\n  Le premier barreau est le seul qui compte structurellement : a x2, vendre 50 %")
    print("  rend la position restante gratuite. Elle ne peut plus perdre, seulement gagner moins.")
    print("  C'est ce qui rend un signal de 4 h du matin prenable sans surveillance.")

    if a.path:
        r = simulate(a.path)
        print(f"\nTRAJECTOIRE {a.path}")
        print(f"  barreaux touches        : {r['rungs_touches'] or 'aucun'}")
        print(f"  vendu sur l'echelle     : {r['part_vendue_sur_echelle']:.0%}")
        print(f"  reste marque au dernier : {r['reste_marque_au_dernier_prix']:.0%}")
        print(f"  MULTIPLE REALISE        : {r['multiple_realise']:.3f}x")

    # --- ce que le depot mesure sur les lancements actuels ------------------------------------
    verdict = {}
    p = os.path.join(DATA, "cout_acheteur", "t1_base_rate_sorties.json")
    if os.path.exists(p):
        d = json.load(open(p))
        pol = d.get("politiques") or d.get("policies") or []
        if isinstance(pol, list) and pol:
            pos = [x for x in pol if (x.get("mean") or x.get("moyenne") or 0) > 0]
            verdict = {"n_politiques": len(pol), "n_moyenne_positive": len(pos)}

    print("\nCE QUE LES MESURES DISENT DE CETTE ECHELLE SUR LES LANCEMENTS DE 2026")
    if verdict:
        print(f"  politiques de sortie testees            : {verdict['n_politiques']}")
        print(f"  dont moyenne positive                   : {verdict['n_moyenne_positive']}")
    print("  entree post-snipe, +1 h                 : 0.35x")
    print("  entree post-snipe, +24 h                : 0.08x")
    print("  tokens ayant deja culmine avant d'etre visibles : 21.3 %")
    print("\n  L'echelle n'a pas change. Le marche si. Sur les lancements actuels la courbe est")
    print("  rachetee dans le slot de creation (42/42 verifies) : quand le lancement devient")
    print("  visible, la position n'est plus accumulee, elle est distribuee. Il n'y a pas de")
    print("  barreau a monter.")
    print("\n  Voir docs/RESULTATS.md et docs/EXPLOITATION.md section 6.")


if __name__ == "__main__":
    main()
