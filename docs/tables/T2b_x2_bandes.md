| bande MC detectee | n   | MC median | ATH median | x2 % | IC95 %       | x2 devant soi % |
|-------------------|-----|-----------|------------|------|--------------|-----------------|
| 5k-20k            | 16  | 14 596    | 42 948     | 75.0 | [50.5, 89.8] | 37.5            |
| 20k-30k           | 108 | 26 813    | 59 217     | 55.6 | [46.2, 64.6] | 37.0            |
| 30k-40k           | 137 | 33 989    | 60 764     | 43.8 | [35.8, 52.2] | 32.8            |
| 40k-50k           | 296 | 45 614    | 82 022     | 44.3 | [38.7, 50.0] | 39.5            |
| 50k-65k           | 277 | 55 593    | 105 500    | 46.6 | [40.8, 52.5] | 42.2            |
| 65k-85k           | 121 | 72 792    | 136 869    | 47.9 | [39.2, 56.8] | 38.0            |
| 85k-100k          | 65  | 92 583    | 169 394    | 44.6 | [33.2, 56.7] | 36.9            |
| 100k-120k         | 58  | 109 339   | 207 671    | 46.6 | [34.3, 59.2] | 43.1            |
| 120k-300k         | 165 | 153 077   | 280 553    | 42.4 | [35.1, 50.1] | 40.6            |


n = 1243 tokens | 123 clusters | 20 jours UTC | socle B propre.
Ici le denominateur est le prix REELLEMENT observe a la detection. Le taux de x2 est quasi plat : les tokens qui apparaissent bas ont aussi un ATH bas.
Elasticite log10(ATH) ~ log10(mc), demeanee par jour : **b = 0.884** (n=1243). b < 1 => entrer plus haut degrade reellement le multiple.
Limite (relecture) : b publie sans SE/IC ; l'erreur de mesure sur le MC d'entree (errors-in-variables) tire la pente sous 1 ; et le taux de x2 quasi plat de ce panneau est en tension avec une lecture causale. Decomposition mecanique : mesuree. Claim economique : indicatif, NON ETABLI.
`x2 devant soi` = x2 ET ATH survenant >= 60 s apres la detection.

Regenerer : `python3 code/t2_x2_par_prix_entree.py`
