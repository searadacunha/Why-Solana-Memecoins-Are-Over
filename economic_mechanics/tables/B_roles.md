# B. Role graph and architectures

Primary architecture per launch (C deployer funds 2+ snipers; A a funder of 2+ snipers linked to the deployer; D several funders of 2+ snipers or a common source; B a common funder, no deployer link; E no common funding; UNRESOLVED a sniper's funder unknown). Flags can combine; the primary is the first of C, A, D, B, E.

| group | split | launches | C | A | D | B | E | UNRESOLVED |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| COORDINATED | TRAIN | 884 | 22 (2 %) | 237 (27 %) | 7 (1 %) | 521 (59 %) | 72 (8 %) | 25 (3 %) |
| COORDINATED | VAL | 520 | 3 (1 %) | 146 (28 %) | 2 (0 %) | 305 (59 %) | 41 (8 %) | 23 (4 %) |
| CONTROL | TRAIN | 131 | 0 (0 %) | 0 (0 %) | 2 (2 %) | 0 (0 %) | 78 (60 %) | 51 (39 %) |
| CONTROL | VAL | 122 | 0 (0 %) | 0 (0 %) | 0 (0 %) | 0 (0 %) | 72 (59 %) | 50 (41 %) |
| STRICT CONTROL | TRAIN | 28 | 0 (0 %) | 0 (0 %) | 0 (0 %) | 0 (0 %) | 12 (43 %) | 16 (57 %) |
| STRICT CONTROL | VAL | 25 | 0 (0 %) | 0 (0 %) | 0 (0 %) | 0 (0 %) | 6 (24 %) | 19 (76 %) |

Sensitivity, all launches: last funders, genesis funders, known non-hub last funders only.

| architecture | last funders | genesis funders | strict |
|---|---:|---:|---:|
| C | 25 | 0 | 5 |
| A | 383 | 359 | 359 |
| D | 11 | 6 | 4 |
| B | 826 | 16 | 80 |
| E | 263 | 1006 | 1060 |
| UNRESOLVED | 149 | 270 | 149 |
| OTHER | 0 | 0 | 0 |

## Representative launches (the first TRAIN launch of each architecture; addresses shortened)

### C, launch 3BLohb... (2026-08-23 14:12:53), deployer 4fVk3W...

| sniper | ticket SOL | tokens | funded by | funding SOL | funding s before buy | funding tx | hub status | first exit | tokens gone by +30 s |
|---|---:|---:|---|---:|---:|---|---|---|---:|
| H4RHey... | 21.28 | 1e+08 | 4fVk3W... (deployer) | 21.546 | 11 | 4dpJz1... | unknown | n/a | 0 % |
| Hat68d... | 20.97 | 6.24e+07 | 4fVk3W... (deployer) | 21.233 | 11 | 4dpJz1... | unknown | n/a | 0 % |
| AJKg3Q... | 21.42 | 4.47e+08 | 4fVk3W... (deployer) | 21.691 | 11 | 4dpJz1... | unknown | n/a | 0 % |
| AUBYLL... | 21.34 | 1.84e+08 | 4fVk3W... (deployer) | 21.606 | 11 | 4dpJz1... | unknown | n/a | 0 % |

### A, launch 5AKiLB... (2026-08-21 17:35:43), deployer BLi6wC...

| sniper | ticket SOL | tokens | funded by | funding SOL | funding s before buy | funding tx | hub status | first exit | tokens gone by +30 s |
|---|---:|---:|---|---:|---:|---|---|---|---:|
| D95a5Z... | 24.69 | 1.36e+08 | FZNT7J... | 25.352 | 1 | 3ihPoW... | non-hub | n/a | 0 % |
| E9rM43... | 25.25 | 7.88e+07 | FZNT7J... | 30.402 | 1 | 9KeHmB... | non-hub | n/a | 0 % |
| CasvXK... | 9.88 | 2.58e+08 | FZNT7J... | 10.202 | 1 | rqRDMA... | non-hub | n/a | 0 % |
| 6UTS7a... | 24.69 | 3.03e+08 | FZNT7J... | 25.352 | 1 | 32Zaca... | non-hub | sell after 36 s | 3 % |

### D, launch 6UNv1w... (2026-09-05 14:38:13), deployer FwVeE1...

| sniper | ticket SOL | tokens | funded by | funding SOL | funding s before buy | funding tx | hub status | first exit | tokens gone by +30 s |
|---|---:|---:|---|---:|---:|---|---|---|---:|
| E3Aiah... | 20.01 | 6.26e+07 | CsfX5H... | 25.000 | 469 | u1vjT5... | unknown | transfer after 4 s | 100 % |
| 4YSRZK... | 20.95 | 1.03e+08 | CsfX5H... | 25.000 | 470 | 286HNv... | unknown | transfer after 4 s | 100 % |
| Fc1n98... | 19.94 | 1.77e+08 | F4fbNW... | 25.000 | 505 | 5YL3RG... | unknown | transfer after 4 s | 100 % |
| 6roByc... | 20.93 | 4.4e+08 | F4fbNW... | 25.000 | 505 | 4s5D39... | unknown | transfer after 4 s | 100 % |

### B, launch 57UEGd... (2026-08-21 20:13:11), deployer 2GU5af...

| sniper | ticket SOL | tokens | funded by | funding SOL | funding s before buy | funding tx | hub status | first exit | tokens gone by +30 s |
|---|---:|---:|---|---:|---:|---|---|---|---:|
| 2wHHnA... | 20.59 | 6.25e+07 | Atq5fT... | 25.000 | 226 | 5Cz9J8... | unknown | n/a | 0 % |
| 2AqFJz... | 20.75 | 9.89e+07 | Atq5fT... | 25.000 | 226 | 2WtYS8... | unknown | sell after 4 s | 100 % |
| 9yxmCN... | 21.02 | 1.82e+08 | Atq5fT... | 25.000 | 226 | p6Yhtg... | unknown | n/a | 0 % |
| 22vL22... | 21.23 | 4.4e+08 | Atq5fT... | 25.000 | 226 | 42EwAX... | unknown | n/a | 0 % |

### E, launch 9KDiVd... (2026-08-21 18:59:34), deployer 6ji5tt...

| sniper | ticket SOL | tokens | funded by | funding SOL | funding s before buy | funding tx | hub status | first exit | tokens gone by +30 s |
|---|---:|---:|---|---:|---:|---|---|---|---:|
| HBLT57... | 29.41 | 1.81e+08 | FyunA6... | 3.305 | 1304 | 3DZ3qP... | unknown | sell after 1 s | 100 % |
| 866LXb... | 26.49 | 8.38e+07 | 9aNmsz... | 2.977 | 1367 | 4GCUHA... | unknown | sell after 2 s | 100 % |
| GLvqY7... | 6.42 | 1.86e+08 | 3ueXBk... | 0.740 | 1324 | 2srzwJ... | unknown | sell after 0 s | 100 % |
| 7HA5cb... | 8.66 | 1.67e+08 | FVE8vZ... | 0.992 | 1365 | 2iKUfz... | unknown | sell after 10 s | 100 % |
| HepNSG... | 13.74 | 1.65e+08 | H7zHGq... | 1.558 | 1300 | UKcRVi... | unknown | sell after 0 s | 100 % |

