#!/usr/bin/env python3
"""A mechanical exit ladder, stated as executable code — and measured.

WHAT THIS FILE IS, AND WHAT IT IS NOT
-------------------------------------
It is not a reconstruction of how the 2024 trades were closed. Those exits were discretionary:
take-profits set by eye, one trade at a time (docs/EXPLOITATION.md section 3). The only automated
part was standing sell orders at x5 and x10 for the hours away from the screen. That automation was
an upside catcher, not a stop: if the price never reached x5, nothing sold. It did nothing whatsoever
for the downside, and an unattended position ran with the stake still in the market. The x2 was used
after a token had graduated off the bonding curve, on large positions. The size sold at any level was
never recorded.

What this file states is a MECHANICAL policy of the kind a reader will naturally propose in place of
judgement: sell fixed fractions at fixed multiples of entry, written out precisely enough to be
applied to real price paths and scored.

    x2   -> sell 50 %
    x5   -> sell 25 %
    x10  -> sell 15 %
    beyond -> never sold by this policy

The 50 / 25 / 15 split is stipulated by this script and sourced nowhere else. Fixing the numbers is
what makes a policy testable; it is not a claim that these were the numbers. Do not quote them as
anyone's configuration.

WHY IT IS STILL WORTH MEASURING
-------------------------------
Because "could a rule have done this?" has an answer, and the answer is the point of the repository.

    2026 corpus, measured in code/t1_base_rate_sorties.py:
        0 of 15 exit policies have a positive mean return
        0 of 15 have a 95 % CI clearing zero

Scope, stated exactly: those fifteen are all single full exits — five timeouts, three trailing stops,
six take-profit / stop-loss variants, and buy-and-hold. A staged ladder like the one above is not
among them, and no backtest of a staged ladder exists in this repository. What the fifteen establish
is broader and more useful: on 2026 launches, no exit rule tested rescues an unfiltered entry. The
exit is not where the problem is. The entry is — the curve is bought out in the creation slot, and
there is nothing left to climb.

The two headline numbers below are derived from the artefact at run time, not asserted here.

USAGE
    python3 code/exit_ladder.py                    # the policy under test, and the 2026 verdict
    python3 code/exit_ladder.py --path 1 2.4 7 3   # apply it to a price path (multiples of entry)
"""
from __future__ import annotations
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

# A MECHANICAL policy under test: (multiple of entry, share of the ORIGINAL position sold there).
# NOT a record of what was executed. The levels x5 and x10 are the ones that were configured for
# unattended trading in 2024; x2 was used post-graduation, on large positions. The three SHARES have
# no source in this repository, and no tranche size was ever confirmed: they are fixed here only so
# the policy is executable and the simulation reproducible. Do not quote them as tranche sizes that
# were used. See docs/EXPLOITATION.md section 3.
LADDER = [(2.0, 0.50), (5.0, 0.25), (10.0, 0.15)]
RESTE_MANUEL = 1.0 - sum(p for _, p in LADDER)  # the 10 % this policy never sells


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

    print("ECHELLE MECANIQUE MISE A L'EPREUVE (stipulee ici, pas un releve d'execution)")
    cum = 0.0
    for seuil, part in LADDER:
        cum += part
        print(f"  x{seuil:<5g} vendre {part:.0%}   (cumul {cum:.0%})")
    print(f"  au-dela  {RESTE_MANUEL:.0%} restant, jamais vendu par cette politique")
    print("\n  Les sorties de 2024 etaient discretionnaires : prises de benefice reglees a l'oeil,")
    print("  trade par trade. La seule partie automatisee etait des ordres de vente a x5 et x10")
    print("  pour les heures passees loin de l'ecran — un attrapeur de hausse, pas un stop : si le")
    print("  prix n'atteignait pas x5, rien ne se vendait, et une position non surveillee tournait")
    print("  avec la mise encore engagee. Le x2 servait apres la sortie de courbe, sur les grosses")
    print("  positions. Les tailles de tranche n'ont jamais ete relevees : les 50/25/15 ci-dessus")
    print("  sont une hypothese de ce script, posee pour pouvoir etre mesuree, et ne sont la")
    print("  configuration de personne. Voir docs/EXPLOITATION.md section 3.")

    if a.path:
        r = simulate(a.path)
        print(f"\nTRAJECTOIRE {a.path}")
        print(f"  barreaux touches        : {r['rungs_touches'] or 'aucun'}")
        print(f"  vendu sur l'echelle     : {r['part_vendue_sur_echelle']:.0%}")
        print(f"  reste marque au dernier : {r['reste_marque_au_dernier_prix']:.0%}")
        print(f"  MULTIPLE REALISE        : {r['multiple_realise']:.3f}x")

    # --- ce que le depot mesure sur les lancements actuels ------------------------------------
    p = os.path.join(DATA, "cout_acheteur", "t1_base_rate_sorties.json")
    if not os.path.exists(p):
        raise SystemExit(f"artefact absent : {p} — lancer d'abord code/t1_base_rate_sorties.py")
    d = json.load(open(p))
    pol = d.get("politiques") or d.get("policies")
    if isinstance(pol, dict):
        pol = [{"nom": k, **v} for k, v in pol.items()]
    if not isinstance(pol, list) or not pol:
        raise SystemExit(f"'politiques' inexploitable dans {p} : {type(pol).__name__}")
    n_pos = sum(1 for x in pol if x["moyenne_pct"] > 0)
    n_ci = sum(1 for x in pol if x["moyenne_ic95_cluster_pct"][0] > 0)

    print("\nCE QUE LES MESURES DISENT DE TOUTE POLITIQUE MECANIQUE SUR LES LANCEMENTS DE 2026")
    print(f"  politiques de sortie testees (sorties uniques)  : {len(pol)}")
    print(f"  dont moyenne positive                           : {n_pos}")
    print(f"  dont IC95 de moyenne au-dessus de zero          : {n_ci}")
    print("  entree post-snipe, +1 h                         : 0.35x")
    print("  entree post-snipe, +24 h                        : 0.08x")
    print("  tokens ayant deja culmine avant d'etre visibles  : 21.3 %")
    print("\n  Ces quinze politiques sont toutes des sorties uniques : l'echelle etagee ci-dessus")
    print("  n'en fait pas partie et n'est backtestee nulle part dans ce depot.")
    print("\n  Ce n'est pas une politique de sortie qui s'est degradee, c'est le marche. Sur les")
    print("  lancements actuels la courbe est rachetee dans le slot de creation (42/42 verifies) :")
    print("  quand le lancement devient visible, la position n'est plus accumulee, elle est")
    print("  distribuee. Il n'y a pas de barreau a monter — pour aucune politique, pas seulement")
    print("  celle-ci.")
    print("\n  Voir docs/RESULTATS.md et docs/EXPLOITATION.md section 6.")


if __name__ == "__main__":
    main()
