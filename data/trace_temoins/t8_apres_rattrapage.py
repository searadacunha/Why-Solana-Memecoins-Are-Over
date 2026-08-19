#!/usr/bin/env python3
"""Etape 8 : le taux de base change-t-il quand on force la couverture ?

Relance le detecteur inchange (t3_decoupage.py) sur les fichiers rattrapes e2r_funding_*.json et
compare, token par token, avec la mesure principale. Deux issues possibles, toutes deux
informatives :

 - le taux de base ne bouge pas : la couverture manquante n'y etait pour rien, et les negatifs
   deviennent des negatifs pleinement valides au lieu d'echecs de mesure ;
 - le taux de base monte : la mesure principale sous-estimait le taux de faux positifs, ce qui
   affaiblit encore les cibles.

Ecrit e3r_splits_<token>.json, t8_journal_rattrapage_consolide.json et t8_apres_rattrapage.json.

Piege : le journal de rattrapage est reconstruit depuis les journaux d'execution jobC.out et
jobD.out, car les deux passages paralleles ecrivent le meme fichier journal et le second ecrase le
premier.
"""
from __future__ import annotations
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def journal_depuis_logs():
    rows, token = [], None
    pat = re.compile(r"\[\d+/\d+\]\s+(\S+)…\s+(\d+) pages, (\d+) sigs, prebuy "
                     r"(MAINTENANT COUVERT|toujours hors atteinte), (\d+) entrees")
    for lg in ("jobC.out", "jobD.out"):
        p = os.path.join(HERE, lg)
        if not os.path.exists(p):
            continue
        for line in open(p):
            m = re.match(r"=== (\S+) : (\d+)/(\d+) portefeuilles a rattraper", line.strip())
            if m:
                token = m.group(1)
                continue
            m = pat.search(line)
            if m and token:
                rows.append({"token": token, "wallet_prefixe": m.group(1),
                             "pages": int(m.group(2)), "sigs": int(m.group(3)),
                             "prebuy_reached_apres": m.group(4) == "MAINTENANT COUVERT",
                             "n_inflows_apres": int(m.group(5)), "journal": lg})
    return rows


def main():
    jr = journal_depuis_logs()
    json.dump(jr, open(os.path.join(HERE, "t8_journal_rattrapage_consolide.json"), "w"), indent=1)

    comp = []
    for p in sorted(glob.glob(os.path.join(HERE, "e2r_funding_*.json"))):
        lab = os.path.basename(p)[len("e2r_funding_"):-len(".json")]
        out = os.path.join(HERE, f"e3r_splits_{lab}.json")
        r = subprocess.run([sys.executable, os.path.join(HERE, "t3_decoupage.py"),
                            "--funding", p, "--out", out], cwd=HERE,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  !! {lab} : {r.stderr[-300:]}")
            continue
        av = json.load(open(os.path.join(HERE, f"e3_splits_{lab}.json")))
        ap = json.load(open(out))
        comp.append({
            "token": lab,
            "avant": {"A": len(av["A_meme_transaction"]),
                      "B": len(av["B_meme_montant_meme_moment"]),
                      "C_prive": len(av["C_bailleurs_communs_PRIVES"]),
                      "prebuy": f"{av['n_prebuy_reached']}/{av['n_wallets']}",
                      "genese": f"{av['n_genesis_reached']}/{av['n_wallets']}",
                      "verdict": av["verdict"][:60]},
            "apres": {"A": len(ap["A_meme_transaction"]),
                      "B": len(ap["B_meme_montant_meme_moment"]),
                      "C_prive": len(ap["C_bailleurs_communs_PRIVES"]),
                      "prebuy": f"{ap['n_prebuy_reached']}/{ap['n_wallets']}",
                      "genese": f"{ap['n_genesis_reached']}/{ap['n_wallets']}",
                      "verdict": ap["verdict"][:60]},
            "signature_changee": (len(av["A_meme_transaction"]) != len(ap["A_meme_transaction"])
                                  or len(av["B_meme_montant_meme_moment"])
                                  != len(ap["B_meme_montant_meme_moment"])
                                  or len(av["C_bailleurs_communs_PRIVES"])
                                  != len(ap["C_bailleurs_communs_PRIVES"])),
        })

    res = {"objet": "Sensibilite du taux de base au plafond de pagination (900 pages au lieu de 400)",
           "n_portefeuilles_retentes": len(jr),
           "n_recuperes": sum(1 for x in jr if x["prebuy_reached_apres"]),
           "n_structurellement_hors_atteinte": sum(1 for x in jr
                                                   if not x["prebuy_reached_apres"]),
           "signatures_max_lues_sur_un_seul_portefeuille": max((x["sigs"] for x in jr), default=0),
           "n_tokens_avec_signature_changee": sum(1 for c in comp if c["signature_changee"]),
           "comparaison": comp, "journal": jr}
    json.dump(res, open(os.path.join(HERE, "t8_apres_rattrapage.json"), "w"), indent=1)

    print(f"\n{'='*92}\nRATTRAPAGE DE COUVERTURE — {len(jr)} portefeuilles retentes a 900 pages")
    print("=" * 92)
    print(f"  recuperes : {res['n_recuperes']}   ·   toujours hors d'atteinte : "
          f"{res['n_structurellement_hors_atteinte']}   ·   "
          f"jusqu'a {res['signatures_max_lues_sur_un_seul_portefeuille']:,} signatures lues "
          f"sur un seul portefeuille")
    print(f"\n{'token':<12}{'A av/ap':>10}{'B av/ap':>10}{'C av/ap':>10}{'prebuy av':>12}"
          f"{'prebuy ap':>12}  change ?")
    for c in comp:
        a, b = c["avant"], c["apres"]
        print(f"{c['token']:<12}{a['A']:>5}/{b['A']:<4}{a['B']:>5}/{b['B']:<4}"
              f"{a['C_prive']:>5}/{b['C_prive']:<4}{a['prebuy']:>12}{b['prebuy']:>12}  "
              f"{'OUI' if c['signature_changee'] else 'non'}")
    print(f"\n  tokens dont une signature change : {res['n_tokens_avec_signature_changee']}"
          f"/{len(comp)}")
    print("  -> t8_apres_rattrapage.json")


if __name__ == "__main__":
    main()
