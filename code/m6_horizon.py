#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M6 : ce que devient le token apres la premiere heure.

Source : data/horizon.json, prix horaires releves a +1 h, +2 h, +4 h et +24 h
apres la fin de la capture, pour 193 tokens, via l'API publique GeckoTerminal.

Avertissement d'unite. Le prix d'entree vient des swaps et est en SOL par
token ; les prix horaires de GeckoTerminal sont en USD par token. Le rapport
brut close/entree melange donc deux unites et ne veut rien dire en valeur
absolue : il vaut le vrai multiple multiplie par le taux SOL/USD de l'epoque.
Un chiffre du type "mediane 0,35x a +1 h" suppose donc un taux qui ne figure
pas dans les donnees, n'est pas reproductible en l'etat, et n'est pas publie
ici comme un fait.

Ce qui est reproductible sans constante externe, c'est la decroissance
relative : le rapport entre deux horizons elimine le taux de change, qui se
simplifie. C'est la mesure principale. Le multiple absolu reste disponible via
--sol-usd <taux>, etiquete comme dependant d'une constante fournie par
l'utilisateur.

Survivance : les quatre horizons ne couvrent pas les memes tokens. Un token
sans bougie a +24 h a disparu, et l'exclure ameliore artificiellement le
resultat. La mesure principale porte donc sur le sous-ensemble apparie (les
tokens ayant les quatre horizons), le plus favorable au marche ; le
sous-ensemble non apparie est donne en sensibilite.

Usage :  python3 m6_horizon.py [--sol-usd 150]
"""

import argparse
import os
import statistics

import pumplib as P

H = ("1h", "2h", "4h", "24h")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sol-usd", type=float, default=None,
                    help="taux SOL/USD, pour convertir en multiple absolu")
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out", "m6_horizon.json"))
    a = ap.parse_args()

    rows = P.load_json("horizon.json")
    P.head("M6 : TRAJECTOIRE APRES LA PREMIERE HEURE", "MESURE")
    P.kv("tokens instrumentes", len(rows))

    no_data = [r for r in rows if r.get("status") != "ok"]
    P.kv("tokens sans aucune bougie horaire", len(no_data),
         note="%.1f %%, plus aucun volume echange" % (100.0 * len(no_data) / len(rows)))
    w = P.wilson(len(no_data), len(rows))
    P.kv("   IC95 de cette part", "[%.1f ; %.1f] %%" % (100 * w[0], 100 * w[1]))

    ok = [r for r in rows if r.get("entry_price")]
    full = [r for r in ok if all(r.get("close_" + h) for h in H)]

    print("\n  PRINCIPAL : sous-ensemble apparie (les 4 horizons disponibles).")
    P.kv("n", len(full), note="%.1f %% des tokens instrumentes"
                              % (100.0 * len(full) / len(rows)))

    # (1) La statistique par token : ce que subit un detenteur donne.
    print("\n  (1) Evolution par token depuis +1 h, ce que subit un"
          " detenteur.\n      Sans unite : le taux SOL/USD se simplifie dans"
          " le rapport.")
    print("      %-8s %8s %8s %8s %8s %8s   %s"
          % ("horizon", "p10", "p25", "mediane", "p75", "p90", "% en baisse"))
    per_tok = {}
    for h in H[1:]:
        per = [r["close_" + h] / r["close_1h"] for r in full]
        per_tok[h] = {"n": len(per), "med": statistics.median(per),
                      "p10": P.quantile(per, 0.10), "p25": P.quantile(per, 0.25),
                      "p75": P.quantile(per, 0.75), "p90": P.quantile(per, 0.90),
                      "pct_baisse": 100.0 * sum(1 for v in per if v < 1.0) / len(per)}
        t = per_tok[h]
        print("      +1h->%-3s %8.3f %8.3f %8.3f %8.3f %8.3f   %5.1f %%"
              % (h, t["p10"], t["p25"], t["med"], t["p75"], t["p90"],
                 t["pct_baisse"]))
    t24 = per_tok["24h"]
    lo, hi = P.bootstrap_median_ci([r["close_24h"] / r["close_1h"] for r in full])
    print("\n      Le token median survivant termine a x%.3f de son niveau de"
          " +1 h\n      (IC95 [%.3f ; %.3f]) : il ne s'effondre pas."
          " Mais le quart inferieur\n      perd %.0f %% et le decile inferieur"
          " perd %.0f %%. La perte n'est pas\n      typique, elle est"
          " concentree, et totale quand elle arrive."
          % (t24["med"], lo, hi, 100 * (1 - t24["p25"]), 100 * (1 - t24["p10"])))

    # (2) La statistique transversale : le niveau de prix de la population.
    print("\n  (2) Niveau de prix transversal de la population (mediane des"
          " prix a chaque\n      horizon, normalisee a +1 h). Ce n'est pas le"
          " parcours d'un token :\n      le token median a +24 h n'est pas le"
          " meme que le token median a +1 h.")
    ratios = {h: [r["close_" + h] / r["entry_price"] for r in full] for h in H}
    med = {h: statistics.median(ratios[h]) for h in H}
    base = med["1h"]
    print("      %-8s %14s" % ("horizon", "niveau relatif"))
    for h in H:
        print("      %-8s %14.3f" % (h, med[h] / base))
    print("      Les series (1) et (2) different fortement (x%.3f contre"
          " x%.3f a\n      +24 h) sans qu'il y ait d'erreur : les tokens les"
          " plus hauts sont ceux\n      qui s'effondrent le plus, ce qui"
          " ecrase la mediane transversale sans que\n      le token median"
          " ait beaucoup bouge. Citer x%.2f comme 'ce que perd\n      un"
          " detenteur' confondrait les deux. Le dossier cite (1) pour le"
          "\n      detenteur et (2) pour la population, jamais l'un pour"
          " l'autre."
          % (t24["med"], med["24h"] / base, med["24h"] / base))

    print("\n  SENSIBILITE : sous-ensemble non apparie (chaque horizon son n) :")
    print("    %-6s %5s %14s" % ("horizon", "n", "niveau relatif"))
    unm = {}
    for h in H:
        v = [r["close_" + h] / r["entry_price"] for r in ok if r.get("close_" + h)]
        unm[h] = {"n": len(v), "med": statistics.median(v)}
    b2 = unm["1h"]["med"]
    for h in H:
        print("    %-6s %5d %14.3f" % (h, unm[h]["n"], unm[h]["med"] / b2))
    print("    Ecart avec le sous-ensemble apparie : la version non appariee"
          " parait\n     pire a +2 h et meilleure a +24 h. C'est un effet de"
          " composition, pas un\n     resultat. Seule la version appariee est"
          " citee par le dossier.")

    abs_mult = None
    if a.sol_usd:
        abs_mult = {h: med[h] / a.sol_usd for h in H}
        print("\n  MULTIPLE ABSOLU, avec le taux SOL/USD = %.2f que vous avez"
              " fourni :" % a.sol_usd)
        for h in H:
            print("    %-6s x%.3f" % (h, abs_mult[h]))
        print("    [DEPEND D'UNE CONSTANTE EXTERNE : non reproductible sans"
              " elle, et\n     sensible a 100 %% a sa valeur. A ne pas citer"
              " comme une mesure.]")

    print("""
  LECTURE :
   - La moitie des tokens instrumentes n'a aucune bougie horaire : passe la
     premiere phase, il ne s'echange plus rien du tout. Un detenteur ne peut
     pas vendre faute de contrepartie. [MESURE, sans unite]
   - Sur ceux qui vivent encore, le niveau median a +24 h ne represente qu'une
     fraction du niveau de +1 h. [MESURE, sans unite]
   - Ces deux effets se cumulent : le sous-ensemble mesure est celui des
     survivants, et la population entiere fait pire.
     [INFERE, direction certaine, ampleur non mesuree ici]
   - Le multiple absolu (0,35x, 0,08x, etc.) n'est pas reproductible a partir
     de ces donnees seules : il exige un taux SOL/USD externe. [NON ETABLI en
     l'etat]""")

    P.emit({"n_instrumentes": len(rows), "n_sans_bougie": len(no_data),
            "part_sans_bougie": len(no_data) / len(rows),
            "apparie": {"n": len(full),
                        "niveau_relatif": {h: med[h] / base for h in H}},
            "non_apparie": {h: {"n": unm[h]["n"], "niveau_relatif": unm[h]["med"] / b2}
                            for h in H},
            "multiple_absolu": abs_mult,
            "sol_usd_fourni": a.sol_usd,
            "niveau": "MESURE (relatif) / NON ETABLI (absolu)"},
           os.path.abspath(a.out))


if __name__ == "__main__":
    main()
