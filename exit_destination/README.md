# Exit-wallet destination and economic loop closure

What happens after a sniper moves its tokens to its recurring exit wallet, and whether the capital comes back to
the network that funded the launch. Follows [economic_mechanics](../economic_mechanics/README.md); no price
outcome defines any wallet, path or category.

[analysis_plan.md](analysis_plan.md) was committed with the selection and the collector before any call;
[results.md](results.md) gives sections A to J and the four closing sections.

## Reproduce

From the repository root. The collection needs Helius keys in the environment and writes the raw cache to
`exit_destination/data/cache/` (untracked); the build and the analysis run offline from that cache.

```bash
python3 exit_destination/code/ed_00_select.py      # the sample, from the frozen tables only
HELIUS_API_KEYS=$(cat post_detection_forensics/.helius_keys) FRPC_KEY_RPS=2 \
    python3 exit_destination/code/ed_10_collect.py  # the calls (hard cap 18,000)
python3 exit_destination/code/ed_20_build.py       # the table, its freeze and the integrity checks
python3 exit_destination/code/ed_30_analysis.py    # tables B to J
```
