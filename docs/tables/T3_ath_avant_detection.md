| bande MC a la detection | n    | ATH deja passe % | ATH < +60 s % | IC95 %       | ATH < +120 s % | delai median ATH (min) |
|-------------------------|------|------------------|---------------|--------------|----------------|------------------------|
| 5k-20k                  | 16   | 43.8             | 62.5          | [38.6, 81.5] | 62.5           | 0.1                    |
| 20k-30k                 | 108  | 23.1             | 55.6          | [46.2, 64.6] | 60.2           | 0.5                    |
| 30k-40k                 | 137  | 27.7             | 60.6          | [52.2, 68.4] | 65.7           | 0.3                    |
| 40k-50k                 | 296  | 18.9             | 44.6          | [39.0, 50.3] | 54.4           | 1.7                    |
| 50k-65k                 | 277  | 26.4             | 46.6          | [40.8, 52.5] | 51.6           | 1.6                    |
| 65k-85k                 | 121  | 26.4             | 52.1          | [43.2, 60.8] | 58.7           | 0.9                    |
| 85k-120k                | 123  | 14.6             | 31.7          | [24.1, 40.4] | 35.8           | 6.7                    |
| 120k-300k               | 165  | 9.7              | 17.6          | [12.5, 24.1] | 23.0           | 36.1                   |
| --- < 20k (agrege)      | 16   | 43.8             | 62.5          | [38.6, 81.5] | 62.5           | 0.1                    |
| --- toute la population | 1243 | 21.3             | 43.8          | [41.1, 46.6] | 50.0           | 2.0                    |


n = 1243 tokens | 123 clusters | 20 jours UTC | socle B propre.
`detect_ts` = premiere visibilite exterieure (token `complete` vu <= 12 s apres creation). C'est une borne BASSE de la latence d'un acheteur humain.
Un delai median NEGATIF signifie que, dans la bande, le token typique a deja fait son sommet avant d'exister pour l'observateur.
Limite : `o_ath_ts` (API pump.fun) et `detect_ts` (horloge locale) peuvent differer de quelques secondes ; les trois seuils sont publies pour cela.

Regenerer : `python3 code/t3_ath_avant_detection.py`
