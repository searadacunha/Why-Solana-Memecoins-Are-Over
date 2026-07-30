| bande MC entree | n   | x2 %  | IC95 %        | x2 devant soi % | x3 % | ATH median USD |
|-----------------|-----|-------|---------------|-----------------|------|----------------|
| 5k-15k          | 8   | 100.0 | [67.6, 100.0] | 37.5            | 75.0 | 57 242         |
| 15k-20k         | 8   | 50.0  | [21.5, 78.5]  | 37.5            | 25.0 | 38 042         |
| 20k-25k         | 31  | 48.4  | [32.0, 65.2]  | 32.3            | 29.0 | 47 249         |
| 25k-30k         | 77  | 58.4  | [47.3, 68.8]  | 39.0            | 35.1 | 66 292         |
| 30k-40k         | 137 | 43.8  | [35.8, 52.2]  | 32.8            | 32.1 | 60 764         |
| 40k-50k         | 296 | 44.3  | [38.7, 50.0]  | 39.5            | 27.7 | 82 022         |
| 50k-65k         | 277 | 46.6  | [40.8, 52.5]  | 42.2            | 30.0 | 105 500        |
| 65k-85k         | 121 | 47.9  | [39.2, 56.8]  | 38.0            | 31.4 | 136 869        |
| 85k-100k        | 65  | 44.6  | [33.2, 56.7]  | 36.9            | 27.7 | 169 394        |
| 100k-120k       | 58  | 46.6  | [34.3, 59.2]  | 43.1            | 27.6 | 207 671        |
| 120k-300k       | 165 | 42.4  | [35.1, 50.1]  | 40.6            | 22.4 | 280 553        |


n = 1243 tokens | 123 clusters | 20 jours UTC | source socle B (fast-grad) propre.
`x2` = ATH pump.fun >= 2 x capitalisation d'entree. **Borne SUPERIEURE** de la chance de doubler : atteindre l'ATH n'est pas vendre a l'ATH.
`x2 devant soi` = idem + ATH survenant au moins 60 s APRES la detection (seule colonne correspondant a quelque chose d'atteignable).
Elasticite mesuree log10(ATH) ~ log10(mc), demeanee par jour : **b = 0.884** (n=1243). b < 1 => entrer plus haut degrade reellement le multiple ; ce n'est pas une tautologie parfaite.
Prix d'entree qui donnerait 90 % de x2  par interpolation lineaire entre les medianes de bande : **11 578 USD**.

Regenerer : `python3 code/t2_x2_par_prix_entree.py`
