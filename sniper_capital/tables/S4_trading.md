# S4. Trading simulation (rules whose VALIDATION lower bound is above the base)

Net mean per trade at $500, cost model of post_detection_edge, 95 % cluster-bootstrap CI; the same exits on every alert as the reference. Cells with fewer than 10 trades are not estimates.

## 4 time since last funding, TRAIN: `102 < age_med <= 646` (476 of 1015 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 435 trades | TP 51 % | net -16.9 % [-21.6, -10.7] | 938 trades | TP 40 % | net -16.5 % [-20.0, -13.3] |
| 0 s | TP 1.5x, 15 min | 410 trades | TP 58 % | net -24.6 % [-30.5, -17.7] | 890 trades | TP 51 % | net -21.2 % [-25.4, -16.9] |
| 0 s | TP 1.5x, 30 min | 388 trades | TP 58 % | net -24.9 % [-30.9, -17.8] | 844 trades | TP 55 % | net -21.8 % [-26.3, -17.4] |
| 0 s | TP 1.5x, 60 min | 349 trades | TP 59 % | net -23.7 % [-30.6, -17.2] | 763 trades | TP 58 % | net -22.0 % [-27.3, -17.8] |
| 0 s | TP 2x, 5 min | 435 trades | TP 26 % | net -14.8 % [-22.9, -4.4] | 938 trades | TP 19 % | net -15.3 % [-19.5, -10.8] |
| 0 s | TP 2x, 15 min | 410 trades | TP 38 % | net -31.5 % [-39.6, -20.5] | 890 trades | TP 30 % | net -27.1 % [-32.7, -20.3] |
| 0 s | TP 2x, 30 min | 388 trades | TP 39 % | net -32.4 % [-40.3, -22.1] | 844 trades | TP 34 % | net -29.9 % [-35.6, -22.8] |
| 0 s | TP 2x, 60 min | 349 trades | TP 40 % | net -32.3 % [-40.4, -22.0] | 763 trades | TP 35 % | net -33.4 % [-39.2, -26.7] |
| 0 s | TP 3x, 5 min | 435 trades | TP 4 % | net -13.8 % [-23.3, -1.1] | 938 trades | TP 3 % | net -15.4 % [-19.9, -10.1] |
| 0 s | TP 3x, 15 min | 410 trades | TP 10 % | net -55.1 % [-62.8, -44.7] | 890 trades | TP 9 % | net -42.5 % [-49.6, -32.8] |
| 0 s | TP 3x, 30 min | 388 trades | TP 13 % | net -61.2 % [-69.8, -50.3] | 844 trades | TP 12 % | net -49.3 % [-57.2, -38.3] |
| 0 s | TP 3x, 60 min | 349 trades | TP 14 % | net -63.8 % [-73.0, -52.9] | 763 trades | TP 14 % | net -55.4 % [-63.2, -45.5] |
| 5 s | TP 1.5x, 5 min | 373 trades | TP 49 % | net -17.6 % [-22.7, -10.1] | 797 trades | TP 39 % | net -16.2 % [-20.0, -12.8] |
| 5 s | TP 1.5x, 15 min | 348 trades | TP 56 % | net -26.7 % [-32.2, -19.8] | 751 trades | TP 50 % | net -22.5 % [-27.0, -18.0] |
| 5 s | TP 1.5x, 30 min | 326 trades | TP 56 % | net -27.7 % [-33.7, -20.2] | 707 trades | TP 54 % | net -23.2 % [-28.3, -18.7] |
| 5 s | TP 1.5x, 60 min | 288 trades | TP 57 % | net -26.7 % [-33.4, -19.9] | 631 trades | TP 56 % | net -23.9 % [-29.4, -19.3] |
| 5 s | TP 2x, 5 min | 373 trades | TP 25 % | net -15.4 % [-23.8, -3.3] | 797 trades | TP 20 % | net -14.1 % [-18.8, -9.7] |
| 5 s | TP 2x, 15 min | 348 trades | TP 36 % | net -35.1 % [-43.8, -22.2] | 751 trades | TP 29 % | net -28.7 % [-34.6, -21.9] |
| 5 s | TP 2x, 30 min | 326 trades | TP 38 % | net -35.4 % [-44.7, -22.0] | 707 trades | TP 34 % | net -30.7 % [-37.5, -23.8] |
| 5 s | TP 2x, 60 min | 288 trades | TP 39 % | net -34.0 % [-43.3, -22.6] | 631 trades | TP 36 % | net -33.2 % [-40.7, -26.6] |
| 5 s | TP 3x, 5 min | 373 trades | TP 5 % | net -14.2 % [-24.0, +0.2] | 797 trades | TP 3 % | net -14.8 % [-19.6, -8.9] |
| 5 s | TP 3x, 15 min | 348 trades | TP 10 % | net -58.8 % [-67.9, -47.7] | 751 trades | TP 8 % | net -46.0 % [-52.5, -37.3] |
| 5 s | TP 3x, 30 min | 326 trades | TP 13 % | net -65.2 % [-75.2, -53.2] | 707 trades | TP 11 % | net -53.5 % [-60.9, -43.7] |
| 5 s | TP 3x, 60 min | 288 trades | TP 13 % | net -66.3 % [-77.7, -53.4] | 631 trades | TP 13 % | net -58.8 % [-66.6, -50.6] |
| 10 s | TP 1.5x, 5 min | 372 trades | TP 50 % | net -18.5 % [-24.3, -10.0] | 794 trades | TP 38 % | net -17.9 % [-21.3, -14.2] |
| 10 s | TP 1.5x, 15 min | 348 trades | TP 55 % | net -27.9 % [-34.3, -19.3] | 749 trades | TP 50 % | net -23.2 % [-27.5, -18.1] |
| 10 s | TP 1.5x, 30 min | 326 trades | TP 55 % | net -29.1 % [-35.8, -19.7] | 707 trades | TP 53 % | net -24.5 % [-29.2, -19.5] |
| 10 s | TP 1.5x, 60 min | 288 trades | TP 55 % | net -28.5 % [-35.5, -18.7] | 630 trades | TP 55 % | net -25.2 % [-30.3, -20.0] |
| 10 s | TP 2x, 5 min | 372 trades | TP 24 % | net -16.3 % [-24.3, -4.2] | 794 trades | TP 19 % | net -16.0 % [-20.6, -11.6] |
| 10 s | TP 2x, 15 min | 348 trades | TP 36 % | net -34.5 % [-42.8, -22.3] | 749 trades | TP 29 % | net -28.9 % [-34.4, -22.3] |
| 10 s | TP 2x, 30 min | 326 trades | TP 38 % | net -35.3 % [-44.2, -23.7] | 707 trades | TP 34 % | net -31.5 % [-37.7, -24.4] |
| 10 s | TP 2x, 60 min | 288 trades | TP 38 % | net -35.3 % [-45.2, -23.6] | 630 trades | TP 35 % | net -34.8 % [-40.8, -27.7] |
| 10 s | TP 3x, 5 min | 372 trades | TP 6 % | net -12.8 % [-22.4, +1.8] | 794 trades | TP 4 % | net -15.1 % [-19.8, -9.3] |
| 10 s | TP 3x, 15 min | 348 trades | TP 12 % | net -53.6 % [-63.7, -40.6] | 749 trades | TP 10 % | net -43.1 % [-50.0, -33.7] |
| 10 s | TP 3x, 30 min | 326 trades | TP 15 % | net -60.4 % [-71.1, -47.7] | 707 trades | TP 12 % | net -50.1 % [-57.7, -39.7] |
| 10 s | TP 3x, 60 min | 288 trades | TP 16 % | net -59.5 % [-71.4, -46.1] | 630 trades | TP 15 % | net -53.6 % [-61.3, -44.1] |
| 20 s | TP 1.5x, 5 min | 376 trades | TP 47 % | net -21.6 % [-27.0, -13.6] | 811 trades | TP 35 % | net -19.9 % [-23.7, -16.2] |
| 20 s | TP 1.5x, 15 min | 354 trades | TP 52 % | net -31.9 % [-38.0, -23.7] | 765 trades | TP 47 % | net -26.4 % [-30.7, -21.6] |
| 20 s | TP 1.5x, 30 min | 331 trades | TP 52 % | net -32.9 % [-39.6, -24.4] | 721 trades | TP 50 % | net -28.0 % [-32.5, -23.2] |
| 20 s | TP 1.5x, 60 min | 294 trades | TP 52 % | net -32.6 % [-39.2, -24.5] | 645 trades | TP 52 % | net -28.9 % [-33.9, -24.3] |
| 20 s | TP 2x, 5 min | 376 trades | TP 23 % | net -19.6 % [-27.7, -7.5] | 811 trades | TP 17 % | net -18.6 % [-22.9, -14.0] |
| 20 s | TP 2x, 15 min | 354 trades | TP 33 % | net -38.1 % [-46.5, -25.8] | 765 trades | TP 27 % | net -32.2 % [-37.5, -25.2] |
| 20 s | TP 2x, 30 min | 331 trades | TP 36 % | net -38.6 % [-47.8, -27.2] | 721 trades | TP 31 % | net -34.5 % [-40.8, -27.3] |
| 20 s | TP 2x, 60 min | 294 trades | TP 36 % | net -38.9 % [-48.4, -28.7] | 645 trades | TP 33 % | net -37.0 % [-44.2, -30.7] |
| 20 s | TP 3x, 5 min | 376 trades | TP 6 % | net -17.0 % [-26.4, -2.7] | 811 trades | TP 4 % | net -18.1 % [-23.0, -12.1] |
| 20 s | TP 3x, 15 min | 354 trades | TP 12 % | net -53.2 % [-63.7, -41.5] | 765 trades | TP 9 % | net -43.1 % [-50.5, -34.4] |
| 20 s | TP 3x, 30 min | 331 trades | TP 15 % | net -59.4 % [-70.8, -47.3] | 721 trades | TP 12 % | net -49.3 % [-56.7, -38.9] |
| 20 s | TP 3x, 60 min | 294 trades | TP 15 % | net -60.8 % [-72.6, -49.5] | 645 trades | TP 14 % | net -54.2 % [-62.4, -45.6] |
| 30 s | TP 1.5x, 5 min | 375 trades | TP 46 % | net -23.2 % [-29.1, -14.3] | 806 trades | TP 35 % | net -21.3 % [-25.1, -17.7] |
| 30 s | TP 1.5x, 15 min | 355 trades | TP 52 % | net -31.1 % [-37.7, -22.0] | 764 trades | TP 46 % | net -26.7 % [-31.1, -21.6] |
| 30 s | TP 1.5x, 30 min | 332 trades | TP 52 % | net -31.8 % [-38.8, -22.4] | 721 trades | TP 50 % | net -28.1 % [-33.4, -22.7] |
| 30 s | TP 1.5x, 60 min | 294 trades | TP 53 % | net -31.3 % [-38.8, -21.8] | 644 trades | TP 52 % | net -29.6 % [-34.9, -24.1] |
| 30 s | TP 2x, 5 min | 375 trades | TP 19 % | net -23.4 % [-30.6, -13.0] | 806 trades | TP 15 % | net -21.2 % [-25.5, -16.8] |
| 30 s | TP 2x, 15 min | 355 trades | TP 28 % | net -45.7 % [-54.1, -35.9] | 764 trades | TP 24 % | net -36.2 % [-42.4, -30.2] |
| 30 s | TP 2x, 30 min | 332 trades | TP 30 % | net -46.8 % [-56.1, -37.7] | 721 trades | TP 30 % | net -38.2 % [-45.4, -31.4] |
| 30 s | TP 2x, 60 min | 294 trades | TP 31 % | net -47.5 % [-58.2, -38.8] | 644 trades | TP 31 % | net -41.7 % [-48.9, -35.8] |
| 30 s | TP 3x, 5 min | 375 trades | TP 5 % | net -21.9 % [-30.4, -8.8] | 806 trades | TP 3 % | net -22.1 % [-27.8, -16.1] |
| 30 s | TP 3x, 15 min | 355 trades | TP 10 % | net -61.7 % [-72.8, -50.0] | 764 trades | TP 7 % | net -48.9 % [-56.6, -38.7] |
| 30 s | TP 3x, 30 min | 332 trades | TP 12 % | net -67.0 % [-78.0, -56.1] | 721 trades | TP 9 % | net -55.5 % [-63.4, -45.2] |
| 30 s | TP 3x, 60 min | 294 trades | TP 12 % | net -69.4 % [-81.5, -58.9] | 644 trades | TP 11 % | net -62.0 % [-70.0, -52.8] |

Sizes, 10 s delay, TP 2x within 15 min: $100 348 trades | TP 36 % | net -27.1 % [-36.5, -13.4]; $500 348 trades | TP 36 % | net -34.5 % [-42.8, -22.3]; $1000 348 trades | TP 36 % | net -42.3 % [-49.7, -31.6].

## 4 time since last funding, VAL: `102 < age_med <= 646` (279 of 642 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 271 trades | TP 51 % | net -17.7 % [-24.3, -11.7] | 625 trades | TP 42 % | net -20.5 % [-24.9, -16.4] |
| 0 s | TP 1.5x, 15 min | 265 trades | TP 58 % | net -23.8 % [-32.0, -16.1] | 605 trades | TP 51 % | net -22.7 % [-28.2, -16.9] |
| 0 s | TP 1.5x, 30 min | 255 trades | TP 59 % | net -23.7 % [-31.8, -16.6] | 577 trades | TP 56 % | net -22.6 % [-28.0, -16.8] |
| 0 s | TP 1.5x, 60 min | 233 trades | TP 59 % | net -23.7 % [-32.1, -16.1] | 527 trades | TP 58 % | net -23.8 % [-29.3, -17.5] |
| 0 s | TP 2x, 5 min | 271 trades | TP 22 % | net -19.9 % [-28.9, -11.4] | 625 trades | TP 19 % | net -21.1 % [-28.6, -14.8] |
| 0 s | TP 2x, 15 min | 265 trades | TP 35 % | net -38.7 % [-50.4, -27.7] | 605 trades | TP 31 % | net -30.9 % [-40.2, -22.9] |
| 0 s | TP 2x, 30 min | 255 trades | TP 36 % | net -38.0 % [-49.7, -26.7] | 577 trades | TP 35 % | net -29.7 % [-39.1, -21.6] |
| 0 s | TP 2x, 60 min | 233 trades | TP 35 % | net -40.2 % [-51.8, -27.9] | 527 trades | TP 38 % | net -33.1 % [-42.4, -25.0] |
| 0 s | TP 3x, 5 min | 271 trades | TP 6 % | net -19.0 % [-31.7, -7.1] | 625 trades | TP 6 % | net -18.5 % [-29.1, -9.6] |
| 0 s | TP 3x, 15 min | 265 trades | TP 15 % | net -51.2 % [-64.3, -38.4] | 605 trades | TP 16 % | net -36.9 % [-48.3, -27.2] |
| 0 s | TP 3x, 30 min | 255 trades | TP 18 % | net -54.5 % [-67.5, -40.9] | 577 trades | TP 18 % | net -39.6 % [-51.6, -30.0] |
| 0 s | TP 3x, 60 min | 233 trades | TP 18 % | net -53.9 % [-67.0, -38.5] | 527 trades | TP 20 % | net -42.2 % [-53.7, -31.7] |
| 5 s | TP 1.5x, 5 min | 271 trades | TP 49 % | net -19.5 % [-25.7, -13.9] | 624 trades | TP 40 % | net -23.1 % [-27.8, -18.9] |
| 5 s | TP 1.5x, 15 min | 265 trades | TP 56 % | net -26.7 % [-35.0, -19.2] | 604 trades | TP 48 % | net -25.8 % [-31.6, -20.0] |
| 5 s | TP 1.5x, 30 min | 255 trades | TP 56 % | net -26.7 % [-35.4, -19.4] | 576 trades | TP 54 % | net -25.4 % [-31.1, -19.1] |
| 5 s | TP 1.5x, 60 min | 233 trades | TP 55 % | net -28.1 % [-37.4, -20.1] | 526 trades | TP 55 % | net -27.1 % [-33.4, -20.4] |
| 5 s | TP 2x, 5 min | 271 trades | TP 23 % | net -20.8 % [-29.9, -12.3] | 624 trades | TP 19 % | net -22.4 % [-29.9, -16.3] |
| 5 s | TP 2x, 15 min | 265 trades | TP 35 % | net -39.3 % [-50.0, -29.0] | 604 trades | TP 31 % | net -32.2 % [-40.8, -24.4] |
| 5 s | TP 2x, 30 min | 255 trades | TP 36 % | net -38.0 % [-49.4, -27.2] | 576 trades | TP 34 % | net -30.5 % [-39.3, -23.0] |
| 5 s | TP 2x, 60 min | 233 trades | TP 36 % | net -38.8 % [-50.6, -27.1] | 526 trades | TP 37 % | net -33.7 % [-42.8, -25.8] |
| 5 s | TP 3x, 5 min | 271 trades | TP 5 % | net -21.9 % [-33.2, -11.1] | 624 trades | TP 6 % | net -19.9 % [-30.2, -11.3] |
| 5 s | TP 3x, 15 min | 265 trades | TP 14 % | net -55.3 % [-67.3, -43.7] | 604 trades | TP 15 % | net -38.5 % [-48.8, -29.8] |
| 5 s | TP 3x, 30 min | 255 trades | TP 16 % | net -57.6 % [-69.1, -45.4] | 576 trades | TP 17 % | net -41.0 % [-51.8, -32.1] |
| 5 s | TP 3x, 60 min | 233 trades | TP 17 % | net -57.2 % [-69.4, -44.0] | 526 trades | TP 20 % | net -43.6 % [-55.1, -33.4] |
| 10 s | TP 1.5x, 5 min | 270 trades | TP 51 % | net -18.1 % [-24.4, -11.6] | 623 trades | TP 41 % | net -22.1 % [-26.6, -17.7] |
| 10 s | TP 1.5x, 15 min | 265 trades | TP 58 % | net -24.8 % [-33.5, -17.2] | 604 trades | TP 49 % | net -24.2 % [-29.7, -18.7] |
| 10 s | TP 1.5x, 30 min | 255 trades | TP 58 % | net -24.7 % [-33.3, -17.0] | 576 trades | TP 55 % | net -23.6 % [-29.0, -17.7] |
| 10 s | TP 1.5x, 60 min | 233 trades | TP 57 % | net -25.9 % [-35.1, -18.2] | 526 trades | TP 57 % | net -25.1 % [-31.0, -18.5] |
| 10 s | TP 2x, 5 min | 270 trades | TP 23 % | net -21.3 % [-29.9, -13.2] | 623 trades | TP 19 % | net -23.2 % [-30.2, -17.4] |
| 10 s | TP 2x, 15 min | 265 trades | TP 36 % | net -38.1 % [-48.9, -28.1] | 604 trades | TP 30 % | net -32.0 % [-39.9, -25.0] |
| 10 s | TP 2x, 30 min | 255 trades | TP 36 % | net -37.3 % [-48.0, -26.9] | 576 trades | TP 34 % | net -31.1 % [-38.8, -24.3] |
| 10 s | TP 2x, 60 min | 233 trades | TP 36 % | net -38.0 % [-48.8, -27.3] | 526 trades | TP 37 % | net -33.9 % [-41.7, -26.6] |
| 10 s | TP 3x, 5 min | 270 trades | TP 5 % | net -22.2 % [-33.6, -11.3] | 623 trades | TP 5 % | net -21.8 % [-32.0, -13.3] |
| 10 s | TP 3x, 15 min | 265 trades | TP 13 % | net -56.8 % [-68.1, -45.3] | 604 trades | TP 14 % | net -41.1 % [-52.1, -32.1] |
| 10 s | TP 3x, 30 min | 255 trades | TP 16 % | net -59.8 % [-70.9, -48.0] | 576 trades | TP 16 % | net -44.0 % [-55.5, -35.2] |
| 10 s | TP 3x, 60 min | 233 trades | TP 16 % | net -59.3 % [-71.4, -45.9] | 526 trades | TP 18 % | net -46.8 % [-58.2, -37.1] |
| 20 s | TP 1.5x, 5 min | 270 trades | TP 46 % | net -24.0 % [-31.3, -17.0] | 624 trades | TP 38 % | net -25.0 % [-30.5, -20.3] |
| 20 s | TP 1.5x, 15 min | 265 trades | TP 52 % | net -32.0 % [-40.7, -23.9] | 605 trades | TP 46 % | net -27.7 % [-34.2, -21.7] |
| 20 s | TP 1.5x, 30 min | 254 trades | TP 52 % | net -31.9 % [-41.3, -23.2] | 576 trades | TP 52 % | net -26.9 % [-33.3, -20.8] |
| 20 s | TP 1.5x, 60 min | 233 trades | TP 52 % | net -31.8 % [-41.4, -23.1] | 527 trades | TP 54 % | net -28.1 % [-34.6, -21.1] |
| 20 s | TP 2x, 5 min | 270 trades | TP 21 % | net -23.6 % [-32.2, -15.3] | 624 trades | TP 18 % | net -24.0 % [-31.2, -18.1] |
| 20 s | TP 2x, 15 min | 265 trades | TP 35 % | net -39.9 % [-51.0, -29.7] | 605 trades | TP 31 % | net -31.5 % [-40.1, -24.0] |
| 20 s | TP 2x, 30 min | 254 trades | TP 35 % | net -39.0 % [-50.3, -28.2] | 576 trades | TP 35 % | net -30.2 % [-39.1, -22.8] |
| 20 s | TP 2x, 60 min | 233 trades | TP 34 % | net -40.8 % [-52.2, -29.1] | 527 trades | TP 36 % | net -34.4 % [-43.2, -26.4] |
| 20 s | TP 3x, 5 min | 270 trades | TP 4 % | net -24.7 % [-35.4, -14.9] | 624 trades | TP 5 % | net -23.4 % [-33.1, -15.0] |
| 20 s | TP 3x, 15 min | 265 trades | TP 12 % | net -59.3 % [-71.0, -47.8] | 605 trades | TP 13 % | net -42.9 % [-53.4, -33.9] |
| 20 s | TP 3x, 30 min | 254 trades | TP 15 % | net -62.7 % [-73.9, -51.3] | 576 trades | TP 15 % | net -46.4 % [-56.3, -38.0] |
| 20 s | TP 3x, 60 min | 233 trades | TP 15 % | net -62.5 % [-73.9, -50.2] | 527 trades | TP 17 % | net -49.0 % [-59.3, -39.9] |
| 30 s | TP 1.5x, 5 min | 270 trades | TP 46 % | net -23.9 % [-30.4, -17.7] | 624 trades | TP 36 % | net -26.4 % [-31.4, -22.3] |
| 30 s | TP 1.5x, 15 min | 265 trades | TP 54 % | net -29.2 % [-37.1, -22.0] | 605 trades | TP 46 % | net -27.6 % [-33.3, -22.5] |
| 30 s | TP 1.5x, 30 min | 254 trades | TP 54 % | net -29.0 % [-37.3, -21.8] | 576 trades | TP 53 % | net -26.3 % [-32.1, -20.8] |
| 30 s | TP 1.5x, 60 min | 233 trades | TP 55 % | net -28.7 % [-36.8, -21.4] | 527 trades | TP 55 % | net -26.9 % [-32.9, -21.0] |
| 30 s | TP 2x, 5 min | 270 trades | TP 17 % | net -26.2 % [-35.0, -18.5] | 624 trades | TP 15 % | net -26.8 % [-33.8, -20.9] |
| 30 s | TP 2x, 15 min | 265 trades | TP 33 % | net -41.6 % [-53.0, -31.9] | 605 trades | TP 29 % | net -33.8 % [-42.2, -26.8] |
| 30 s | TP 2x, 30 min | 254 trades | TP 33 % | net -42.0 % [-52.2, -32.1] | 576 trades | TP 33 % | net -33.0 % [-41.5, -25.8] |
| 30 s | TP 2x, 60 min | 233 trades | TP 32 % | net -44.1 % [-54.8, -33.1] | 527 trades | TP 35 % | net -36.4 % [-44.7, -28.7] |
| 30 s | TP 3x, 5 min | 270 trades | TP 5 % | net -26.4 % [-36.8, -17.4] | 624 trades | TP 5 % | net -24.2 % [-33.6, -16.0] |
| 30 s | TP 3x, 15 min | 265 trades | TP 12 % | net -58.6 % [-70.9, -46.6] | 605 trades | TP 13 % | net -42.0 % [-52.5, -32.7] |
| 30 s | TP 3x, 30 min | 254 trades | TP 15 % | net -60.4 % [-72.6, -48.7] | 576 trades | TP 16 % | net -45.1 % [-56.1, -36.3] |
| 30 s | TP 3x, 60 min | 233 trades | TP 15 % | net -61.0 % [-73.0, -49.0] | 527 trades | TP 17 % | net -47.8 % [-58.1, -38.9] |

Sizes, 10 s delay, TP 2x within 15 min: $100 265 trades | TP 36 % | net -32.0 % [-44.1, -20.9]; $500 265 trades | TP 36 % | net -38.1 % [-48.9, -28.1]; $1000 265 trades | TP 36 % | net -44.9 % [-54.5, -36.1].

## 6 funding about the ticket, TRAIN: `fit_share_90_100 <= 0.25` (593 of 1015 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 550 trades | TP 50 % | net -16.4 % [-22.2, -12.0] | 938 trades | TP 40 % | net -16.5 % [-20.0, -13.3] |
| 0 s | TP 1.5x, 15 min | 524 trades | TP 57 % | net -24.4 % [-31.9, -18.5] | 890 trades | TP 51 % | net -21.2 % [-25.4, -16.9] |
| 0 s | TP 1.5x, 30 min | 497 trades | TP 57 % | net -25.0 % [-32.5, -19.2] | 844 trades | TP 55 % | net -21.8 % [-26.3, -17.4] |
| 0 s | TP 1.5x, 60 min | 456 trades | TP 57 % | net -24.4 % [-32.0, -18.5] | 763 trades | TP 58 % | net -22.0 % [-27.3, -17.8] |
| 0 s | TP 2x, 5 min | 550 trades | TP 25 % | net -14.2 % [-20.6, -8.4] | 938 trades | TP 19 % | net -15.3 % [-19.5, -10.8] |
| 0 s | TP 2x, 15 min | 524 trades | TP 36 % | net -32.3 % [-40.2, -25.0] | 890 trades | TP 30 % | net -27.1 % [-32.7, -20.3] |
| 0 s | TP 2x, 30 min | 497 trades | TP 37 % | net -34.3 % [-42.7, -26.3] | 844 trades | TP 34 % | net -29.9 % [-35.6, -22.8] |
| 0 s | TP 2x, 60 min | 456 trades | TP 38 % | net -34.0 % [-42.0, -26.0] | 763 trades | TP 35 % | net -33.4 % [-39.2, -26.7] |
| 0 s | TP 3x, 5 min | 550 trades | TP 4 % | net -13.2 % [-19.9, -6.4] | 938 trades | TP 3 % | net -15.4 % [-19.9, -10.1] |
| 0 s | TP 3x, 15 min | 524 trades | TP 11 % | net -51.7 % [-60.3, -44.2] | 890 trades | TP 9 % | net -42.5 % [-49.6, -32.8] |
| 0 s | TP 3x, 30 min | 497 trades | TP 14 % | net -58.9 % [-67.3, -50.0] | 844 trades | TP 12 % | net -49.3 % [-57.2, -38.3] |
| 0 s | TP 3x, 60 min | 456 trades | TP 14 % | net -61.2 % [-70.1, -51.5] | 763 trades | TP 14 % | net -55.4 % [-63.2, -45.5] |
| 5 s | TP 1.5x, 5 min | 477 trades | TP 49 % | net -16.5 % [-22.5, -11.5] | 797 trades | TP 39 % | net -16.2 % [-20.0, -12.8] |
| 5 s | TP 1.5x, 15 min | 452 trades | TP 55 % | net -26.8 % [-34.5, -20.8] | 751 trades | TP 50 % | net -22.5 % [-27.0, -18.0] |
| 5 s | TP 1.5x, 30 min | 426 trades | TP 54 % | net -27.7 % [-34.9, -21.5] | 707 trades | TP 54 % | net -23.2 % [-28.3, -18.7] |
| 5 s | TP 1.5x, 60 min | 387 trades | TP 55 % | net -26.8 % [-34.3, -20.4] | 631 trades | TP 56 % | net -23.9 % [-29.4, -19.3] |
| 5 s | TP 2x, 5 min | 477 trades | TP 26 % | net -13.1 % [-19.8, -6.7] | 797 trades | TP 20 % | net -14.1 % [-18.8, -9.7] |
| 5 s | TP 2x, 15 min | 452 trades | TP 36 % | net -33.8 % [-43.4, -25.2] | 751 trades | TP 29 % | net -28.7 % [-34.6, -21.9] |
| 5 s | TP 2x, 30 min | 426 trades | TP 37 % | net -34.8 % [-44.7, -25.8] | 707 trades | TP 34 % | net -30.7 % [-37.5, -23.8] |
| 5 s | TP 2x, 60 min | 387 trades | TP 37 % | net -34.2 % [-44.3, -25.1] | 631 trades | TP 36 % | net -33.2 % [-40.7, -26.6] |
| 5 s | TP 3x, 5 min | 477 trades | TP 4 % | net -13.6 % [-20.8, -5.4] | 797 trades | TP 3 % | net -14.8 % [-19.6, -8.9] |
| 5 s | TP 3x, 15 min | 452 trades | TP 10 % | net -57.0 % [-66.2, -48.8] | 751 trades | TP 8 % | net -46.0 % [-52.5, -37.3] |
| 5 s | TP 3x, 30 min | 426 trades | TP 12 % | net -64.4 % [-74.1, -55.5] | 707 trades | TP 11 % | net -53.5 % [-60.9, -43.7] |
| 5 s | TP 3x, 60 min | 387 trades | TP 13 % | net -65.1 % [-74.9, -55.3] | 631 trades | TP 13 % | net -58.8 % [-66.6, -50.6] |
| 10 s | TP 1.5x, 5 min | 473 trades | TP 48 % | net -19.0 % [-25.0, -14.1] | 794 trades | TP 38 % | net -17.9 % [-21.3, -14.2] |
| 10 s | TP 1.5x, 15 min | 448 trades | TP 54 % | net -28.2 % [-35.2, -22.7] | 749 trades | TP 50 % | net -23.2 % [-27.5, -18.1] |
| 10 s | TP 1.5x, 30 min | 423 trades | TP 53 % | net -28.8 % [-35.6, -22.5] | 707 trades | TP 53 % | net -24.5 % [-29.2, -19.5] |
| 10 s | TP 1.5x, 60 min | 384 trades | TP 54 % | net -28.0 % [-34.9, -22.2] | 630 trades | TP 55 % | net -25.2 % [-30.3, -20.0] |
| 10 s | TP 2x, 5 min | 473 trades | TP 25 % | net -15.0 % [-22.4, -8.8] | 794 trades | TP 19 % | net -16.0 % [-20.6, -11.6] |
| 10 s | TP 2x, 15 min | 448 trades | TP 35 % | net -33.7 % [-42.4, -26.1] | 749 trades | TP 29 % | net -28.9 % [-34.4, -22.3] |
| 10 s | TP 2x, 30 min | 423 trades | TP 36 % | net -35.2 % [-44.3, -26.8] | 707 trades | TP 34 % | net -31.5 % [-37.7, -24.4] |
| 10 s | TP 2x, 60 min | 384 trades | TP 36 % | net -35.0 % [-44.2, -26.8] | 630 trades | TP 35 % | net -34.8 % [-40.8, -27.7] |
| 10 s | TP 3x, 5 min | 473 trades | TP 6 % | net -13.1 % [-20.8, -4.8] | 794 trades | TP 4 % | net -15.1 % [-19.8, -9.3] |
| 10 s | TP 3x, 15 min | 448 trades | TP 12 % | net -52.5 % [-61.4, -43.8] | 749 trades | TP 10 % | net -43.1 % [-50.0, -33.7] |
| 10 s | TP 3x, 30 min | 423 trades | TP 15 % | net -59.1 % [-68.2, -49.9] | 707 trades | TP 12 % | net -50.1 % [-57.7, -39.7] |
| 10 s | TP 3x, 60 min | 384 trades | TP 15 % | net -58.5 % [-68.1, -48.5] | 630 trades | TP 15 % | net -53.6 % [-61.3, -44.1] |
| 20 s | TP 1.5x, 5 min | 476 trades | TP 45 % | net -21.2 % [-27.8, -16.2] | 811 trades | TP 35 % | net -19.9 % [-23.7, -16.2] |
| 20 s | TP 1.5x, 15 min | 451 trades | TP 51 % | net -31.5 % [-38.9, -25.9] | 765 trades | TP 47 % | net -26.4 % [-30.7, -21.6] |
| 20 s | TP 1.5x, 30 min | 425 trades | TP 51 % | net -32.4 % [-39.4, -26.5] | 721 trades | TP 50 % | net -28.0 % [-32.5, -23.2] |
| 20 s | TP 1.5x, 60 min | 386 trades | TP 51 % | net -32.0 % [-39.0, -25.9] | 645 trades | TP 52 % | net -28.9 % [-33.9, -24.3] |
| 20 s | TP 2x, 5 min | 476 trades | TP 23 % | net -18.4 % [-25.3, -12.6] | 811 trades | TP 17 % | net -18.6 % [-22.9, -14.0] |
| 20 s | TP 2x, 15 min | 451 trades | TP 32 % | net -38.1 % [-46.8, -31.0] | 765 trades | TP 27 % | net -32.2 % [-37.5, -25.2] |
| 20 s | TP 2x, 30 min | 425 trades | TP 33 % | net -40.1 % [-50.2, -32.2] | 721 trades | TP 31 % | net -34.5 % [-40.8, -27.3] |
| 20 s | TP 2x, 60 min | 386 trades | TP 33 % | net -40.2 % [-50.8, -31.6] | 645 trades | TP 33 % | net -37.0 % [-44.2, -30.7] |
| 20 s | TP 3x, 5 min | 476 trades | TP 5 % | net -17.5 % [-25.3, -9.8] | 811 trades | TP 4 % | net -18.1 % [-23.0, -12.1] |
| 20 s | TP 3x, 15 min | 451 trades | TP 11 % | net -53.7 % [-65.0, -44.1] | 765 trades | TP 9 % | net -43.1 % [-50.5, -34.4] |
| 20 s | TP 3x, 30 min | 425 trades | TP 14 % | net -60.2 % [-71.3, -51.3] | 721 trades | TP 12 % | net -49.3 % [-56.7, -38.9] |
| 20 s | TP 3x, 60 min | 386 trades | TP 14 % | net -61.9 % [-72.2, -52.4] | 645 trades | TP 14 % | net -54.2 % [-62.4, -45.6] |
| 30 s | TP 1.5x, 5 min | 477 trades | TP 44 % | net -23.2 % [-29.6, -18.3] | 806 trades | TP 35 % | net -21.3 % [-25.1, -17.7] |
| 30 s | TP 1.5x, 15 min | 455 trades | TP 50 % | net -31.8 % [-38.9, -26.2] | 764 trades | TP 46 % | net -26.7 % [-31.1, -21.6] |
| 30 s | TP 1.5x, 30 min | 429 trades | TP 50 % | net -32.6 % [-39.5, -26.4] | 721 trades | TP 50 % | net -28.1 % [-33.4, -22.7] |
| 30 s | TP 1.5x, 60 min | 389 trades | TP 50 % | net -32.8 % [-40.1, -26.4] | 644 trades | TP 52 % | net -29.6 % [-34.9, -24.1] |
| 30 s | TP 2x, 5 min | 477 trades | TP 21 % | net -21.7 % [-29.6, -15.8] | 806 trades | TP 15 % | net -21.2 % [-25.5, -16.8] |
| 30 s | TP 2x, 15 min | 455 trades | TP 29 % | net -43.4 % [-53.1, -36.0] | 764 trades | TP 24 % | net -36.2 % [-42.4, -30.2] |
| 30 s | TP 2x, 30 min | 429 trades | TP 30 % | net -45.4 % [-55.1, -37.6] | 721 trades | TP 30 % | net -38.2 % [-45.4, -31.4] |
| 30 s | TP 2x, 60 min | 389 trades | TP 30 % | net -46.3 % [-57.0, -38.0] | 644 trades | TP 31 % | net -41.7 % [-48.9, -35.8] |
| 30 s | TP 3x, 5 min | 477 trades | TP 4 % | net -23.3 % [-32.8, -15.7] | 806 trades | TP 3 % | net -22.1 % [-27.8, -16.1] |
| 30 s | TP 3x, 15 min | 455 trades | TP 9 % | net -61.0 % [-71.9, -52.1] | 764 trades | TP 7 % | net -48.9 % [-56.6, -38.7] |
| 30 s | TP 3x, 30 min | 429 trades | TP 11 % | net -67.8 % [-78.4, -59.1] | 721 trades | TP 9 % | net -55.5 % [-63.4, -45.2] |
| 30 s | TP 3x, 60 min | 389 trades | TP 11 % | net -70.0 % [-80.8, -61.4] | 644 trades | TP 11 % | net -62.0 % [-70.0, -52.8] |

Sizes, 10 s delay, TP 2x within 15 min: $100 448 trades | TP 35 % | net -26.6 % [-36.5, -18.1]; $500 448 trades | TP 35 % | net -33.7 % [-42.4, -26.1]; $1000 448 trades | TP 35 % | net -41.3 % [-48.9, -34.7].

## 6 funding about the ticket, VAL: `fit_share_90_100 <= 0.25` (384 of 642 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 371 trades | TP 53 % | net -15.5 % [-21.1, -10.6] | 625 trades | TP 42 % | net -20.5 % [-24.9, -16.4] |
| 0 s | TP 1.5x, 15 min | 358 trades | TP 62 % | net -18.9 % [-25.8, -12.7] | 605 trades | TP 51 % | net -22.7 % [-28.2, -16.9] |
| 0 s | TP 1.5x, 30 min | 339 trades | TP 62 % | net -20.0 % [-26.9, -13.8] | 577 trades | TP 56 % | net -22.6 % [-28.0, -16.8] |
| 0 s | TP 1.5x, 60 min | 308 trades | TP 62 % | net -19.9 % [-26.2, -14.0] | 527 trades | TP 58 % | net -23.8 % [-29.3, -17.5] |
| 0 s | TP 2x, 5 min | 371 trades | TP 24 % | net -16.7 % [-25.7, -8.2] | 625 trades | TP 19 % | net -21.1 % [-28.6, -14.8] |
| 0 s | TP 2x, 15 min | 358 trades | TP 39 % | net -32.4 % [-42.9, -21.3] | 605 trades | TP 31 % | net -30.9 % [-40.2, -22.9] |
| 0 s | TP 2x, 30 min | 339 trades | TP 39 % | net -32.6 % [-43.2, -21.3] | 577 trades | TP 35 % | net -29.7 % [-39.1, -21.6] |
| 0 s | TP 2x, 60 min | 308 trades | TP 38 % | net -34.2 % [-45.2, -23.8] | 527 trades | TP 38 % | net -33.1 % [-42.4, -25.0] |
| 0 s | TP 3x, 5 min | 371 trades | TP 7 % | net -14.5 % [-26.2, -2.4] | 625 trades | TP 6 % | net -18.5 % [-29.1, -9.6] |
| 0 s | TP 3x, 15 min | 358 trades | TP 19 % | net -42.0 % [-56.2, -27.3] | 605 trades | TP 16 % | net -36.9 % [-48.3, -27.2] |
| 0 s | TP 3x, 30 min | 339 trades | TP 20 % | net -47.3 % [-61.0, -33.4] | 577 trades | TP 18 % | net -39.6 % [-51.6, -30.0] |
| 0 s | TP 3x, 60 min | 308 trades | TP 21 % | net -46.2 % [-60.1, -32.3] | 527 trades | TP 20 % | net -42.2 % [-53.7, -31.7] |
| 5 s | TP 1.5x, 5 min | 370 trades | TP 53 % | net -16.9 % [-22.3, -12.1] | 624 trades | TP 40 % | net -23.1 % [-27.8, -18.9] |
| 5 s | TP 1.5x, 15 min | 357 trades | TP 61 % | net -21.3 % [-27.5, -15.4] | 604 trades | TP 48 % | net -25.8 % [-31.6, -20.0] |
| 5 s | TP 1.5x, 30 min | 338 trades | TP 60 % | net -22.1 % [-28.5, -16.0] | 576 trades | TP 54 % | net -25.4 % [-31.1, -19.1] |
| 5 s | TP 1.5x, 60 min | 307 trades | TP 59 % | net -23.1 % [-29.1, -17.2] | 526 trades | TP 55 % | net -27.1 % [-33.4, -20.4] |
| 5 s | TP 2x, 5 min | 370 trades | TP 25 % | net -17.2 % [-26.2, -8.5] | 624 trades | TP 19 % | net -22.4 % [-29.9, -16.3] |
| 5 s | TP 2x, 15 min | 357 trades | TP 39 % | net -32.6 % [-43.3, -21.5] | 604 trades | TP 31 % | net -32.2 % [-40.8, -24.4] |
| 5 s | TP 2x, 30 min | 338 trades | TP 40 % | net -31.5 % [-42.3, -20.3] | 576 trades | TP 34 % | net -30.5 % [-39.3, -23.0] |
| 5 s | TP 2x, 60 min | 307 trades | TP 39 % | net -32.4 % [-43.5, -21.9] | 526 trades | TP 37 % | net -33.7 % [-42.8, -25.8] |
| 5 s | TP 3x, 5 min | 370 trades | TP 7 % | net -15.6 % [-27.1, -4.2] | 624 trades | TP 6 % | net -19.9 % [-30.2, -11.3] |
| 5 s | TP 3x, 15 min | 357 trades | TP 18 % | net -42.9 % [-55.5, -30.1] | 604 trades | TP 15 % | net -38.5 % [-48.8, -29.8] |
| 5 s | TP 3x, 30 min | 338 trades | TP 20 % | net -48.1 % [-60.7, -35.5] | 576 trades | TP 17 % | net -41.0 % [-51.8, -32.1] |
| 5 s | TP 3x, 60 min | 307 trades | TP 21 % | net -47.8 % [-61.1, -34.5] | 526 trades | TP 20 % | net -43.6 % [-55.1, -33.4] |
| 10 s | TP 1.5x, 5 min | 369 trades | TP 54 % | net -15.0 % [-20.5, -10.0] | 623 trades | TP 41 % | net -22.1 % [-26.6, -17.7] |
| 10 s | TP 1.5x, 15 min | 357 trades | TP 62 % | net -19.2 % [-25.8, -13.0] | 604 trades | TP 49 % | net -24.2 % [-29.7, -18.7] |
| 10 s | TP 1.5x, 30 min | 338 trades | TP 62 % | net -19.5 % [-26.5, -13.1] | 576 trades | TP 55 % | net -23.6 % [-29.0, -17.7] |
| 10 s | TP 1.5x, 60 min | 307 trades | TP 62 % | net -20.2 % [-27.0, -14.1] | 526 trades | TP 57 % | net -25.1 % [-31.0, -18.5] |
| 10 s | TP 2x, 5 min | 369 trades | TP 25 % | net -17.8 % [-26.6, -9.3] | 623 trades | TP 19 % | net -23.2 % [-30.2, -17.4] |
| 10 s | TP 2x, 15 min | 357 trades | TP 39 % | net -31.8 % [-41.8, -21.0] | 604 trades | TP 30 % | net -32.0 % [-39.9, -25.0] |
| 10 s | TP 2x, 30 min | 338 trades | TP 40 % | net -31.0 % [-41.1, -20.2] | 576 trades | TP 34 % | net -31.1 % [-38.8, -24.3] |
| 10 s | TP 2x, 60 min | 307 trades | TP 40 % | net -31.3 % [-41.5, -21.7] | 526 trades | TP 37 % | net -33.9 % [-41.7, -26.6] |
| 10 s | TP 3x, 5 min | 369 trades | TP 7 % | net -18.0 % [-29.6, -6.5] | 623 trades | TP 5 % | net -21.8 % [-32.0, -13.3] |
| 10 s | TP 3x, 15 min | 357 trades | TP 16 % | net -47.5 % [-60.7, -34.1] | 604 trades | TP 14 % | net -41.1 % [-52.1, -32.1] |
| 10 s | TP 3x, 30 min | 338 trades | TP 18 % | net -53.5 % [-66.1, -41.2] | 576 trades | TP 16 % | net -44.0 % [-55.5, -35.2] |
| 10 s | TP 3x, 60 min | 307 trades | TP 19 % | net -52.7 % [-65.6, -39.5] | 526 trades | TP 18 % | net -46.8 % [-58.2, -37.1] |
| 20 s | TP 1.5x, 5 min | 370 trades | TP 49 % | net -18.9 % [-24.9, -13.8] | 624 trades | TP 38 % | net -25.0 % [-30.5, -20.3] |
| 20 s | TP 1.5x, 15 min | 358 trades | TP 58 % | net -24.6 % [-32.3, -18.1] | 605 trades | TP 46 % | net -27.7 % [-34.2, -21.7] |
| 20 s | TP 1.5x, 30 min | 338 trades | TP 57 % | net -25.5 % [-33.6, -18.4] | 576 trades | TP 52 % | net -26.9 % [-33.3, -20.8] |
| 20 s | TP 1.5x, 60 min | 308 trades | TP 58 % | net -24.9 % [-32.8, -18.6] | 527 trades | TP 54 % | net -28.1 % [-34.6, -21.1] |
| 20 s | TP 2x, 5 min | 370 trades | TP 24 % | net -18.8 % [-27.5, -10.6] | 624 trades | TP 18 % | net -24.0 % [-31.2, -18.1] |
| 20 s | TP 2x, 15 min | 358 trades | TP 39 % | net -32.3 % [-43.1, -21.7] | 605 trades | TP 31 % | net -31.5 % [-40.1, -24.0] |
| 20 s | TP 2x, 30 min | 338 trades | TP 40 % | net -31.4 % [-42.1, -20.5] | 576 trades | TP 35 % | net -30.2 % [-39.1, -22.8] |
| 20 s | TP 2x, 60 min | 308 trades | TP 39 % | net -33.0 % [-43.7, -23.0] | 527 trades | TP 36 % | net -34.4 % [-43.2, -26.4] |
| 20 s | TP 3x, 5 min | 370 trades | TP 6 % | net -20.2 % [-31.1, -9.7] | 624 trades | TP 5 % | net -23.4 % [-33.1, -15.0] |
| 20 s | TP 3x, 15 min | 358 trades | TP 15 % | net -50.1 % [-62.8, -37.0] | 605 trades | TP 13 % | net -42.9 % [-53.4, -33.9] |
| 20 s | TP 3x, 30 min | 338 trades | TP 17 % | net -56.5 % [-68.3, -45.7] | 576 trades | TP 15 % | net -46.4 % [-56.3, -38.0] |
| 20 s | TP 3x, 60 min | 308 trades | TP 17 % | net -56.0 % [-67.7, -44.8] | 527 trades | TP 17 % | net -49.0 % [-59.3, -39.9] |
| 30 s | TP 1.5x, 5 min | 370 trades | TP 47 % | net -21.7 % [-27.6, -16.3] | 624 trades | TP 36 % | net -26.4 % [-31.4, -22.3] |
| 30 s | TP 1.5x, 15 min | 358 trades | TP 57 % | net -25.4 % [-32.3, -18.6] | 605 trades | TP 46 % | net -27.6 % [-33.3, -22.5] |
| 30 s | TP 1.5x, 30 min | 338 trades | TP 58 % | net -24.7 % [-32.1, -18.1] | 576 trades | TP 53 % | net -26.3 % [-32.1, -20.8] |
| 30 s | TP 1.5x, 60 min | 308 trades | TP 58 % | net -24.1 % [-31.0, -17.9] | 527 trades | TP 55 % | net -26.9 % [-32.9, -21.0] |
| 30 s | TP 2x, 5 min | 370 trades | TP 19 % | net -23.1 % [-31.9, -14.8] | 624 trades | TP 15 % | net -26.8 % [-33.8, -20.9] |
| 30 s | TP 2x, 15 min | 358 trades | TP 36 % | net -35.8 % [-46.3, -25.6] | 605 trades | TP 29 % | net -33.8 % [-42.2, -26.8] |
| 30 s | TP 2x, 30 min | 338 trades | TP 37 % | net -35.9 % [-46.6, -25.4] | 576 trades | TP 33 % | net -33.0 % [-41.5, -25.8] |
| 30 s | TP 2x, 60 min | 308 trades | TP 36 % | net -37.5 % [-48.0, -27.8] | 527 trades | TP 35 % | net -36.4 % [-44.7, -28.7] |
| 30 s | TP 3x, 5 min | 370 trades | TP 7 % | net -20.8 % [-32.0, -9.3] | 624 trades | TP 5 % | net -24.2 % [-33.6, -16.0] |
| 30 s | TP 3x, 15 min | 358 trades | TP 16 % | net -47.2 % [-60.7, -32.3] | 605 trades | TP 13 % | net -42.0 % [-52.5, -32.7] |
| 30 s | TP 3x, 30 min | 338 trades | TP 19 % | net -52.1 % [-65.2, -39.5] | 576 trades | TP 16 % | net -45.1 % [-56.1, -36.3] |
| 30 s | TP 3x, 60 min | 308 trades | TP 19 % | net -52.0 % [-64.3, -39.9] | 527 trades | TP 17 % | net -47.8 % [-58.1, -38.9] |

Sizes, 10 s delay, TP 2x within 15 min: $100 357 trades | TP 39 % | net -25.0 % [-36.1, -12.6]; $500 357 trades | TP 39 % | net -31.8 % [-41.8, -21.0]; $1000 357 trades | TP 39 % | net -39.4 % [-48.2, -29.9].

## 7 snipers by fraction risked, TRAIN: `n_a_ge90 <= 2` (710 of 1015 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 658 trades | TP 52 % | net -14.4 % [-20.9, -10.4] | 938 trades | TP 40 % | net -16.5 % [-20.0, -13.3] |
| 0 s | TP 1.5x, 15 min | 625 trades | TP 60 % | net -22.0 % [-29.7, -17.1] | 890 trades | TP 51 % | net -21.2 % [-25.4, -16.9] |
| 0 s | TP 1.5x, 30 min | 594 trades | TP 59 % | net -22.7 % [-30.2, -17.7] | 844 trades | TP 55 % | net -21.8 % [-26.3, -17.4] |
| 0 s | TP 1.5x, 60 min | 539 trades | TP 60 % | net -22.3 % [-30.1, -17.2] | 763 trades | TP 58 % | net -22.0 % [-27.3, -17.8] |
| 0 s | TP 2x, 5 min | 658 trades | TP 25 % | net -12.1 % [-19.2, -6.3] | 938 trades | TP 19 % | net -15.3 % [-19.5, -10.8] |
| 0 s | TP 2x, 15 min | 625 trades | TP 37 % | net -30.8 % [-39.1, -24.1] | 890 trades | TP 30 % | net -27.1 % [-32.7, -20.3] |
| 0 s | TP 2x, 30 min | 594 trades | TP 38 % | net -33.5 % [-41.8, -25.8] | 844 trades | TP 34 % | net -29.9 % [-35.6, -22.8] |
| 0 s | TP 2x, 60 min | 539 trades | TP 38 % | net -34.6 % [-41.6, -26.6] | 763 trades | TP 35 % | net -33.4 % [-39.2, -26.7] |
| 0 s | TP 3x, 5 min | 658 trades | TP 3 % | net -12.1 % [-19.4, -5.2] | 938 trades | TP 3 % | net -15.4 % [-19.9, -10.1] |
| 0 s | TP 3x, 15 min | 625 trades | TP 11 % | net -51.9 % [-58.9, -44.8] | 890 trades | TP 9 % | net -42.5 % [-49.6, -32.8] |
| 0 s | TP 3x, 30 min | 594 trades | TP 14 % | net -59.2 % [-67.4, -50.6] | 844 trades | TP 12 % | net -49.3 % [-57.2, -38.3] |
| 0 s | TP 3x, 60 min | 539 trades | TP 14 % | net -62.1 % [-69.5, -53.1] | 763 trades | TP 14 % | net -55.4 % [-63.2, -45.5] |
| 5 s | TP 1.5x, 5 min | 560 trades | TP 51 % | net -14.0 % [-21.1, -9.2] | 797 trades | TP 39 % | net -16.2 % [-20.0, -12.8] |
| 5 s | TP 1.5x, 15 min | 529 trades | TP 58 % | net -23.8 % [-32.8, -18.0] | 751 trades | TP 50 % | net -22.5 % [-27.0, -18.0] |
| 5 s | TP 1.5x, 30 min | 499 trades | TP 58 % | net -24.9 % [-33.8, -19.2] | 707 trades | TP 54 % | net -23.2 % [-28.3, -18.7] |
| 5 s | TP 1.5x, 60 min | 448 trades | TP 58 % | net -24.5 % [-33.4, -19.0] | 631 trades | TP 56 % | net -23.9 % [-29.4, -19.3] |
| 5 s | TP 2x, 5 min | 560 trades | TP 27 % | net -10.2 % [-18.9, -4.3] | 797 trades | TP 20 % | net -14.1 % [-18.8, -9.7] |
| 5 s | TP 2x, 15 min | 529 trades | TP 37 % | net -32.2 % [-42.7, -24.8] | 751 trades | TP 29 % | net -28.7 % [-34.6, -21.9] |
| 5 s | TP 2x, 30 min | 499 trades | TP 38 % | net -34.0 % [-44.9, -26.3] | 707 trades | TP 34 % | net -30.7 % [-37.5, -23.8] |
| 5 s | TP 2x, 60 min | 448 trades | TP 38 % | net -34.3 % [-45.5, -26.7] | 631 trades | TP 36 % | net -33.2 % [-40.7, -26.6] |
| 5 s | TP 3x, 5 min | 560 trades | TP 4 % | net -11.2 % [-19.3, -3.1] | 797 trades | TP 3 % | net -14.8 % [-19.6, -8.9] |
| 5 s | TP 3x, 15 min | 529 trades | TP 11 % | net -55.1 % [-65.2, -48.1] | 751 trades | TP 8 % | net -46.0 % [-52.5, -37.3] |
| 5 s | TP 3x, 30 min | 499 trades | TP 13 % | net -63.2 % [-74.0, -56.0] | 707 trades | TP 11 % | net -53.5 % [-60.9, -43.7] |
| 5 s | TP 3x, 60 min | 448 trades | TP 14 % | net -64.6 % [-74.9, -56.4] | 631 trades | TP 13 % | net -58.8 % [-66.6, -50.6] |
| 10 s | TP 1.5x, 5 min | 559 trades | TP 50 % | net -16.2 % [-22.8, -11.6] | 794 trades | TP 38 % | net -17.9 % [-21.3, -14.2] |
| 10 s | TP 1.5x, 15 min | 528 trades | TP 57 % | net -24.7 % [-32.6, -19.7] | 749 trades | TP 50 % | net -23.2 % [-27.5, -18.1] |
| 10 s | TP 1.5x, 30 min | 500 trades | TP 57 % | net -25.7 % [-33.3, -20.6] | 707 trades | TP 53 % | net -24.5 % [-29.2, -19.5] |
| 10 s | TP 1.5x, 60 min | 449 trades | TP 57 % | net -25.5 % [-32.5, -20.3] | 630 trades | TP 55 % | net -25.2 % [-30.3, -20.0] |
| 10 s | TP 2x, 5 min | 559 trades | TP 26 % | net -12.3 % [-20.4, -6.8] | 794 trades | TP 19 % | net -16.0 % [-20.6, -11.6] |
| 10 s | TP 2x, 15 min | 528 trades | TP 37 % | net -31.4 % [-40.6, -24.8] | 749 trades | TP 29 % | net -28.9 % [-34.4, -22.3] |
| 10 s | TP 2x, 30 min | 500 trades | TP 38 % | net -34.1 % [-44.0, -26.5] | 707 trades | TP 34 % | net -31.5 % [-37.7, -24.4] |
| 10 s | TP 2x, 60 min | 449 trades | TP 37 % | net -35.7 % [-44.2, -27.6] | 630 trades | TP 35 % | net -34.8 % [-40.8, -27.7] |
| 10 s | TP 3x, 5 min | 559 trades | TP 6 % | net -11.1 % [-18.7, -3.9] | 794 trades | TP 4 % | net -15.1 % [-19.8, -9.3] |
| 10 s | TP 3x, 15 min | 528 trades | TP 13 % | net -50.5 % [-59.6, -42.6] | 749 trades | TP 10 % | net -43.1 % [-50.0, -33.7] |
| 10 s | TP 3x, 30 min | 500 trades | TP 16 % | net -57.8 % [-67.4, -48.8] | 707 trades | TP 12 % | net -50.1 % [-57.7, -39.7] |
| 10 s | TP 3x, 60 min | 449 trades | TP 17 % | net -57.0 % [-66.8, -48.0] | 630 trades | TP 15 % | net -53.6 % [-61.3, -44.1] |
| 20 s | TP 1.5x, 5 min | 562 trades | TP 46 % | net -18.9 % [-26.3, -14.2] | 811 trades | TP 35 % | net -19.9 % [-23.7, -16.2] |
| 20 s | TP 1.5x, 15 min | 531 trades | TP 54 % | net -28.9 % [-36.4, -24.0] | 765 trades | TP 47 % | net -26.4 % [-30.7, -21.6] |
| 20 s | TP 1.5x, 30 min | 501 trades | TP 54 % | net -29.9 % [-37.9, -24.7] | 721 trades | TP 50 % | net -28.0 % [-32.5, -23.2] |
| 20 s | TP 1.5x, 60 min | 450 trades | TP 54 % | net -30.4 % [-37.4, -25.4] | 645 trades | TP 52 % | net -28.9 % [-33.9, -24.3] |
| 20 s | TP 2x, 5 min | 562 trades | TP 24 % | net -15.8 % [-24.2, -10.3] | 811 trades | TP 17 % | net -18.6 % [-22.9, -14.0] |
| 20 s | TP 2x, 15 min | 531 trades | TP 34 % | net -36.0 % [-44.2, -29.7] | 765 trades | TP 27 % | net -32.2 % [-37.5, -25.2] |
| 20 s | TP 2x, 30 min | 501 trades | TP 35 % | net -38.6 % [-48.7, -30.9] | 721 trades | TP 31 % | net -34.5 % [-40.8, -27.3] |
| 20 s | TP 2x, 60 min | 450 trades | TP 35 % | net -39.4 % [-49.3, -31.8] | 645 trades | TP 33 % | net -37.0 % [-44.2, -30.7] |
| 20 s | TP 3x, 5 min | 562 trades | TP 6 % | net -15.1 % [-23.8, -7.9] | 811 trades | TP 4 % | net -18.1 % [-23.0, -12.1] |
| 20 s | TP 3x, 15 min | 531 trades | TP 12 % | net -50.8 % [-61.6, -42.6] | 765 trades | TP 9 % | net -43.1 % [-50.5, -34.4] |
| 20 s | TP 3x, 30 min | 501 trades | TP 15 % | net -57.4 % [-69.4, -48.2] | 721 trades | TP 12 % | net -49.3 % [-56.7, -38.9] |
| 20 s | TP 3x, 60 min | 450 trades | TP 16 % | net -59.2 % [-70.6, -49.6] | 645 trades | TP 14 % | net -54.2 % [-62.4, -45.6] |
| 30 s | TP 1.5x, 5 min | 561 trades | TP 47 % | net -20.1 % [-27.4, -15.4] | 806 trades | TP 35 % | net -21.3 % [-25.1, -17.7] |
| 30 s | TP 1.5x, 15 min | 534 trades | TP 54 % | net -29.0 % [-37.2, -23.8] | 764 trades | TP 46 % | net -26.7 % [-31.1, -21.6] |
| 30 s | TP 1.5x, 30 min | 505 trades | TP 54 % | net -29.7 % [-37.9, -24.5] | 721 trades | TP 50 % | net -28.1 % [-33.4, -22.7] |
| 30 s | TP 1.5x, 60 min | 452 trades | TP 53 % | net -31.0 % [-38.6, -25.4] | 644 trades | TP 52 % | net -29.6 % [-34.9, -24.1] |
| 30 s | TP 2x, 5 min | 561 trades | TP 21 % | net -19.2 % [-27.8, -13.6] | 806 trades | TP 15 % | net -21.2 % [-25.5, -16.8] |
| 30 s | TP 2x, 15 min | 534 trades | TP 30 % | net -41.7 % [-52.6, -34.8] | 764 trades | TP 24 % | net -36.2 % [-42.4, -30.2] |
| 30 s | TP 2x, 30 min | 505 trades | TP 32 % | net -44.1 % [-56.2, -36.9] | 721 trades | TP 30 % | net -38.2 % [-45.4, -31.4] |
| 30 s | TP 2x, 60 min | 452 trades | TP 31 % | net -45.6 % [-57.1, -38.4] | 644 trades | TP 31 % | net -41.7 % [-48.9, -35.8] |
| 30 s | TP 3x, 5 min | 561 trades | TP 4 % | net -20.2 % [-30.5, -12.5] | 806 trades | TP 3 % | net -22.1 % [-27.8, -16.1] |
| 30 s | TP 3x, 15 min | 534 trades | TP 10 % | net -58.6 % [-70.4, -49.8] | 764 trades | TP 7 % | net -48.9 % [-56.6, -38.7] |
| 30 s | TP 3x, 30 min | 505 trades | TP 12 % | net -65.5 % [-77.6, -56.7] | 721 trades | TP 9 % | net -55.5 % [-63.4, -45.2] |
| 30 s | TP 3x, 60 min | 452 trades | TP 12 % | net -68.3 % [-78.8, -60.3] | 644 trades | TP 11 % | net -62.0 % [-70.0, -52.8] |

Sizes, 10 s delay, TP 2x within 15 min: $100 528 trades | TP 37 % | net -23.8 % [-34.2, -16.2]; $500 528 trades | TP 37 % | net -31.4 % [-40.6, -24.8]; $1000 528 trades | TP 37 % | net -39.6 % [-47.5, -33.8].

## 7 snipers by fraction risked, VAL: `n_a_ge90 <= 2` (467 of 642 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 453 trades | TP 53 % | net -16.4 % [-21.3, -12.3] | 625 trades | TP 42 % | net -20.5 % [-24.9, -16.4] |
| 0 s | TP 1.5x, 15 min | 437 trades | TP 61 % | net -20.5 % [-25.9, -14.7] | 605 trades | TP 51 % | net -22.7 % [-28.2, -16.9] |
| 0 s | TP 1.5x, 30 min | 413 trades | TP 61 % | net -20.8 % [-26.0, -14.9] | 577 trades | TP 56 % | net -22.6 % [-28.0, -16.8] |
| 0 s | TP 1.5x, 60 min | 376 trades | TP 61 % | net -21.2 % [-26.3, -14.9] | 527 trades | TP 58 % | net -23.8 % [-29.3, -17.5] |
| 0 s | TP 2x, 5 min | 453 trades | TP 26 % | net -15.8 % [-25.6, -8.7] | 625 trades | TP 19 % | net -21.1 % [-28.6, -14.8] |
| 0 s | TP 2x, 15 min | 437 trades | TP 41 % | net -29.0 % [-41.4, -18.8] | 605 trades | TP 31 % | net -30.9 % [-40.2, -22.9] |
| 0 s | TP 2x, 30 min | 413 trades | TP 41 % | net -28.7 % [-40.9, -18.6] | 577 trades | TP 35 % | net -29.7 % [-39.1, -21.6] |
| 0 s | TP 2x, 60 min | 376 trades | TP 40 % | net -30.5 % [-42.3, -21.6] | 527 trades | TP 38 % | net -33.1 % [-42.4, -25.0] |
| 0 s | TP 3x, 5 min | 453 trades | TP 8 % | net -12.5 % [-26.5, -1.3] | 625 trades | TP 6 % | net -18.5 % [-29.1, -9.6] |
| 0 s | TP 3x, 15 min | 437 trades | TP 21 % | net -37.9 % [-54.8, -24.5] | 605 trades | TP 16 % | net -36.9 % [-48.3, -27.2] |
| 0 s | TP 3x, 30 min | 413 trades | TP 22 % | net -42.0 % [-58.9, -28.5] | 577 trades | TP 18 % | net -39.6 % [-51.6, -30.0] |
| 0 s | TP 3x, 60 min | 376 trades | TP 23 % | net -42.4 % [-58.4, -30.1] | 527 trades | TP 20 % | net -42.2 % [-53.7, -31.7] |
| 5 s | TP 1.5x, 5 min | 452 trades | TP 52 % | net -18.5 % [-23.0, -14.3] | 624 trades | TP 40 % | net -23.1 % [-27.8, -18.9] |
| 5 s | TP 1.5x, 15 min | 436 trades | TP 59 % | net -23.2 % [-27.9, -17.9] | 604 trades | TP 48 % | net -25.8 % [-31.6, -20.0] |
| 5 s | TP 1.5x, 30 min | 412 trades | TP 59 % | net -23.5 % [-28.1, -17.5] | 576 trades | TP 54 % | net -25.4 % [-31.1, -19.1] |
| 5 s | TP 1.5x, 60 min | 375 trades | TP 58 % | net -24.8 % [-29.7, -18.2] | 526 trades | TP 55 % | net -27.1 % [-33.4, -20.4] |
| 5 s | TP 2x, 5 min | 452 trades | TP 26 % | net -17.1 % [-26.2, -10.5] | 624 trades | TP 19 % | net -22.4 % [-29.9, -16.3] |
| 5 s | TP 2x, 15 min | 436 trades | TP 40 % | net -29.9 % [-41.8, -20.1] | 604 trades | TP 31 % | net -32.2 % [-40.8, -24.4] |
| 5 s | TP 2x, 30 min | 412 trades | TP 42 % | net -28.5 % [-39.8, -19.5] | 576 trades | TP 34 % | net -30.5 % [-39.3, -23.0] |
| 5 s | TP 2x, 60 min | 375 trades | TP 41 % | net -29.9 % [-41.3, -21.5] | 526 trades | TP 37 % | net -33.7 % [-42.8, -25.8] |
| 5 s | TP 3x, 5 min | 452 trades | TP 8 % | net -13.9 % [-27.0, -3.8] | 624 trades | TP 6 % | net -19.9 % [-30.2, -11.3] |
| 5 s | TP 3x, 15 min | 436 trades | TP 20 % | net -39.1 % [-54.3, -27.3] | 604 trades | TP 15 % | net -38.5 % [-48.8, -29.8] |
| 5 s | TP 3x, 30 min | 412 trades | TP 22 % | net -43.2 % [-58.1, -31.5] | 576 trades | TP 17 % | net -41.0 % [-51.8, -32.1] |
| 5 s | TP 3x, 60 min | 375 trades | TP 22 % | net -43.6 % [-59.3, -31.8] | 526 trades | TP 20 % | net -43.6 % [-55.1, -33.4] |
| 10 s | TP 1.5x, 5 min | 451 trades | TP 54 % | net -16.8 % [-21.2, -12.4] | 623 trades | TP 41 % | net -22.1 % [-26.6, -17.7] |
| 10 s | TP 1.5x, 15 min | 436 trades | TP 60 % | net -21.2 % [-26.1, -16.1] | 604 trades | TP 49 % | net -24.2 % [-29.7, -18.7] |
| 10 s | TP 1.5x, 30 min | 412 trades | TP 61 % | net -21.1 % [-26.2, -15.3] | 576 trades | TP 55 % | net -23.6 % [-29.0, -17.7] |
| 10 s | TP 1.5x, 60 min | 375 trades | TP 60 % | net -22.2 % [-27.1, -16.0] | 526 trades | TP 57 % | net -25.1 % [-31.0, -18.5] |
| 10 s | TP 2x, 5 min | 451 trades | TP 25 % | net -17.8 % [-26.5, -11.5] | 623 trades | TP 19 % | net -23.2 % [-30.2, -17.4] |
| 10 s | TP 2x, 15 min | 436 trades | TP 40 % | net -29.9 % [-40.4, -21.6] | 604 trades | TP 30 % | net -32.0 % [-39.9, -25.0] |
| 10 s | TP 2x, 30 min | 412 trades | TP 41 % | net -28.9 % [-38.9, -20.8] | 576 trades | TP 34 % | net -31.1 % [-38.8, -24.3] |
| 10 s | TP 2x, 60 min | 375 trades | TP 41 % | net -29.9 % [-39.2, -22.7] | 526 trades | TP 37 % | net -33.9 % [-41.7, -26.6] |
| 10 s | TP 3x, 5 min | 451 trades | TP 7 % | net -16.1 % [-29.8, -5.8] | 623 trades | TP 5 % | net -21.8 % [-32.0, -13.3] |
| 10 s | TP 3x, 15 min | 436 trades | TP 18 % | net -43.0 % [-59.3, -29.6] | 604 trades | TP 14 % | net -41.1 % [-52.1, -32.1] |
| 10 s | TP 3x, 30 min | 412 trades | TP 20 % | net -47.5 % [-63.4, -34.8] | 576 trades | TP 16 % | net -44.0 % [-55.5, -35.2] |
| 10 s | TP 3x, 60 min | 375 trades | TP 20 % | net -48.2 % [-63.7, -36.0] | 526 trades | TP 18 % | net -46.8 % [-58.2, -37.1] |
| 20 s | TP 1.5x, 5 min | 452 trades | TP 50 % | net -20.1 % [-25.7, -15.7] | 624 trades | TP 38 % | net -25.0 % [-30.5, -20.3] |
| 20 s | TP 1.5x, 15 min | 437 trades | TP 57 % | net -25.4 % [-32.4, -20.1] | 605 trades | TP 46 % | net -27.7 % [-34.2, -21.7] |
| 20 s | TP 1.5x, 30 min | 412 trades | TP 57 % | net -25.7 % [-33.5, -20.1] | 576 trades | TP 52 % | net -26.9 % [-33.3, -20.8] |
| 20 s | TP 1.5x, 60 min | 376 trades | TP 57 % | net -26.0 % [-32.6, -20.2] | 527 trades | TP 54 % | net -28.1 % [-34.6, -21.1] |
| 20 s | TP 2x, 5 min | 452 trades | TP 25 % | net -18.4 % [-27.8, -11.5] | 624 trades | TP 18 % | net -24.0 % [-31.2, -18.1] |
| 20 s | TP 2x, 15 min | 437 trades | TP 40 % | net -29.4 % [-41.5, -20.0] | 605 trades | TP 31 % | net -31.5 % [-40.1, -24.0] |
| 20 s | TP 2x, 30 min | 412 trades | TP 42 % | net -28.2 % [-39.9, -19.1] | 576 trades | TP 35 % | net -30.2 % [-39.1, -22.8] |
| 20 s | TP 2x, 60 min | 376 trades | TP 40 % | net -30.2 % [-41.2, -21.8] | 527 trades | TP 36 % | net -34.4 % [-43.2, -26.4] |
| 20 s | TP 3x, 5 min | 452 trades | TP 7 % | net -17.6 % [-30.9, -7.4] | 624 trades | TP 5 % | net -23.4 % [-33.1, -15.0] |
| 20 s | TP 3x, 15 min | 437 trades | TP 17 % | net -45.8 % [-61.1, -33.2] | 605 trades | TP 13 % | net -42.9 % [-53.4, -33.9] |
| 20 s | TP 3x, 30 min | 412 trades | TP 19 % | net -51.2 % [-65.9, -40.1] | 576 trades | TP 15 % | net -46.4 % [-56.3, -38.0] |
| 20 s | TP 3x, 60 min | 376 trades | TP 19 % | net -51.5 % [-65.3, -41.1] | 527 trades | TP 17 % | net -49.0 % [-59.3, -39.9] |
| 30 s | TP 1.5x, 5 min | 452 trades | TP 47 % | net -22.2 % [-27.9, -18.1] | 624 trades | TP 36 % | net -26.4 % [-31.4, -22.3] |
| 30 s | TP 1.5x, 15 min | 437 trades | TP 56 % | net -25.6 % [-32.1, -20.9] | 605 trades | TP 46 % | net -27.6 % [-33.3, -22.5] |
| 30 s | TP 1.5x, 30 min | 412 trades | TP 57 % | net -24.7 % [-31.4, -19.3] | 576 trades | TP 53 % | net -26.3 % [-32.1, -20.8] |
| 30 s | TP 1.5x, 60 min | 376 trades | TP 57 % | net -24.6 % [-30.0, -19.3] | 527 trades | TP 55 % | net -26.9 % [-32.9, -21.0] |
| 30 s | TP 2x, 5 min | 452 trades | TP 20 % | net -22.1 % [-31.8, -15.0] | 624 trades | TP 15 % | net -26.8 % [-33.8, -20.9] |
| 30 s | TP 2x, 15 min | 437 trades | TP 38 % | net -32.7 % [-44.7, -23.8] | 605 trades | TP 29 % | net -33.8 % [-42.2, -26.8] |
| 30 s | TP 2x, 30 min | 412 trades | TP 39 % | net -32.3 % [-43.7, -23.5] | 576 trades | TP 33 % | net -33.0 % [-41.5, -25.8] |
| 30 s | TP 2x, 60 min | 376 trades | TP 38 % | net -34.3 % [-44.5, -26.5] | 527 trades | TP 35 % | net -36.4 % [-44.7, -28.7] |
| 30 s | TP 3x, 5 min | 452 trades | TP 7 % | net -18.6 % [-31.8, -8.5] | 624 trades | TP 5 % | net -24.2 % [-33.6, -16.0] |
| 30 s | TP 3x, 15 min | 437 trades | TP 17 % | net -43.7 % [-59.3, -30.8] | 605 trades | TP 13 % | net -42.0 % [-52.5, -32.7] |
| 30 s | TP 3x, 30 min | 412 trades | TP 20 % | net -48.0 % [-63.5, -36.1] | 576 trades | TP 16 % | net -45.1 % [-56.1, -36.3] |
| 30 s | TP 3x, 60 min | 376 trades | TP 20 % | net -48.3 % [-61.9, -37.7] | 527 trades | TP 17 % | net -47.8 % [-58.1, -38.9] |

Sizes, 10 s delay, TP 2x within 15 min: $100 436 trades | TP 40 % | net -22.9 % [-34.6, -13.5]; $500 436 trades | TP 40 % | net -29.9 % [-40.4, -21.6]; $1000 436 trades | TP 40 % | net -37.7 % [-46.9, -30.4].

## 8 topology, TRAIN: `gen_share_hub > 0` (584 of 1015 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 547 trades | TP 53 % | net -15.9 % [-21.2, -11.5] | 938 trades | TP 40 % | net -16.5 % [-20.0, -13.3] |
| 0 s | TP 1.5x, 15 min | 519 trades | TP 58 % | net -24.6 % [-31.6, -19.1] | 890 trades | TP 51 % | net -21.2 % [-25.4, -16.9] |
| 0 s | TP 1.5x, 30 min | 487 trades | TP 58 % | net -25.3 % [-32.2, -19.5] | 844 trades | TP 55 % | net -21.8 % [-26.3, -17.4] |
| 0 s | TP 1.5x, 60 min | 432 trades | TP 59 % | net -23.7 % [-31.2, -18.0] | 763 trades | TP 58 % | net -22.0 % [-27.3, -17.8] |
| 0 s | TP 2x, 5 min | 547 trades | TP 26 % | net -14.1 % [-20.5, -6.9] | 938 trades | TP 19 % | net -15.3 % [-19.5, -10.8] |
| 0 s | TP 2x, 15 min | 519 trades | TP 37 % | net -34.4 % [-42.4, -25.9] | 890 trades | TP 30 % | net -27.1 % [-32.7, -20.3] |
| 0 s | TP 2x, 30 min | 487 trades | TP 37 % | net -35.8 % [-44.4, -26.7] | 844 trades | TP 34 % | net -29.9 % [-35.6, -22.8] |
| 0 s | TP 2x, 60 min | 432 trades | TP 38 % | net -35.7 % [-43.5, -27.5] | 763 trades | TP 35 % | net -33.4 % [-39.2, -26.7] |
| 0 s | TP 3x, 5 min | 547 trades | TP 3 % | net -13.6 % [-20.6, -5.0] | 938 trades | TP 3 % | net -15.4 % [-19.9, -10.1] |
| 0 s | TP 3x, 15 min | 519 trades | TP 10 % | net -57.5 % [-63.9, -49.9] | 890 trades | TP 9 % | net -42.5 % [-49.6, -32.8] |
| 0 s | TP 3x, 30 min | 487 trades | TP 13 % | net -63.5 % [-71.1, -54.5] | 844 trades | TP 12 % | net -49.3 % [-57.2, -38.3] |
| 0 s | TP 3x, 60 min | 432 trades | TP 13 % | net -66.0 % [-73.7, -57.0] | 763 trades | TP 14 % | net -55.4 % [-63.2, -45.5] |
| 5 s | TP 1.5x, 5 min | 481 trades | TP 51 % | net -16.3 % [-21.5, -11.3] | 797 trades | TP 39 % | net -16.2 % [-20.0, -12.8] |
| 5 s | TP 1.5x, 15 min | 452 trades | TP 56 % | net -26.4 % [-32.5, -20.9] | 751 trades | TP 50 % | net -22.5 % [-27.0, -18.0] |
| 5 s | TP 1.5x, 30 min | 421 trades | TP 56 % | net -27.1 % [-33.7, -20.9] | 707 trades | TP 54 % | net -23.2 % [-28.3, -18.7] |
| 5 s | TP 1.5x, 60 min | 368 trades | TP 57 % | net -25.5 % [-33.2, -19.2] | 631 trades | TP 56 % | net -23.9 % [-29.4, -19.3] |
| 5 s | TP 2x, 5 min | 481 trades | TP 26 % | net -14.0 % [-20.2, -5.9] | 797 trades | TP 20 % | net -14.1 % [-18.8, -9.7] |
| 5 s | TP 2x, 15 min | 452 trades | TP 35 % | net -37.5 % [-45.7, -27.4] | 751 trades | TP 29 % | net -28.7 % [-34.6, -21.9] |
| 5 s | TP 2x, 30 min | 421 trades | TP 36 % | net -37.9 % [-46.7, -27.5] | 707 trades | TP 34 % | net -30.7 % [-37.5, -23.8] |
| 5 s | TP 2x, 60 min | 368 trades | TP 36 % | net -37.1 % [-46.3, -26.9] | 631 trades | TP 36 % | net -33.2 % [-40.7, -26.6] |
| 5 s | TP 3x, 5 min | 481 trades | TP 4 % | net -14.6 % [-21.9, -4.3] | 797 trades | TP 3 % | net -14.8 % [-19.6, -8.9] |
| 5 s | TP 3x, 15 min | 452 trades | TP 9 % | net -61.7 % [-68.8, -52.0] | 751 trades | TP 8 % | net -46.0 % [-52.5, -37.3] |
| 5 s | TP 3x, 30 min | 421 trades | TP 12 % | net -67.6 % [-75.4, -58.6] | 707 trades | TP 11 % | net -53.5 % [-60.9, -43.7] |
| 5 s | TP 3x, 60 min | 368 trades | TP 12 % | net -68.2 % [-77.0, -58.8] | 631 trades | TP 13 % | net -58.8 % [-66.6, -50.6] |
| 10 s | TP 1.5x, 5 min | 478 trades | TP 50 % | net -18.1 % [-23.5, -12.2] | 794 trades | TP 38 % | net -17.9 % [-21.3, -14.2] |
| 10 s | TP 1.5x, 15 min | 450 trades | TP 55 % | net -27.9 % [-34.2, -21.4] | 749 trades | TP 50 % | net -23.2 % [-27.5, -18.1] |
| 10 s | TP 1.5x, 30 min | 420 trades | TP 55 % | net -28.7 % [-35.1, -22.0] | 707 trades | TP 53 % | net -24.5 % [-29.2, -19.5] |
| 10 s | TP 1.5x, 60 min | 367 trades | TP 56 % | net -27.4 % [-34.2, -20.8] | 630 trades | TP 55 % | net -25.2 % [-30.3, -20.0] |
| 10 s | TP 2x, 5 min | 478 trades | TP 25 % | net -15.3 % [-22.0, -7.6] | 794 trades | TP 19 % | net -16.0 % [-20.6, -11.6] |
| 10 s | TP 2x, 15 min | 450 trades | TP 35 % | net -36.1 % [-43.9, -27.0] | 749 trades | TP 29 % | net -28.9 % [-34.4, -22.3] |
| 10 s | TP 2x, 30 min | 420 trades | TP 36 % | net -36.8 % [-45.2, -27.9] | 707 trades | TP 34 % | net -31.5 % [-37.7, -24.4] |
| 10 s | TP 2x, 60 min | 367 trades | TP 36 % | net -37.5 % [-46.3, -28.3] | 630 trades | TP 35 % | net -34.8 % [-40.8, -27.7] |
| 10 s | TP 3x, 5 min | 478 trades | TP 5 % | net -14.3 % [-21.8, -4.0] | 794 trades | TP 4 % | net -15.1 % [-19.8, -9.3] |
| 10 s | TP 3x, 15 min | 450 trades | TP 11 % | net -57.2 % [-65.5, -46.3] | 749 trades | TP 10 % | net -43.1 % [-50.0, -33.7] |
| 10 s | TP 3x, 30 min | 420 trades | TP 14 % | net -62.7 % [-71.9, -52.4] | 707 trades | TP 12 % | net -50.1 % [-57.7, -39.7] |
| 10 s | TP 3x, 60 min | 367 trades | TP 15 % | net -62.1 % [-72.3, -51.6] | 630 trades | TP 15 % | net -53.6 % [-61.3, -44.1] |
| 20 s | TP 1.5x, 5 min | 481 trades | TP 46 % | net -20.9 % [-27.4, -16.0] | 811 trades | TP 35 % | net -19.9 % [-23.7, -16.2] |
| 20 s | TP 1.5x, 15 min | 455 trades | TP 52 % | net -31.8 % [-38.1, -26.3] | 765 trades | TP 47 % | net -26.4 % [-30.7, -21.6] |
| 20 s | TP 1.5x, 30 min | 424 trades | TP 51 % | net -33.0 % [-39.0, -27.4] | 721 trades | TP 50 % | net -28.0 % [-32.5, -23.2] |
| 20 s | TP 1.5x, 60 min | 371 trades | TP 52 % | net -32.7 % [-39.2, -26.7] | 645 trades | TP 52 % | net -28.9 % [-33.9, -24.3] |
| 20 s | TP 2x, 5 min | 481 trades | TP 23 % | net -19.4 % [-25.9, -12.0] | 811 trades | TP 17 % | net -18.6 % [-22.9, -14.0] |
| 20 s | TP 2x, 15 min | 455 trades | TP 31 % | net -40.3 % [-47.2, -31.5] | 765 trades | TP 27 % | net -32.2 % [-37.5, -25.2] |
| 20 s | TP 2x, 30 min | 424 trades | TP 33 % | net -41.6 % [-49.9, -32.9] | 721 trades | TP 31 % | net -34.5 % [-40.8, -27.3] |
| 20 s | TP 2x, 60 min | 371 trades | TP 34 % | net -41.7 % [-51.2, -32.8] | 645 trades | TP 33 % | net -37.0 % [-44.2, -30.7] |
| 20 s | TP 3x, 5 min | 481 trades | TP 5 % | net -18.2 % [-26.0, -8.8] | 811 trades | TP 4 % | net -18.1 % [-23.0, -12.1] |
| 20 s | TP 3x, 15 min | 455 trades | TP 11 % | net -56.4 % [-65.2, -45.8] | 765 trades | TP 9 % | net -43.1 % [-50.5, -34.4] |
| 20 s | TP 3x, 30 min | 424 trades | TP 14 % | net -61.6 % [-71.2, -51.5] | 721 trades | TP 12 % | net -49.3 % [-56.7, -38.9] |
| 20 s | TP 3x, 60 min | 371 trades | TP 14 % | net -64.2 % [-74.3, -53.5] | 645 trades | TP 14 % | net -54.2 % [-62.4, -45.6] |
| 30 s | TP 1.5x, 5 min | 486 trades | TP 45 % | net -23.0 % [-28.1, -17.0] | 806 trades | TP 35 % | net -21.3 % [-25.1, -17.7] |
| 30 s | TP 1.5x, 15 min | 462 trades | TP 51 % | net -32.1 % [-38.5, -25.7] | 764 trades | TP 46 % | net -26.7 % [-31.1, -21.6] |
| 30 s | TP 1.5x, 30 min | 431 trades | TP 51 % | net -32.8 % [-39.7, -26.1] | 721 trades | TP 50 % | net -28.1 % [-33.4, -22.7] |
| 30 s | TP 1.5x, 60 min | 377 trades | TP 51 % | net -33.2 % [-40.5, -26.6] | 644 trades | TP 52 % | net -29.6 % [-34.9, -24.1] |
| 30 s | TP 2x, 5 min | 486 trades | TP 20 % | net -22.7 % [-29.0, -15.2] | 806 trades | TP 15 % | net -21.2 % [-25.5, -16.8] |
| 30 s | TP 2x, 15 min | 462 trades | TP 27 % | net -46.5 % [-54.4, -38.6] | 764 trades | TP 24 % | net -36.2 % [-42.4, -30.2] |
| 30 s | TP 2x, 30 min | 431 trades | TP 29 % | net -47.8 % [-57.1, -39.9] | 721 trades | TP 30 % | net -38.2 % [-45.4, -31.4] |
| 30 s | TP 2x, 60 min | 377 trades | TP 29 % | net -48.8 % [-58.5, -40.6] | 644 trades | TP 31 % | net -41.7 % [-48.9, -35.8] |
| 30 s | TP 3x, 5 min | 486 trades | TP 4 % | net -23.1 % [-31.0, -12.3] | 806 trades | TP 3 % | net -22.1 % [-27.8, -16.1] |
| 30 s | TP 3x, 15 min | 462 trades | TP 9 % | net -63.4 % [-71.7, -52.3] | 764 trades | TP 7 % | net -48.9 % [-56.6, -38.7] |
| 30 s | TP 3x, 30 min | 431 trades | TP 11 % | net -69.2 % [-78.1, -58.6] | 721 trades | TP 9 % | net -55.5 % [-63.4, -45.2] |
| 30 s | TP 3x, 60 min | 377 trades | TP 11 % | net -71.9 % [-80.3, -62.9] | 644 trades | TP 11 % | net -62.0 % [-70.0, -52.8] |

Sizes, 10 s delay, TP 2x within 15 min: $100 450 trades | TP 35 % | net -29.0 % [-37.8, -18.8]; $500 450 trades | TP 35 % | net -36.1 % [-43.9, -27.0]; $1000 450 trades | TP 35 % | net -43.6 % [-50.5, -35.6].

## 8 topology, VAL: `gen_share_hub > 0` (419 of 642 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 409 trades | TP 52 % | net -17.7 % [-22.9, -12.6] | 625 trades | TP 42 % | net -20.5 % [-24.9, -16.4] |
| 0 s | TP 1.5x, 15 min | 395 trades | TP 59 % | net -22.8 % [-29.2, -16.3] | 605 trades | TP 51 % | net -22.7 % [-28.2, -16.9] |
| 0 s | TP 1.5x, 30 min | 371 trades | TP 59 % | net -23.7 % [-30.2, -17.0] | 577 trades | TP 56 % | net -22.6 % [-28.0, -16.8] |
| 0 s | TP 1.5x, 60 min | 341 trades | TP 59 % | net -23.4 % [-29.9, -16.6] | 527 trades | TP 58 % | net -23.8 % [-29.3, -17.5] |
| 0 s | TP 2x, 5 min | 409 trades | TP 22 % | net -19.4 % [-26.5, -12.5] | 625 trades | TP 19 % | net -21.1 % [-28.6, -14.8] |
| 0 s | TP 2x, 15 min | 395 trades | TP 36 % | net -36.6 % [-45.2, -28.2] | 605 trades | TP 31 % | net -30.9 % [-40.2, -22.9] |
| 0 s | TP 2x, 30 min | 371 trades | TP 37 % | net -37.0 % [-46.2, -27.9] | 577 trades | TP 35 % | net -29.7 % [-39.1, -21.6] |
| 0 s | TP 2x, 60 min | 341 trades | TP 36 % | net -38.4 % [-47.5, -28.7] | 527 trades | TP 38 % | net -33.1 % [-42.4, -25.0] |
| 0 s | TP 3x, 5 min | 409 trades | TP 6 % | net -17.1 % [-26.6, -8.2] | 625 trades | TP 6 % | net -18.5 % [-29.1, -9.6] |
| 0 s | TP 3x, 15 min | 395 trades | TP 17 % | net -47.5 % [-57.8, -36.9] | 605 trades | TP 16 % | net -36.9 % [-48.3, -27.2] |
| 0 s | TP 3x, 30 min | 371 trades | TP 19 % | net -50.9 % [-62.1, -38.3] | 577 trades | TP 18 % | net -39.6 % [-51.6, -30.0] |
| 0 s | TP 3x, 60 min | 341 trades | TP 19 % | net -50.6 % [-62.6, -37.8] | 527 trades | TP 20 % | net -42.2 % [-53.7, -31.7] |
| 5 s | TP 1.5x, 5 min | 408 trades | TP 51 % | net -18.8 % [-23.7, -13.9] | 624 trades | TP 40 % | net -23.1 % [-27.8, -18.9] |
| 5 s | TP 1.5x, 15 min | 394 trades | TP 58 % | net -24.7 % [-30.4, -18.9] | 604 trades | TP 48 % | net -25.8 % [-31.6, -20.0] |
| 5 s | TP 1.5x, 30 min | 370 trades | TP 58 % | net -25.3 % [-31.3, -19.3] | 576 trades | TP 54 % | net -25.4 % [-31.1, -19.1] |
| 5 s | TP 1.5x, 60 min | 340 trades | TP 57 % | net -25.9 % [-32.1, -19.5] | 526 trades | TP 55 % | net -27.1 % [-33.4, -20.4] |
| 5 s | TP 2x, 5 min | 408 trades | TP 23 % | net -19.8 % [-27.3, -12.7] | 624 trades | TP 19 % | net -22.4 % [-29.9, -16.3] |
| 5 s | TP 2x, 15 min | 394 trades | TP 36 % | net -36.8 % [-45.3, -28.3] | 604 trades | TP 31 % | net -32.2 % [-40.8, -24.4] |
| 5 s | TP 2x, 30 min | 370 trades | TP 37 % | net -35.9 % [-45.1, -27.0] | 576 trades | TP 34 % | net -30.5 % [-39.3, -23.0] |
| 5 s | TP 2x, 60 min | 340 trades | TP 37 % | net -36.8 % [-46.5, -27.4] | 526 trades | TP 37 % | net -33.7 % [-42.8, -25.8] |
| 5 s | TP 3x, 5 min | 408 trades | TP 6 % | net -17.7 % [-27.4, -8.6] | 624 trades | TP 6 % | net -19.9 % [-30.2, -11.3] |
| 5 s | TP 3x, 15 min | 394 trades | TP 17 % | net -47.9 % [-57.0, -38.1] | 604 trades | TP 15 % | net -38.5 % [-48.8, -29.8] |
| 5 s | TP 3x, 30 min | 370 trades | TP 19 % | net -50.8 % [-61.3, -39.4] | 576 trades | TP 17 % | net -41.0 % [-51.8, -32.1] |
| 5 s | TP 3x, 60 min | 340 trades | TP 19 % | net -51.3 % [-62.9, -39.4] | 526 trades | TP 20 % | net -43.6 % [-55.1, -33.4] |
| 10 s | TP 1.5x, 5 min | 407 trades | TP 53 % | net -17.3 % [-22.4, -12.3] | 623 trades | TP 41 % | net -22.1 % [-26.6, -17.7] |
| 10 s | TP 1.5x, 15 min | 394 trades | TP 59 % | net -23.0 % [-29.1, -17.1] | 604 trades | TP 49 % | net -24.2 % [-29.7, -18.7] |
| 10 s | TP 1.5x, 30 min | 370 trades | TP 59 % | net -23.1 % [-29.5, -17.0] | 576 trades | TP 55 % | net -23.6 % [-29.0, -17.7] |
| 10 s | TP 1.5x, 60 min | 340 trades | TP 59 % | net -23.6 % [-30.0, -17.4] | 526 trades | TP 57 % | net -25.1 % [-31.0, -18.5] |
| 10 s | TP 2x, 5 min | 407 trades | TP 23 % | net -20.5 % [-27.3, -13.7] | 623 trades | TP 19 % | net -23.2 % [-30.2, -17.4] |
| 10 s | TP 2x, 15 min | 394 trades | TP 37 % | net -35.8 % [-43.9, -27.6] | 604 trades | TP 30 % | net -32.0 % [-39.9, -25.0] |
| 10 s | TP 2x, 30 min | 370 trades | TP 38 % | net -35.3 % [-43.6, -27.0] | 576 trades | TP 34 % | net -31.1 % [-38.8, -24.3] |
| 10 s | TP 2x, 60 min | 340 trades | TP 37 % | net -35.6 % [-44.4, -26.4] | 526 trades | TP 37 % | net -33.9 % [-41.7, -26.6] |
| 10 s | TP 3x, 5 min | 407 trades | TP 6 % | net -20.3 % [-29.8, -11.4] | 623 trades | TP 5 % | net -21.8 % [-32.0, -13.3] |
| 10 s | TP 3x, 15 min | 394 trades | TP 15 % | net -51.8 % [-61.0, -42.3] | 604 trades | TP 14 % | net -41.1 % [-52.1, -32.1] |
| 10 s | TP 3x, 30 min | 370 trades | TP 17 % | net -55.6 % [-65.7, -45.1] | 576 trades | TP 16 % | net -44.0 % [-55.5, -35.2] |
| 10 s | TP 3x, 60 min | 340 trades | TP 17 % | net -55.5 % [-67.3, -44.2] | 526 trades | TP 18 % | net -46.8 % [-58.2, -37.1] |
| 20 s | TP 1.5x, 5 min | 408 trades | TP 48 % | net -21.8 % [-27.4, -16.1] | 624 trades | TP 38 % | net -25.0 % [-30.5, -20.3] |
| 20 s | TP 1.5x, 15 min | 395 trades | TP 55 % | net -28.2 % [-35.0, -21.6] | 605 trades | TP 46 % | net -27.7 % [-34.2, -21.7] |
| 20 s | TP 1.5x, 30 min | 370 trades | TP 55 % | net -28.9 % [-36.0, -22.1] | 576 trades | TP 52 % | net -26.9 % [-33.3, -20.8] |
| 20 s | TP 1.5x, 60 min | 341 trades | TP 55 % | net -28.5 % [-36.0, -21.4] | 527 trades | TP 54 % | net -28.1 % [-34.6, -21.1] |
| 20 s | TP 2x, 5 min | 408 trades | TP 22 % | net -21.5 % [-28.7, -14.8] | 624 trades | TP 18 % | net -24.0 % [-31.2, -18.1] |
| 20 s | TP 2x, 15 min | 395 trades | TP 37 % | net -34.9 % [-44.1, -25.9] | 605 trades | TP 31 % | net -31.5 % [-40.1, -24.0] |
| 20 s | TP 2x, 30 min | 370 trades | TP 38 % | net -34.2 % [-43.6, -25.1] | 576 trades | TP 35 % | net -30.2 % [-39.1, -22.8] |
| 20 s | TP 2x, 60 min | 341 trades | TP 37 % | net -35.7 % [-45.4, -25.7] | 527 trades | TP 36 % | net -34.4 % [-43.2, -26.4] |
| 20 s | TP 3x, 5 min | 408 trades | TP 5 % | net -22.5 % [-31.3, -14.5] | 624 trades | TP 5 % | net -23.4 % [-33.1, -15.0] |
| 20 s | TP 3x, 15 min | 395 trades | TP 14 % | net -53.8 % [-62.3, -44.2] | 605 trades | TP 13 % | net -42.9 % [-53.4, -33.9] |
| 20 s | TP 3x, 30 min | 370 trades | TP 16 % | net -58.3 % [-67.5, -48.0] | 576 trades | TP 15 % | net -46.4 % [-56.3, -38.0] |
| 20 s | TP 3x, 60 min | 341 trades | TP 16 % | net -58.5 % [-68.7, -48.2] | 527 trades | TP 17 % | net -49.0 % [-59.3, -39.9] |
| 30 s | TP 1.5x, 5 min | 408 trades | TP 46 % | net -23.9 % [-29.1, -18.8] | 624 trades | TP 36 % | net -26.4 % [-31.4, -22.3] |
| 30 s | TP 1.5x, 15 min | 395 trades | TP 55 % | net -28.4 % [-34.2, -22.9] | 605 trades | TP 46 % | net -27.6 % [-33.3, -22.5] |
| 30 s | TP 1.5x, 30 min | 370 trades | TP 55 % | net -27.7 % [-33.4, -21.9] | 576 trades | TP 53 % | net -26.3 % [-32.1, -20.8] |
| 30 s | TP 1.5x, 60 min | 341 trades | TP 56 % | net -27.2 % [-33.0, -21.4] | 527 trades | TP 55 % | net -26.9 % [-32.9, -21.0] |
| 30 s | TP 2x, 5 min | 408 trades | TP 18 % | net -25.4 % [-32.4, -19.1] | 624 trades | TP 15 % | net -26.8 % [-33.8, -20.9] |
| 30 s | TP 2x, 15 min | 395 trades | TP 35 % | net -37.8 % [-46.3, -29.5] | 605 trades | TP 29 % | net -33.8 % [-42.2, -26.8] |
| 30 s | TP 2x, 30 min | 370 trades | TP 36 % | net -37.8 % [-46.6, -29.2] | 576 trades | TP 33 % | net -33.0 % [-41.5, -25.8] |
| 30 s | TP 2x, 60 min | 341 trades | TP 35 % | net -39.0 % [-47.8, -30.3] | 527 trades | TP 35 % | net -36.4 % [-44.7, -28.7] |
| 30 s | TP 3x, 5 min | 408 trades | TP 6 % | net -23.4 % [-32.1, -15.4] | 624 trades | TP 5 % | net -24.2 % [-33.6, -16.0] |
| 30 s | TP 3x, 15 min | 395 trades | TP 15 % | net -51.7 % [-60.9, -42.0] | 605 trades | TP 13 % | net -42.0 % [-52.5, -32.7] |
| 30 s | TP 3x, 30 min | 370 trades | TP 17 % | net -56.1 % [-66.1, -45.9] | 576 trades | TP 16 % | net -45.1 % [-56.1, -36.3] |
| 30 s | TP 3x, 60 min | 341 trades | TP 17 % | net -55.4 % [-65.6, -45.1] | 527 trades | TP 17 % | net -47.8 % [-58.1, -38.9] |

Sizes, 10 s delay, TP 2x within 15 min: $100 394 trades | TP 37 % | net -29.4 % [-38.3, -20.2]; $500 394 trades | TP 37 % | net -35.8 % [-43.9, -27.6]; $1000 394 trades | TP 37 % | net -43.0 % [-50.1, -35.6].

## 9 other aggregates, TRAIN: `hhi_ticket <= 0.25` (209 of 1015 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 191 trades | TP 47 % | net -13.7 % [-19.5, -3.6] | 938 trades | TP 40 % | net -16.5 % [-20.0, -13.3] |
| 0 s | TP 1.5x, 15 min | 181 trades | TP 54 % | net -20.5 % [-28.4, -6.3] | 890 trades | TP 51 % | net -21.2 % [-25.4, -16.9] |
| 0 s | TP 1.5x, 30 min | 175 trades | TP 53 % | net -21.5 % [-29.9, -7.5] | 844 trades | TP 55 % | net -21.8 % [-26.3, -17.4] |
| 0 s | TP 1.5x, 60 min | 156 trades | TP 51 % | net -22.3 % [-31.1, -8.0] | 763 trades | TP 58 % | net -22.0 % [-27.3, -17.8] |
| 0 s | TP 2x, 5 min | 191 trades | TP 30 % | net -6.3 % [-12.5, +3.4] | 938 trades | TP 19 % | net -15.3 % [-19.5, -10.8] |
| 0 s | TP 2x, 15 min | 181 trades | TP 40 % | net -17.8 % [-26.0, -2.9] | 890 trades | TP 30 % | net -27.1 % [-32.7, -20.3] |
| 0 s | TP 2x, 30 min | 175 trades | TP 39 % | net -21.5 % [-31.0, -6.9] | 844 trades | TP 34 % | net -29.9 % [-35.6, -22.8] |
| 0 s | TP 2x, 60 min | 156 trades | TP 37 % | net -25.7 % [-36.7, -9.3] | 763 trades | TP 35 % | net -33.4 % [-39.2, -26.7] |
| 0 s | TP 3x, 5 min | 191 trades | TP 6 % | net -8.0 % [-15.1, +4.8] | 938 trades | TP 3 % | net -15.4 % [-19.9, -10.1] |
| 0 s | TP 3x, 15 min | 181 trades | TP 14 % | net -38.9 % [-51.4, -18.0] | 890 trades | TP 9 % | net -42.5 % [-49.6, -32.8] |
| 0 s | TP 3x, 30 min | 175 trades | TP 17 % | net -42.4 % [-55.3, -20.0] | 844 trades | TP 12 % | net -49.3 % [-57.2, -38.3] |
| 0 s | TP 3x, 60 min | 156 trades | TP 15 % | net -47.9 % [-62.2, -21.4] | 763 trades | TP 14 % | net -55.4 % [-63.2, -45.5] |
| 5 s | TP 1.5x, 5 min | 157 trades | TP 50 % | net -10.5 % [-16.1, +2.5] | 797 trades | TP 39 % | net -16.2 % [-20.0, -12.8] |
| 5 s | TP 1.5x, 15 min | 150 trades | TP 55 % | net -19.1 % [-26.0, -4.3] | 751 trades | TP 50 % | net -22.5 % [-27.0, -18.0] |
| 5 s | TP 1.5x, 30 min | 144 trades | TP 54 % | net -20.3 % [-28.3, -5.4] | 707 trades | TP 54 % | net -23.2 % [-28.3, -18.7] |
| 5 s | TP 1.5x, 60 min | 127 trades | TP 52 % | net -21.6 % [-31.3, -5.3] | 631 trades | TP 56 % | net -23.9 % [-29.4, -19.3] |
| 5 s | TP 2x, 5 min | 157 trades | TP 32 % | net -1.2 % [-6.7, +11.0] | 797 trades | TP 20 % | net -14.1 % [-18.8, -9.7] |
| 5 s | TP 2x, 15 min | 150 trades | TP 42 % | net -15.1 % [-21.9, +0.7] | 751 trades | TP 29 % | net -28.7 % [-34.6, -21.9] |
| 5 s | TP 2x, 30 min | 144 trades | TP 42 % | net -18.1 % [-26.4, -2.4] | 707 trades | TP 34 % | net -30.7 % [-37.5, -23.8] |
| 5 s | TP 2x, 60 min | 127 trades | TP 40 % | net -20.1 % [-30.3, -3.1] | 631 trades | TP 36 % | net -33.2 % [-40.7, -26.6] |
| 5 s | TP 3x, 5 min | 157 trades | TP 8 % | net -6.0 % [-13.8, +8.4] | 797 trades | TP 3 % | net -14.8 % [-19.6, -8.9] |
| 5 s | TP 3x, 15 min | 150 trades | TP 14 % | net -41.7 % [-59.9, -27.9] | 751 trades | TP 8 % | net -46.0 % [-52.5, -37.3] |
| 5 s | TP 3x, 30 min | 144 trades | TP 15 % | net -50.2 % [-69.3, -36.1] | 707 trades | TP 11 % | net -53.5 % [-60.9, -43.7] |
| 5 s | TP 3x, 60 min | 127 trades | TP 12 % | net -57.5 % [-78.1, -42.3] | 631 trades | TP 13 % | net -58.8 % [-66.6, -50.6] |
| 10 s | TP 1.5x, 5 min | 158 trades | TP 48 % | net -13.2 % [-18.6, -0.1] | 794 trades | TP 38 % | net -17.9 % [-21.3, -14.2] |
| 10 s | TP 1.5x, 15 min | 151 trades | TP 54 % | net -19.6 % [-25.8, -5.7] | 749 trades | TP 50 % | net -23.2 % [-27.5, -18.1] |
| 10 s | TP 1.5x, 30 min | 145 trades | TP 53 % | net -20.8 % [-27.4, -7.0] | 707 trades | TP 53 % | net -24.5 % [-29.2, -19.5] |
| 10 s | TP 1.5x, 60 min | 128 trades | TP 51 % | net -22.0 % [-30.3, -6.6] | 630 trades | TP 55 % | net -25.2 % [-30.3, -20.0] |
| 10 s | TP 2x, 5 min | 158 trades | TP 28 % | net -7.2 % [-12.4, +4.6] | 794 trades | TP 19 % | net -16.0 % [-20.6, -11.6] |
| 10 s | TP 2x, 15 min | 151 trades | TP 39 % | net -20.3 % [-27.1, -5.4] | 749 trades | TP 29 % | net -28.9 % [-34.4, -22.3] |
| 10 s | TP 2x, 30 min | 145 trades | TP 39 % | net -23.7 % [-31.6, -7.8] | 707 trades | TP 34 % | net -31.5 % [-37.7, -24.4] |
| 10 s | TP 2x, 60 min | 128 trades | TP 36 % | net -26.4 % [-36.0, -10.2] | 630 trades | TP 35 % | net -34.8 % [-40.8, -27.7] |
| 10 s | TP 3x, 5 min | 158 trades | TP 9 % | net -7.6 % [-13.0, +4.5] | 794 trades | TP 4 % | net -15.1 % [-19.8, -9.3] |
| 10 s | TP 3x, 15 min | 151 trades | TP 15 % | net -38.3 % [-52.6, -21.6] | 749 trades | TP 10 % | net -43.1 % [-50.0, -33.7] |
| 10 s | TP 3x, 30 min | 145 trades | TP 17 % | net -43.7 % [-58.0, -27.0] | 707 trades | TP 12 % | net -50.1 % [-57.7, -39.7] |
| 10 s | TP 3x, 60 min | 128 trades | TP 16 % | net -46.4 % [-63.0, -28.7] | 630 trades | TP 15 % | net -53.6 % [-61.3, -44.1] |
| 20 s | TP 1.5x, 5 min | 160 trades | TP 42 % | net -18.3 % [-23.5, -5.4] | 811 trades | TP 35 % | net -19.9 % [-23.7, -16.2] |
| 20 s | TP 1.5x, 15 min | 151 trades | TP 50 % | net -24.8 % [-30.9, -10.5] | 765 trades | TP 47 % | net -26.4 % [-30.7, -21.6] |
| 20 s | TP 1.5x, 30 min | 144 trades | TP 50 % | net -25.9 % [-32.1, -12.4] | 721 trades | TP 50 % | net -28.0 % [-32.5, -23.2] |
| 20 s | TP 1.5x, 60 min | 126 trades | TP 47 % | net -28.4 % [-36.6, -14.9] | 645 trades | TP 52 % | net -28.9 % [-33.9, -24.3] |
| 20 s | TP 2x, 5 min | 160 trades | TP 26 % | net -11.0 % [-15.2, -1.2] | 811 trades | TP 17 % | net -18.6 % [-22.9, -14.0] |
| 20 s | TP 2x, 15 min | 151 trades | TP 38 % | net -23.2 % [-30.8, -6.4] | 765 trades | TP 27 % | net -32.2 % [-37.5, -25.2] |
| 20 s | TP 2x, 30 min | 144 trades | TP 38 % | net -25.5 % [-35.1, -7.5] | 721 trades | TP 31 % | net -34.5 % [-40.8, -27.3] |
| 20 s | TP 2x, 60 min | 126 trades | TP 37 % | net -26.7 % [-37.2, -6.1] | 645 trades | TP 33 % | net -37.0 % [-44.2, -30.7] |
| 20 s | TP 3x, 5 min | 160 trades | TP 8 % | net -14.5 % [-21.3, -1.0] | 811 trades | TP 4 % | net -18.1 % [-23.0, -12.1] |
| 20 s | TP 3x, 15 min | 151 trades | TP 12 % | net -44.1 % [-58.7, -26.0] | 765 trades | TP 9 % | net -43.1 % [-50.5, -34.4] |
| 20 s | TP 3x, 30 min | 144 trades | TP 16 % | net -48.3 % [-65.7, -28.2] | 721 trades | TP 12 % | net -49.3 % [-56.7, -38.9] |
| 20 s | TP 3x, 60 min | 126 trades | TP 15 % | net -51.4 % [-70.9, -29.0] | 645 trades | TP 14 % | net -54.2 % [-62.4, -45.6] |
| 30 s | TP 1.5x, 5 min | 159 trades | TP 43 % | net -18.2 % [-24.5, -9.7] | 806 trades | TP 35 % | net -21.3 % [-25.1, -17.7] |
| 30 s | TP 1.5x, 15 min | 152 trades | TP 49 % | net -26.4 % [-33.6, -16.7] | 764 trades | TP 46 % | net -26.7 % [-31.1, -21.6] |
| 30 s | TP 1.5x, 30 min | 146 trades | TP 48 % | net -28.1 % [-35.4, -17.3] | 721 trades | TP 50 % | net -28.1 % [-33.4, -22.7] |
| 30 s | TP 1.5x, 60 min | 127 trades | TP 44 % | net -31.2 % [-41.0, -20.0] | 644 trades | TP 52 % | net -29.6 % [-34.9, -24.1] |
| 30 s | TP 2x, 5 min | 159 trades | TP 23 % | net -14.8 % [-19.9, -5.4] | 806 trades | TP 15 % | net -21.2 % [-25.5, -16.8] |
| 30 s | TP 2x, 15 min | 152 trades | TP 33 % | net -29.9 % [-41.4, -18.1] | 764 trades | TP 24 % | net -36.2 % [-42.4, -30.2] |
| 30 s | TP 2x, 30 min | 146 trades | TP 35 % | net -30.5 % [-44.1, -18.1] | 721 trades | TP 30 % | net -38.2 % [-45.4, -31.4] |
| 30 s | TP 2x, 60 min | 127 trades | TP 33 % | net -32.0 % [-45.1, -17.9] | 644 trades | TP 31 % | net -41.7 % [-48.9, -35.8] |
| 30 s | TP 3x, 5 min | 159 trades | TP 6 % | net -20.0 % [-31.4, -7.2] | 806 trades | TP 3 % | net -22.1 % [-27.8, -16.1] |
| 30 s | TP 3x, 15 min | 152 trades | TP 9 % | net -53.9 % [-72.3, -37.8] | 764 trades | TP 7 % | net -48.9 % [-56.6, -38.7] |
| 30 s | TP 3x, 30 min | 146 trades | TP 10 % | net -58.9 % [-80.1, -42.6] | 721 trades | TP 9 % | net -55.5 % [-63.4, -45.2] |
| 30 s | TP 3x, 60 min | 127 trades | TP 9 % | net -64.7 % [-85.6, -47.0] | 644 trades | TP 11 % | net -62.0 % [-70.0, -52.8] |

Sizes, 10 s delay, TP 2x within 15 min: $100 151 trades | TP 39 % | net -12.1 % [-19.0, +3.0]; $500 151 trades | TP 39 % | net -20.3 % [-27.1, -5.4]; $1000 151 trades | TP 39 % | net -28.8 % [-36.0, -13.4].

## 9 other aggregates, VAL: `hhi_ticket <= 0.25` (160 of 642 alerts)

| delay | exit | rule | all alerts |
|---:|---|---|---|
| 0 s | TP 1.5x, 5 min | 156 trades | TP 52 % | net -17.4 % [-21.5, -7.8] | 625 trades | TP 42 % | net -20.5 % [-24.9, -16.4] |
| 0 s | TP 1.5x, 15 min | 151 trades | TP 59 % | net -22.3 % [-30.4, -4.7] | 605 trades | TP 51 % | net -22.7 % [-28.2, -16.9] |
| 0 s | TP 1.5x, 30 min | 139 trades | TP 58 % | net -24.7 % [-31.3, -8.8] | 577 trades | TP 56 % | net -22.6 % [-28.0, -16.8] |
| 0 s | TP 1.5x, 60 min | 131 trades | TP 56 % | net -26.0 % [-33.0, -8.4] | 527 trades | TP 58 % | net -23.8 % [-29.3, -17.5] |
| 0 s | TP 2x, 5 min | 156 trades | TP 26 % | net -16.3 % [-32.6, -9.1] | 625 trades | TP 19 % | net -21.1 % [-28.6, -14.8] |
| 0 s | TP 2x, 15 min | 151 trades | TP 42 % | net -26.6 % [-49.8, -14.5] | 605 trades | TP 31 % | net -30.9 % [-40.2, -22.9] |
| 0 s | TP 2x, 30 min | 139 trades | TP 41 % | net -29.0 % [-52.7, -16.6] | 577 trades | TP 35 % | net -29.7 % [-39.1, -21.6] |
| 0 s | TP 2x, 60 min | 131 trades | TP 39 % | net -32.5 % [-53.6, -18.3] | 527 trades | TP 38 % | net -33.1 % [-42.4, -25.0] |
| 0 s | TP 3x, 5 min | 156 trades | TP 11 % | net -9.1 % [-32.2, +0.5] | 625 trades | TP 6 % | net -18.5 % [-29.1, -9.6] |
| 0 s | TP 3x, 15 min | 151 trades | TP 25 % | net -31.1 % [-57.2, -14.9] | 605 trades | TP 16 % | net -36.9 % [-48.3, -27.2] |
| 0 s | TP 3x, 30 min | 139 trades | TP 24 % | net -37.1 % [-65.1, -24.0] | 577 trades | TP 18 % | net -39.6 % [-51.6, -30.0] |
| 0 s | TP 3x, 60 min | 131 trades | TP 23 % | net -41.0 % [-63.6, -26.9] | 527 trades | TP 20 % | net -42.2 % [-53.7, -31.7] |
| 5 s | TP 1.5x, 5 min | 156 trades | TP 49 % | net -20.8 % [-26.8, -9.0] | 624 trades | TP 40 % | net -23.1 % [-27.8, -18.9] |
| 5 s | TP 1.5x, 15 min | 151 trades | TP 55 % | net -27.3 % [-35.5, -9.9] | 604 trades | TP 48 % | net -25.8 % [-31.6, -20.0] |
| 5 s | TP 1.5x, 30 min | 139 trades | TP 54 % | net -29.2 % [-36.6, -11.2] | 576 trades | TP 54 % | net -25.4 % [-31.1, -19.1] |
| 5 s | TP 1.5x, 60 min | 131 trades | TP 53 % | net -30.8 % [-38.6, -11.1] | 526 trades | TP 55 % | net -27.1 % [-33.4, -20.4] |
| 5 s | TP 2x, 5 min | 156 trades | TP 24 % | net -19.3 % [-35.7, -10.7] | 624 trades | TP 19 % | net -22.4 % [-29.9, -16.3] |
| 5 s | TP 2x, 15 min | 151 trades | TP 40 % | net -28.5 % [-48.5, -14.5] | 604 trades | TP 31 % | net -32.2 % [-40.8, -24.4] |
| 5 s | TP 2x, 30 min | 139 trades | TP 40 % | net -30.1 % [-50.0, -12.9] | 576 trades | TP 34 % | net -30.5 % [-39.3, -23.0] |
| 5 s | TP 2x, 60 min | 131 trades | TP 39 % | net -32.3 % [-49.8, -14.2] | 526 trades | TP 37 % | net -33.7 % [-42.8, -25.8] |
| 5 s | TP 3x, 5 min | 156 trades | TP 9 % | net -12.4 % [-35.0, -2.7] | 624 trades | TP 6 % | net -19.9 % [-30.2, -11.3] |
| 5 s | TP 3x, 15 min | 151 trades | TP 24 % | net -33.1 % [-57.9, -16.9] | 604 trades | TP 15 % | net -38.5 % [-48.8, -29.8] |
| 5 s | TP 3x, 30 min | 139 trades | TP 24 % | net -38.8 % [-65.0, -25.9] | 576 trades | TP 17 % | net -41.0 % [-51.8, -32.1] |
| 5 s | TP 3x, 60 min | 131 trades | TP 24 % | net -38.9 % [-63.4, -25.1] | 526 trades | TP 20 % | net -43.6 % [-55.1, -33.4] |
| 10 s | TP 1.5x, 5 min | 156 trades | TP 48 % | net -23.0 % [-28.3, -13.3] | 623 trades | TP 41 % | net -22.1 % [-26.6, -17.7] |
| 10 s | TP 1.5x, 15 min | 151 trades | TP 54 % | net -29.1 % [-36.3, -14.1] | 604 trades | TP 49 % | net -24.2 % [-29.7, -18.7] |
| 10 s | TP 1.5x, 30 min | 139 trades | TP 53 % | net -30.3 % [-37.3, -13.5] | 576 trades | TP 55 % | net -23.6 % [-29.0, -17.7] |
| 10 s | TP 1.5x, 60 min | 131 trades | TP 52 % | net -31.9 % [-39.2, -13.8] | 526 trades | TP 57 % | net -25.1 % [-31.0, -18.5] |
| 10 s | TP 2x, 5 min | 156 trades | TP 23 % | net -20.2 % [-36.2, -11.9] | 623 trades | TP 19 % | net -23.2 % [-30.2, -17.4] |
| 10 s | TP 2x, 15 min | 151 trades | TP 39 % | net -30.6 % [-49.6, -16.9] | 604 trades | TP 30 % | net -32.0 % [-39.9, -25.0] |
| 10 s | TP 2x, 30 min | 139 trades | TP 39 % | net -32.4 % [-51.0, -16.8] | 576 trades | TP 34 % | net -31.1 % [-38.8, -24.3] |
| 10 s | TP 2x, 60 min | 131 trades | TP 37 % | net -36.0 % [-51.5, -17.5] | 526 trades | TP 37 % | net -33.9 % [-41.7, -26.6] |
| 10 s | TP 3x, 5 min | 156 trades | TP 9 % | net -13.2 % [-35.6, -4.0] | 623 trades | TP 5 % | net -21.8 % [-32.0, -13.3] |
| 10 s | TP 3x, 15 min | 151 trades | TP 23 % | net -35.1 % [-58.2, -20.0] | 604 trades | TP 14 % | net -41.1 % [-52.1, -32.1] |
| 10 s | TP 3x, 30 min | 139 trades | TP 23 % | net -40.3 % [-65.1, -27.0] | 576 trades | TP 16 % | net -44.0 % [-55.5, -35.2] |
| 10 s | TP 3x, 60 min | 131 trades | TP 22 % | net -42.5 % [-63.6, -28.3] | 526 trades | TP 18 % | net -46.8 % [-58.2, -37.1] |
| 20 s | TP 1.5x, 5 min | 156 trades | TP 44 % | net -25.0 % [-37.7, -15.1] | 624 trades | TP 38 % | net -25.0 % [-30.5, -20.3] |
| 20 s | TP 1.5x, 15 min | 151 trades | TP 53 % | net -29.2 % [-43.0, -14.6] | 605 trades | TP 46 % | net -27.7 % [-34.2, -21.7] |
| 20 s | TP 1.5x, 30 min | 139 trades | TP 52 % | net -31.3 % [-45.3, -16.8] | 576 trades | TP 52 % | net -26.9 % [-33.3, -20.8] |
| 20 s | TP 1.5x, 60 min | 131 trades | TP 50 % | net -33.9 % [-45.8, -17.1] | 527 trades | TP 54 % | net -28.1 % [-34.6, -21.1] |
| 20 s | TP 2x, 5 min | 156 trades | TP 24 % | net -19.4 % [-37.4, -9.5] | 624 trades | TP 18 % | net -24.0 % [-31.2, -18.1] |
| 20 s | TP 2x, 15 min | 151 trades | TP 40 % | net -29.8 % [-54.0, -16.4] | 605 trades | TP 31 % | net -31.5 % [-40.1, -24.0] |
| 20 s | TP 2x, 30 min | 139 trades | TP 39 % | net -31.9 % [-57.0, -16.1] | 576 trades | TP 35 % | net -30.2 % [-39.1, -22.8] |
| 20 s | TP 2x, 60 min | 131 trades | TP 37 % | net -35.4 % [-56.6, -18.4] | 527 trades | TP 36 % | net -34.4 % [-43.2, -26.4] |
| 20 s | TP 3x, 5 min | 156 trades | TP 10 % | net -11.6 % [-35.7, -0.3] | 624 trades | TP 5 % | net -23.4 % [-33.1, -15.0] |
| 20 s | TP 3x, 15 min | 151 trades | TP 24 % | net -35.0 % [-60.6, -16.1] | 605 trades | TP 13 % | net -42.9 % [-53.4, -33.9] |
| 20 s | TP 3x, 30 min | 139 trades | TP 23 % | net -40.3 % [-67.0, -20.8] | 576 trades | TP 15 % | net -46.4 % [-56.3, -38.0] |
| 20 s | TP 3x, 60 min | 131 trades | TP 22 % | net -42.3 % [-66.9, -20.6] | 527 trades | TP 17 % | net -49.0 % [-59.3, -39.9] |
| 30 s | TP 1.5x, 5 min | 156 trades | TP 47 % | net -22.5 % [-29.3, -13.0] | 624 trades | TP 36 % | net -26.4 % [-31.4, -22.3] |
| 30 s | TP 1.5x, 15 min | 151 trades | TP 55 % | net -25.9 % [-32.7, -12.0] | 605 trades | TP 46 % | net -27.6 % [-33.3, -22.5] |
| 30 s | TP 1.5x, 30 min | 139 trades | TP 55 % | net -26.6 % [-33.6, -10.7] | 576 trades | TP 53 % | net -26.3 % [-32.1, -20.8] |
| 30 s | TP 1.5x, 60 min | 131 trades | TP 53 % | net -28.0 % [-34.7, -11.8] | 527 trades | TP 55 % | net -26.9 % [-32.9, -21.0] |
| 30 s | TP 2x, 5 min | 156 trades | TP 21 % | net -19.2 % [-34.1, -10.0] | 624 trades | TP 15 % | net -26.8 % [-33.8, -20.9] |
| 30 s | TP 2x, 15 min | 151 trades | TP 40 % | net -27.7 % [-46.6, -11.4] | 605 trades | TP 29 % | net -33.8 % [-42.2, -26.8] |
| 30 s | TP 2x, 30 min | 139 trades | TP 40 % | net -29.4 % [-48.1, -9.6] | 576 trades | TP 33 % | net -33.0 % [-41.5, -25.8] |
| 30 s | TP 2x, 60 min | 131 trades | TP 37 % | net -32.9 % [-47.8, -10.7] | 527 trades | TP 35 % | net -36.4 % [-44.7, -28.7] |
| 30 s | TP 3x, 5 min | 156 trades | TP 9 % | net -12.9 % [-32.5, -3.3] | 624 trades | TP 5 % | net -24.2 % [-33.6, -16.0] |
| 30 s | TP 3x, 15 min | 151 trades | TP 23 % | net -35.0 % [-56.1, -17.8] | 605 trades | TP 13 % | net -42.0 % [-52.5, -32.7] |
| 30 s | TP 3x, 30 min | 139 trades | TP 22 % | net -40.7 % [-62.5, -23.9] | 576 trades | TP 16 % | net -45.1 % [-56.1, -36.3] |
| 30 s | TP 3x, 60 min | 131 trades | TP 21 % | net -42.7 % [-61.2, -20.7] | 527 trades | TP 17 % | net -47.8 % [-58.1, -38.9] |

Sizes, 10 s delay, TP 2x within 15 min: $100 151 trades | TP 39 % | net -23.7 % [-45.1, -8.9]; $500 151 trades | TP 39 % | net -30.6 % [-49.6, -16.9]; $1000 151 trades | TP 39 % | net -38.2 % [-55.0, -25.6].

## Summary

Estimable VALIDATION cells: 300; with a net mean whose CI is above 0: 0.
