| horizon | n with candle | no candle | median multiple | 95% CI       | p25 / p75   | % > 1 | high median | whole-population median |
|---------|---------------|-----------|-----------------|--------------|-------------|-------|-------------|-------------------------|
| +1 h    | 189           | 2 (1 %)   | 0.48            | [0.38, 0.61] | 0.03 / 0.94 | 18.5  | 0.86        | 0.47                    |
| +2 h    | 185           | 6 (3 %)   | 0.43            | [0.29, 0.54] | 0.03 / 0.92 | 18.4  | 0.56        | 0.41                    |
| +4 h    | 179           | 12 (6 %)  | 0.38            | [0.26, 0.49] | 0.02 / 0.82 | 15.6  | 0.43        | 0.30                    |
| +24 h   | 144           | 47 (25 %) | 0.20            | [0.05, 0.29] | 0.02 / 0.60 | 12.5  | 0.22        | 0.03                    |


n = 191 tokens | 27 clusters. Bought at the robust price of the last 120 seconds of the capture (~t0+20 min), converted to USD; sold at the `close` of the nearest hourly candle (90 min tolerance).
`high median` = median of the expiry candle's high: an OPTIMISTIC bound (it assumes selling at the hour's high).
`whole-population median` counts as 0.00x the tokens that no longer have ANY candle at expiry, i.e. no trading left at all: the honest convention for an asset that can no longer be sold.
Units control (GT price in USD / swap price in SOL) / (SOL in USD) = **0.850** median on n=277 tokens. Close to 1: the SOL->USD conversion is correct. Without it, every multiple in this table would be multiplied by ~76.

Prerequisites: `python3 code/fetch_sol_usd.py` then `python3 code/fetch_gt_ohlcv.py`.
Regenerate: `python3 code/t5_horizon_1h_24h.py`
