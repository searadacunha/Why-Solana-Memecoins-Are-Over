# D3. Actor or premium? (primary label, fitted on TRAIN, measured on VALIDATION)

VALIDATION base 26.4 % (N 606). Ridge logistic, penalty chosen on VALIDATION among [1.0, 10.0, 100.0, 1000.0].

| model | features | ROC-AUC | PR-AUC | top 10 % | top 20 % |
|---|---:|---:|---:|---|---|
| A actor | 1 | 0.632 | 0.324 | 32.8 % (20/61) [22.3-45.3] | 32.2 % (39/121) [24.6-41.0] |
| B premium | 1 | 0.636 | 0.329 | 32.8 % (20/61) [22.3-45.3] | 31.4 % (38/121) [23.8-40.1] |
| C actor + premium | 2 | 0.637 | 0.330 | 32.8 % (20/61) [22.3-45.3] | 31.4 % (38/121) [23.8-40.1] |
| D on-chain without actor | 142 | 0.673 | 0.407 | 50.8 % (31/61) [38.6-62.9] | 45.5 % (55/121) [36.9-54.3] |
| E all + actor | 143 | 0.704 | 0.433 | 47.5 % (29/61) [35.5-59.8] | 50.4 % (61/121) [41.6-59.2] |
| F all + actor + premium | 144 | 0.674 | 0.424 | 54.1 % (33/61) [41.7-66.0] | 47.1 % (57/121) [38.4-56.0] |

Paired AUC differences on VALIDATION (95 % cluster-bootstrap CI):

- C actor + premium minus B premium: +0.001 [-0.009, +0.008]
- C actor + premium minus A actor: +0.005 [-0.034, +0.046]
- E all + actor minus D on-chain without actor: +0.031 [+0.006, +0.069]
- F all + actor + premium minus C actor + premium: +0.037 [-0.056, +0.094]
- D on-chain without actor minus B premium: +0.037 [-0.055, +0.093]

Overlap of actor and premium (all alerts with both): {('grouped', '>= x4.5'): 392, ('single', '< x4.5'): 1233, ('grouped', '< x4.5'): 15, ('single', '>= x4.5'): 6}. A cell with fewer than 20 alerts means the two cannot be separated in that region.
