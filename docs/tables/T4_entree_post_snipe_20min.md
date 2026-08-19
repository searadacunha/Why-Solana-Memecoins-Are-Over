| entry rule          | n   | clusters | never triggered | median entry t (s) | median multiple | 95% CI       | p25 / p75   | % multiple > 1 | median net PnL % | mean net PnL % | mean 95% CI (cluster) % | mean without the best token % |
|---------------------|-----|----------|-----------------|--------------------|-----------------|--------------|-------------|----------------|------------------|----------------|-------------------------|-------------------------------|
| graduation (+120 s) | 196 | 20       | 0               | 120                | 0.81            | [0.61, 0.93] | 0.06 / 1.33 | 40.3           | -23.8            | -10.2          | [-21, +10]              | -13.8                         |
| retrace -20 %       | 181 | 21       | 32              | 150                | 0.70            | [0.56, 0.91] | 0.04 / 1.27 | 38.1           | -33.7            | -15.6          | [-28, +4]               | -19.5                         |
| retrace -30 %       | 160 | 21       | 58              | 210                | 0.64            | [0.53, 0.84] | 0.03 / 1.26 | 35.0           | -39.6            | -14.0          | [-34, +30]              | -24.2                         |
| retrace -40 %       | 135 | 18       | 84              | 270                | 0.63            | [0.51, 0.84] | 0.03 / 1.20 | 33.3           | -40.5            | +16.6          | [-41, +58]              | -15.2                         |
| retrace -50 %       | 118 | 16       | 102             | 315                | 0.67            | [0.46, 0.80] | 0.00 / 1.04 | 28.0           | -36.8            | +22.3          | [-49, +72]              | -14.1                         |
| retrace -60 %       | 86  | 14       | 134             | 270                | 0.46            | [0.09, 0.73] | 0.00 / 0.97 | 23.3           | -57.0            | +23.9          | [-54, +89]              | -26.3                         |
| retrace -70 %       | 61  | 13       | 157             | 360                | 0.16            | [0.00, 0.51] | 0.00 / 0.85 | 16.4           | -85.0            | +13.1          | [-68, +89]              | -58.0                         |


Source: `data/floor_capture_public.jsonl.gz` (645 files, 289 usable captures). Common exit: hold until the usable end of the capture (<= 20 min).
`median multiple` is gross (before fees); `net PnL` deducts 5.8241 % round-trip.
Every rule is live-safe: a decision taken on a 30 s bucket executes on the next bucket, never at the price that triggered it.
**No post-snipe entry rule reaches a median multiple of 1 on this horizon**; the best is `graduation (+120 s)` at 0.81x (95% CI [0.61, 0.93], n=196).
`never triggered` = the token never offered the requested retracement during the capture; those tokens count in no column.
**Do not read the mean as an edge**: it turns positive on deep retracements (-40 % to -70 %), but two controls in the table rule that out. (a) The 95% CI of the mean, bootstrapped at the cluster level, crosses zero on every one of those rows. (b) Removing the single best token flips all those means back negative. The right tail is fat and carried by a handful of tokens.

Regenerate: `python3 code/t4_entree_post_snipe_20min.py`
