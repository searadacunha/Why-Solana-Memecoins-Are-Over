| MC band at detection   | n    | ATH already past % | ATH < +60 s % | 95% CI %     | ATH < +120 s % | median ATH delay (min) |
|------------------------|------|--------------------|---------------|--------------|----------------|------------------------|
| 5k-20k                 | 16   | 43.8               | 62.5          | [38.6, 81.5] | 62.5           | 0.1                    |
| 20k-30k                | 108  | 23.1               | 55.6          | [46.2, 64.6] | 60.2           | 0.5                    |
| 30k-40k                | 137  | 27.7               | 60.6          | [52.2, 68.4] | 65.7           | 0.3                    |
| 40k-50k                | 296  | 18.9               | 44.6          | [39.0, 50.3] | 54.4           | 1.7                    |
| 50k-65k                | 277  | 26.4               | 46.6          | [40.8, 52.5] | 51.6           | 1.6                    |
| 65k-85k                | 121  | 26.4               | 52.1          | [43.2, 60.8] | 58.7           | 0.9                    |
| 85k-120k               | 123  | 14.6               | 31.7          | [24.1, 40.4] | 35.8           | 6.7                    |
| 120k-300k              | 165  | 9.7                | 17.6          | [12.5, 24.1] | 23.0           | 36.1                   |
| --- < 20k (aggregated) | 16   | 43.8               | 62.5          | [38.6, 81.5] | 62.5           | 0.1                    |
| --- whole population   | 1243 | 21.3               | 43.8          | [41.1, 46.6] | 50.0           | 2.0                    |


n = 1243 tokens | 123 clusters | 20 UTC days | clean population B.
`detect_ts` = first outside visibility (token `complete` seen <= 12 s after creation). A LOWER bound on a human buyer's latency.
A NEGATIVE median delay means that, within the band, the typical token peaked before it existed for the observer.
Limit: `o_ath_ts` (pump.fun API) and `detect_ts` (local clock) can differ by a few seconds; the three thresholds are published for that reason.

Regenerate: `python3 code/t3_ath_avant_detection.py`
