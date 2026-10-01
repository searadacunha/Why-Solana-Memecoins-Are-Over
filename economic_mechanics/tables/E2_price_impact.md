# E2. Price impact of the creation slot (descriptive; read after every group and role was fixed)

Prices in SOL per token. The curve's initial price is 2.796e-08. Inside the creation slot the order of transactions is unknown, so the group's part of the jump is approximated by its share of the slot's SOL; exact attribution is not possible.

| group | split | jump over the creation slot (x) | P0 over initial (x) | share of the move to P0 done in the slot (log) | group share of the slot's SOL | max within 10 s / 30 s / 60 s / 5 min of the creation, over P0 |
|---|---|---|---|---|---|---|
| COORDINATED | TRAIN | 14.5 / 13.1 / 27.3 / 46.2 / 11.7 / 1.3e+05 (N 884) | 13.9 / 13 / 29.1 / 47.3 / 3.99 / 1.3e+05 (N 884) | 0.996 / 0.987 / 1.02 / 1.05 / 0.812 / 1.5 (N 884) | 0.988 / 0.948 / 0.999 / 1 / 0.869 / 1 (N 884) | 1.06 ; 1.12 ; 1.18 ; 1.34 |
| COORDINATED | VAL | 13.9 / 13 / 19.4 / 40.3 / 11.7 / 3.31e+04 (N 520) | 14.1 / 13.1 / 21.3 / 41 / 4.52 / 3.31e+04 (N 520) | 0.995 / 0.979 / 1.01 / 1.04 / 0.863 / 1.5 (N 520) | 0.988 / 0.944 / 0.998 / 0.999 / 0.866 / 1 (N 520) | 1.05 ; 1.12 ; 1.17 ; 1.33 |
| CONTROL | TRAIN | 13.4 / 12 / 14.7 / 16.3 / 11.7 / 3.31e+04 (N 131) | 13 / 12.2 / 13.8 / 16.2 / 4.41 / 3.31e+04 (N 131) | 1.01 / 0.975 / 1.06 / 1.11 / 0.439 / 1.5 (N 131) | 0.992 / 0.951 / 0.999 / 1 / 0.874 / 1 (N 131) | 1.15 ; 1.22 ; 1.31 ; 1.54 |
| CONTROL | VAL | 13.2 / 12.7 / 14.4 / 14.7 / 11.8 / 451 (N 122) | 12.6 / 11.5 / 13.6 / 14.4 / 4.35 / 453 (N 122) | 1.02 / 0.991 / 1.07 / 1.12 / 0.921 / 1.5 (N 122) | 0.937 / 0.923 / 0.969 / 0.999 / 0.883 / 1 (N 122) | 1.16 ; 1.22 ; 1.28 ; 1.58 |
| STRICT CONTROL | TRAIN | 13.2 / 11.9 / 13.8 / 14.7 / 11.7 / 42.8 (N 28) | 12.5 / 10.8 / 13.9 / 14.7 / 4.41 / 371 (N 28) | 1 / 0.972 / 1.08 / 1.25 / 0.439 / 1.5 (N 28) | 0.992 / 0.955 / 0.999 / 1 / 0.909 / 1 (N 28) | 1.24 ; 1.28 ; 1.35 ; 1.65 |
| STRICT CONTROL | VAL | 13.4 / 12.8 / 14.7 / 14.7 / 12.1 / 42.8 (N 25) | 11.4 / 10.4 / 11.8 / 14.3 / 5.64 / 39.9 (N 25) | 1.07 / 1.04 / 1.12 / 1.31 / 0.964 / 1.5 (N 25) | 0.919 / 0.902 / 0.957 / 0.985 / 0.89 / 0.999 (N 25) | 1.26 ; 1.26 ; 1.33 ; 1.77 |
