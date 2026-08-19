#!/usr/bin/env python3
"""Etape 6 : un bailleur commun "prive" l'est-il vraiment ?

La signature C (un meme bailleur finance >= 2 premiers acheteurs) est la seule que le detecteur ait
trouvee sur la cible OPTIMUS, et aussi la seule trouvee sur le temoin HLGOOFY. Tout repose donc sur
un point : ces bailleurs sont-ils des acteurs prives, ou de l'infrastructure absente de la liste
`KNOWN` ? Un depot d'echange mal etiquete produirait exactement le meme motif sans aucune
coordination.

Mesure, symetriquement sur la cible et sur le temoin : volume total de transactions, age, nombre de
destinataires distincts, montant de sortie le plus repete. Une adresse a des centaines de milliers
de transactions et des milliers de destinataires est de l'infrastructure, quel que soit son
etiquetage. Une adresse a quelques dizaines de sorties vers quelques destinataires est un acteur.

Ecrit t6_profil_bailleurs.json a cote du script. Les adresses viennent de DEFAUT, ou de --addresses.

Piege : la pagination des signatures est plafonnee a 120 pages et seules 6 pages de transactions
parsees sont echantillonnees. Le profil est donc une borne inferieure, et `genese_atteinte` le dit.
"""
from __future__ import annotations
import argparse, json, os
from collections import Counter
import lib_trace as L

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAUT = [
    ("HLGOOFY (TEMOIN)", "12hHGUFAC2o3QaoNqgfr9tFe16v2dRNGLtzffoFScKcW"),
    ("OPTIMUS (CIBLE)", "A77HErqtfN1hLLpvZ9pCtu66FEtM8BveoaKbbMoZ4RiR"),
    ("ODIN (CAS PROUVE)", "HRS6JqXcFgWrWxaBPjhnThQiWmUMkE3GrYHWR86tbFqR"),
]


def profil(addr, pages_parsees=6):
    """Profil d'une adresse. La pagination de signatures est bornee, et le dit."""
    sigs, genesis, npages = L.all_signatures(addr, max_pages=120, label=addr[:8], verbose=False)
    out_counts, dests, entrees = Counter(), Counter(), Counter()
    before, n_tx = None, 0
    for _ in range(pages_parsees):
        batch = L.helius_parsed(addr, before=before, limit=100)
        if not batch:
            break
        n_tx += len(batch)
        for tx in batch:
            d = L.balance_deltas(tx)
            mine = d.get(addr, 0.0)
            if mine < -0.001:
                for k, v in d.items():
                    if k != addr and v > 0.001 and k not in L.SYSTEM_ACCOUNTS:
                        dests[k] += 1
                        out_counts[round(v, 9)] += 1
            elif mine > 0.001:
                for k, v in d.items():
                    if k != addr and v < -0.001 and k not in L.SYSTEM_ACCOUNTS:
                        entrees[k] += 1
        before = batch[-1].get("signature")
    return {
        "adresse": addr,
        "n_signatures_vues": len(sigs),
        "pages_signatures": npages,
        "genese_atteinte": genesis,
        "plus_ancienne_utc": L.utc(sigs[0].get("blockTime")) if sigs else None,
        "plus_recente_utc": L.utc(sigs[-1].get("blockTime")) if sigs else None,
        "n_tx_parsees_inspectees": n_tx,
        "n_destinataires_distincts_sur_echantillon": len(dests),
        "n_sources_distinctes_sur_echantillon": len(entrees),
        "montants_de_sortie_les_plus_repetes": out_counts.most_common(8),
        "etiquette_connue": L.KNOWN.get(addr),
        "lecture": ("INFRASTRUCTURE probable (volume et eventail de destinataires trop larges)"
                    if len(sigs) > 50_000 or len(dests) > 200 else
                    "ACTEUR PRIVE probable (volume et eventail compatibles avec un distributeur)"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addresses", nargs="*")
    a = ap.parse_args()
    cibles = [(f"ad-hoc", x) for x in a.addresses] if a.addresses else DEFAUT
    res = []
    for nom, ad in cibles:
        print(f"\n=== {nom} : {ad}", flush=True)
        p = profil(ad)
        p["contexte"] = nom
        res.append(p)
        for k in ("n_signatures_vues", "pages_signatures", "genese_atteinte",
                  "plus_ancienne_utc", "plus_recente_utc",
                  "n_destinataires_distincts_sur_echantillon",
                  "n_sources_distinctes_sur_echantillon", "etiquette_connue", "lecture"):
            print(f"   {k:<44} {p[k]}", flush=True)
        print(f"   montants de sortie repetes                   {p['montants_de_sortie_les_plus_repetes'][:5]}",
              flush=True)
    json.dump(res, open(os.path.join(HERE, "t6_profil_bailleurs.json"), "w"), indent=1)
    print("\n  -> t6_profil_bailleurs.json")


if __name__ == "__main__":
    main()
