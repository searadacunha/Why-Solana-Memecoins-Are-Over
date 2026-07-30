| politique de sortie | n   | mediane % | IC95 mediane % | moyenne % | IC95 moyenne (cluster) % | % gagnants | % non remplies | mediane excl % | clusters + | jours med>0 |
|---------------------|-----|-----------|----------------|-----------|--------------------------|------------|----------------|----------------|------------|-------------|
| time_1m             | 196 | -5.4      | [-8.6, -2.6]   | -8.6      | [-12.2, -1.4]            | 35.7       | 3.6            | -5.2           | 8/20       | 1/6         |
| time_3m             | 196 | -8.7      | [-13.5, -3.2]  | -9.5      | [-13.5, -2.2]            | 40.8       | 5.6            | -6.2           | 10/20      | 0/6         |
| time_5m             | 196 | -11.7     | [-21.0, -5.6]  | -10.1     | [-17.6, -4.0]            | 40.3       | 10.2           | -8.0           | 8/20       | 1/6         |
| time_10m            | 196 | -13.3     | [-26.0, -4.4]  | -10.3     | [-20.7, +8.2]            | 38.8       | 17.3           | -1.9           | 8/20       | 0/6         |
| time_20m            | 196 | -23.8     | [-42.1, -12.7] | -10.2     | [-20.7, +10.2]           | 37.8       | 19.4           | -5.7           | 7/20       | 1/6         |
| trail_20            | 196 | -17.8     | [-22.6, -14.3] | -12.1     | [-19.8, -1.4]            | 32.7       | 6.1            | -16.3          | 9/20       | 0/6         |
| trail_30            | 196 | -24.2     | [-29.5, -14.8] | -10.9     | [-16.4, -4.5]            | 33.7       | 5.6            | -18.7          | 6/20       | 1/6         |
| trail_40            | 196 | -26.8     | [-36.6, -17.4] | -12.0     | [-18.7, -1.7]            | 31.6       | 6.1            | -21.3          | 6/20       | 1/6         |
| tp30                | 196 | +22.4     | [+0.5, +22.4]  | -16.4     | [-22.6, -6.3]            | 56.6       | 15.3           | +22.4          | 9/20       | 5/6         |
| tp30_sl35           | 196 | +11.2     | [-17.4, +22.4] | -14.2     | [-18.4, -5.6]            | 53.1       | 6.6            | +22.4          | 10/20      | 5/6         |
| tp50                | 196 | +3.3      | [-17.5, +27.1] | -12.9     | [-19.9, +0.5]            | 51.5       | 16.8           | +31.5          | 9/20       | 4/6         |
| tp50_sl35           | 196 | -15.7     | [-29.9, +12.3] | -11.3     | [-16.3, +0.1]            | 46.9       | 6.6            | +0.2           | 9/20       | 2/6         |
| tp2x                | 196 | -17.4     | [-30.5, -0.7]  | -10.9     | [-19.5, +5.2]            | 42.9       | 19.4           | +5.4           | 8/20       | 1/6         |
| tp2x_sl35           | 196 | -29.5     | [-37.4, -17.0] | -10.1     | [-16.2, +1.8]            | 37.8       | 6.6            | -18.7          | 9/20       | 1/6         |
| hold_t_safe         | 196 | -23.8     | [-42.1, -12.7] | -10.2     | [-20.6, +10.2]           | 37.8       | 18.9           | -7.9           | 7/20       | 1/6         |


n = 196 tokens | 20 clusters | 6 jours UTC | entree a t0+120 s, AUCUN filtre d'entree.
Source : `data/floor_capture_public.jsonl.gz` (645 fichiers, 289 captures exploitables, rejets {'aucun_buy': 1, 'capture_vide': 352, 'span_swaps_lt_2min': 3}).
Couts : 1 % de frais + 2 % de slippage adverse par jambe = **5,8241 % aller-retour**, deja retranches.
`mediane excl` = meme calcul en JETANT les sorties non remplies (convention optimiste, publiee pour montrer ce qu'elle fabrique).
**Moyenne negative sur 15/15 politiques.** Mediane negative sur 12/15 (9/10 sur la grille canonique du 28/07).
**Aucune politique n'est positive a la fois en mediane et en moyenne (0/15).** Les rares medianes positives sont des politiques a take-profit serre : elles gagnent souvent un peu et perdent rarement beaucoup, donc leur ESPERANCE est la pire du tableau (tp30 : mediane +22 %, moyenne -16 %).
Aucune politique n'a un IC95 de moyenne (bootstrap au niveau CLUSTER) entierement au-dessus de zero : 0/15.
Moyenne des moyennes sur les 15 politiques : **-11.3 %** par aller-retour.
Aucune correction de multiplicite n'est necessaire ici : le resultat est NEGATIF partout, et balayer plus de politiques ne peut que rendre un resultat negatif plus difficile a obtenir par hasard.

Regenerer : `python3 code/t1_base_rate_sorties.py`
