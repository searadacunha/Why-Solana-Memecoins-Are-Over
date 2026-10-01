# F. Operator robustness (G1 KNOWN vs UNKNOWN, primary target)

| split | full | without the dominant operator | within operators (Mantel-Haenszel) | operator-level means (operators with both) | strict non-hub funder (G2) |
|---|---|---|---|---|---|
| TRAIN | 60.3 % (N 380) vs 41.9 % (N 310): +18.3 pts [+8.5, +26.3], p 2.27e-06 | 57.9 % (N 252) vs 41.1 % (N 282): +16.8 pts [+5.7, +26.6], p 0.000146 | +8.1 pts [-9.2, +18.4], 47 operators, N 445 | 47 operators: 61.3 % vs 58.5 % | 66.7 % (N 39) vs 51.2 % (N 750): +15.5 pts [+4.5, +38.9], p 0.0834 |
| VAL | 61.2 % (N 227) vs 33.6 % (N 253): +27.6 pts [+16.4, +38.4], p 1.95e-09 | 61.2 % (N 183) vs 32.2 % (N 242): +29.0 pts [+17.4, +39.9], p 4.19e-09 | +20.0 pts [+6.3, +38.5], 36 operators, N 261 | 36 operators: 65.3 % vs 39.0 % | 47.6 % (N 21) vs 49.1 % (N 601): -1.5 pts [-48.2, +11.8], p 1 |

## Leave one operator out (VALIDATION, the 10 largest operators)

| operator left out | alerts | KNOWN vs UNKNOWN |
|---|---:|---|
| k:21.13+21.08+19 | 106 | 61.2 % (N 183) vs 32.2 % (N 242): +29.0 pts [+17.4, +39.9], p 4.19e-09 |
| k:34.57+29.63+9. | 34 | 61.2 % (N 227) vs 36.9 % (N 222): +24.3 pts [+13.7, +35.1], p 3.82e-07 |
| k:32.56+24.69+14 | 20 | 61.2 % (N 227) vs 35.0 % (N 234): +26.2 pts [+14.7, +37.6], p 2.63e-08 |
| k:20.57+20.30+19 | 20 | 61.2 % (N 227) vs 33.9 % (N 251): +27.4 pts [+16.0, +37.8], p 3.04e-09 |
| c:DKiwf4Dv3j7UoR | 18 | 61.4 % (N 210) vs 33.7 % (N 252): +27.7 pts [+15.9, +38.5], p 4.06e-09 |
| c:2AExfZPGVRGxbK | 16 | 61.3 % (N 212) vs 33.7 % (N 252): +27.6 pts [+16.1, +38.4], p 4.25e-09 |
| c:8peR5ucxZnSFWY | 14 | 61.7 % (N 214) vs 33.3 % (N 252): +28.3 pts [+16.9, +38.6], p 1.39e-09 |
| c:5MSpdabaEo18hZ | 14 | 61.7 % (N 214) vs 33.7 % (N 252): +28.0 pts [+16.6, +38.5], p 2.41e-09 |
| c:8uM3AeYfpA88Z7 | 14 | 60.1 % (N 218) vs 33.5 % (N 248): +26.6 pts [+15.2, +36.7], p 1.27e-08 |
| k:20.33+20.14+19 | 13 | 62.6 % (N 222) vs 33.9 % (N 251): +28.7 pts [+16.9, +39.0], p 5.82e-10 |
