| regle d'entree      | n   | clusters | jamais declenchee | t entree median (s) | multiple median | IC95         | p25 / p75   | % multiple > 1 | PnL net median % | PnL net moyen % | IC95 moyenne (cluster) % | moyenne sans le meilleur token % |
|---------------------|-----|----------|-------------------|---------------------|-----------------|--------------|-------------|----------------|------------------|-----------------|--------------------------|----------------------------------|
| graduation (+120 s) | 196 | 20       | 0                 | 120                 | 0.81            | [0.61, 0.93] | 0.06 / 1.33 | 40.3           | -23.8            | -10.2           | [-21, +10]               | -13.8                            |
| retrace -20 %       | 181 | 21       | 32                | 150                 | 0.70            | [0.56, 0.91] | 0.04 / 1.27 | 38.1           | -33.7            | -15.6           | [-28, +4]                | -19.5                            |
| retrace -30 %       | 160 | 21       | 58                | 210                 | 0.64            | [0.53, 0.84] | 0.03 / 1.26 | 35.0           | -39.6            | -14.0           | [-34, +30]               | -24.2                            |
| retrace -40 %       | 135 | 18       | 84                | 270                 | 0.63            | [0.51, 0.84] | 0.03 / 1.20 | 33.3           | -40.5            | +16.6           | [-41, +58]               | -15.2                            |
| retrace -50 %       | 118 | 16       | 102               | 315                 | 0.67            | [0.46, 0.80] | 0.00 / 1.04 | 28.0           | -36.8            | +22.3           | [-49, +72]               | -14.1                            |
| retrace -60 %       | 86  | 14       | 134               | 270                 | 0.46            | [0.09, 0.73] | 0.00 / 0.97 | 23.3           | -57.0            | +23.9           | [-54, +89]               | -26.3                            |
| retrace -70 %       | 61  | 13       | 157               | 360                 | 0.16            | [0.00, 0.51] | 0.00 / 0.85 | 16.4           | -85.0            | +13.1           | [-68, +89]               | -58.0                            |


Source : `data/floor_capture_public.jsonl.gz` (645 fichiers, 289 captures exploitables). Sortie commune : conservation jusqu'a la fin exploitable de la capture (<= 20 min).
`multiple median` est BRUT (hors frais) ; `PnL net` retranche 5,8241 % aller-retour.
Toutes les regles sont live-safe : la decision prise sur un bucket de 30 s s'execute au bucket suivant, jamais au prix qui l'a declenchee.
**Aucune regle d'entree post-snipe n'atteint un multiple median de 1 sur cet horizon** ; la meilleure est `graduation (+120 s)` a 0.81x (IC95 [0.61, 0.93], n=196).
`jamais declenchee` = le token n'a pas offert le retracement demande pendant la capture ; ces tokens ne comptent dans aucune colonne.
**A ne pas surinterpreter** : la MOYENNE devient positive sur les retracements profonds (-40 % a -70 %). Ce n'est pas un edge. Deux controles le montrent, et ils sont dans le tableau : (a) l'IC95 de la moyenne, bootstrappe au niveau CLUSTER, traverse zero pour chacune de ces lignes ; (b) retirer LE SEUL meilleur token de l'echantillon fait repasser toutes ces moyennes en negatif. C'est une queue droite epaisse portee par une poignee de tokens, pas une esperance positive.

Regenerer : `python3 code/t4_entree_post_snipe_20min.py`
