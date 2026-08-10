| exit policy | n   | median % | median 95% CI % | mean % | mean 95% CI (cluster) % | % winners | % unfilled | median excl % | clusters + | days med>0 |
|-------------|-----|----------|-----------------|--------|-------------------------|-----------|------------|---------------|------------|------------|
| time_1m     | 196 | -5.4     | [-8.6, -2.6]    | -8.6   | [-12.2, -1.4]           | 35.7      | 3.6        | -5.2          | 8/20       | 1/6        |
| time_3m     | 196 | -8.7     | [-13.5, -3.2]   | -9.5   | [-13.5, -2.2]           | 40.8      | 5.6        | -6.2          | 10/20      | 0/6        |
| time_5m     | 196 | -11.7    | [-21.0, -5.6]   | -10.1  | [-17.6, -4.0]           | 40.3      | 10.2       | -8.0          | 8/20       | 1/6        |
| time_10m    | 196 | -13.3    | [-26.0, -4.4]   | -10.3  | [-20.7, +8.2]           | 38.8      | 17.3       | -1.9          | 8/20       | 0/6        |
| time_20m    | 196 | -23.8    | [-42.1, -12.7]  | -10.2  | [-20.7, +10.2]          | 37.8      | 19.4       | -5.7          | 7/20       | 1/6        |
| trail_20    | 196 | -17.8    | [-22.6, -14.3]  | -12.1  | [-19.8, -1.4]           | 32.7      | 6.1        | -16.3         | 9/20       | 0/6        |
| trail_30    | 196 | -24.2    | [-29.5, -14.8]  | -10.9  | [-16.4, -4.5]           | 33.7      | 5.6        | -18.7         | 6/20       | 1/6        |
| trail_40    | 196 | -26.8    | [-36.6, -17.4]  | -12.0  | [-18.7, -1.7]           | 31.6      | 6.1        | -21.3         | 6/20       | 1/6        |
| tp30        | 196 | +22.4    | [+0.5, +22.4]   | -16.4  | [-22.6, -6.3]           | 56.6      | 15.3       | +22.4         | 9/20       | 5/6        |
| tp30_sl35   | 196 | +11.2    | [-17.4, +22.4]  | -14.2  | [-18.4, -5.6]           | 53.1      | 6.6        | +22.4         | 10/20      | 5/6        |
| tp50        | 196 | +3.3     | [-17.5, +27.1]  | -12.9  | [-19.9, +0.5]           | 51.5      | 16.8       | +31.5         | 9/20       | 4/6        |
| tp50_sl35   | 196 | -15.7    | [-29.9, +12.3]  | -11.3  | [-16.3, +0.1]           | 46.9      | 6.6        | +0.2          | 9/20       | 2/6        |
| tp2x        | 196 | -17.4    | [-30.5, -0.7]   | -10.9  | [-19.5, +5.2]           | 42.9      | 19.4       | +5.4          | 8/20       | 1/6        |
| tp2x_sl35   | 196 | -29.5    | [-37.4, -17.0]  | -10.1  | [-16.2, +1.8]           | 37.8      | 6.6        | -18.7         | 9/20       | 1/6        |
| hold_t_safe | 196 | -23.8    | [-42.1, -12.7]  | -10.2  | [-20.6, +10.2]          | 37.8      | 18.9       | -7.9          | 7/20       | 1/6        |


n = 196 tokens | 20 clusters | 6 UTC days | entry at t0+120 s, NO entry filter.
Source: `data/floor_capture_public.jsonl.gz` (645 files, 289 usable captures, rejects {'aucun_buy': 1, 'capture_vide': 352, 'span_swaps_lt_2min': 3}).
Costs: 1 % fees + 2 % adverse slippage per leg = **5.8241 % round-trip**, already deducted.
`median excl` = same computation DROPPING unfilled exits (an optimistic convention, published to show what it manufactures).
**Negative mean on 15/15 policies.** Negative median on 12/15 (9/10 on the canonical 28/07 grid).
**No policy is positive in both median and mean (0/15).** The few positive medians are tight take-profit policies: they often win a little and rarely lose a lot, so their EXPECTATION is the worst of the table (tp30: median +22 %, mean -16 %).
No policy has a 95% CI of the mean (CLUSTER-level bootstrap) entirely above zero: 0/15.
Mean of means over the 15 policies: **-11.3 %** per round-trip.
No multiplicity correction is needed here: the result is NEGATIVE everywhere, and sweeping more policies can only make a negative result harder to obtain by chance.

Regenerate: `python3 code/t1_base_rate_sorties.py`
