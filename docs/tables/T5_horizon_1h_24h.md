| horizon | n avec bougie | sans bougie | multiple median | IC95         | p25 / p75   | % > 1 | high median | median population entiere |
|---------|---------------|-------------|-----------------|--------------|-------------|-------|-------------|---------------------------|
| +1 h    | 189           | 2 (1 %)     | 0.48            | [0.38, 0.61] | 0.03 / 0.94 | 18.5  | 0.86        | 0.47                      |
| +2 h    | 185           | 6 (3 %)     | 0.43            | [0.29, 0.54] | 0.03 / 0.92 | 18.4  | 0.56        | 0.41                      |
| +4 h    | 179           | 12 (6 %)    | 0.38            | [0.26, 0.49] | 0.02 / 0.82 | 15.6  | 0.43        | 0.30                      |
| +24 h   | 144           | 47 (25 %)   | 0.20            | [0.05, 0.29] | 0.02 / 0.60 | 12.5  | 0.22        | 0.03                      |


n = 191 tokens | 27 clusters. Achat au prix robuste des 120 dernieres secondes de la capture (~t0+20 min), converti en USD ; vente au `close` de la bougie horaire la plus proche (tolerance 90 min).
`high median` = mediane du plus haut de la bougie d'echeance : borne OPTIMISTE (elle suppose de vendre au plus haut de l'heure).
`median population entiere` compte 0,00x les tokens qui n'ont plus AUCUNE bougie a l'echeance, c'est-a-dire plus aucun echange : c'est la convention honnete pour un actif qu'on ne peut plus vendre.
Controle d'unites (prix GT en USD / prix de swap en SOL) / (SOL en USD) = **0.850** en mediane sur n=277 tokens. Proche de 1 : la conversion SOL->USD est correcte. Sans cette conversion, tous les multiples de cette table seraient multiplies par ~76.

Prerequis : `python3 code/fetch_sol_usd.py` puis `python3 code/fetch_gt_ohlcv.py`.
Regenerer : `python3 code/t5_horizon_1h_24h.py`
