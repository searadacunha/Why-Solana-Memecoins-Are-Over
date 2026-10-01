# Exit-wallet destination and economic loop closure

What happens after a sniper moves its tokens to its recurring exit wallet, and whether the capital comes back to
the network that funded the launch. Follows [economic_mechanics](../economic_mechanics/README.md); no price
outcome defines any wallet, path or category.

**Answer: for 17 of the 24 operators observed, the loop closes, transfer by transfer.** The exit wallet sells
the tokens on PumpSwap about 80 s after receiving them. Seconds after its last sale, a transaction signed by the
exit wallet and by the recipient sweeps its SOL, through a one-time address and wrapped SOL, to the wallet
that funded that launch's snipers. That wallet then funds the same snipers again about 18 minutes later, behind
a new deployer. The other 7 operators sweep the same way, but to separate, very active wallets that this study
could not follow. Whether all this is one actor or an execution service holding its clients' keys cannot be
told from these data.

| 300 recurring exit wallets, 1,457 events | TRAIN | VALIDATION |
|---|---:|---:|
| events read / launches | 787 / 117 | 670 / 31 |
| outgoing SOL transfers co-signed by the recipient, through a one-time address | 100 % | 100 % |
| transfers to the launch's own funder (any hub status) | 70 % | 53 % |
| events with capital reaching the launch's funder, pre-registered H1 rule (null) | 49 % (2 %) | 53 % (8 %) |
| events whose capital funds a later launch (null) | 62 % (36 %) | 44 % (27 %) |
| capital reaching a deployer network | 0 | 0 |

By operator: 17 send 80 to 100 % of their sweeps to the launch's funder, 7 send 20 % or less, none falls in
between. The event-level p-values overstate the evidence, because behaviour is fixed per operator;
[results.md](results.md) section I explains this, and its section A sums up the study.
[analysis_plan.md](analysis_plan.md) was committed with the selection and the collector before any call.

## Reproduce

From the repository root. The collection needs Helius keys in the environment and writes the raw cache to
`exit_destination/data/cache/` (untracked); everything after it runs offline from that cache.

```bash
python3 exit_destination/code/ed_00_select.py      # the sample, from the frozen tables only
HELIUS_API_KEYS=$(cat post_detection_forensics/.helius_keys) FRPC_KEY_RPS=2 \
    python3 exit_destination/code/ed_10_collect.py  # the calls (hard cap 18,000; 9,757 used)
python3 exit_destination/code/ed_20_build.py       # the table, its freeze and the integrity checks
python3 exit_destination/code/ed_30_analysis.py    # pre-registered tables B to J
python3 exit_destination/code/ed_40_posthoc.py     # table K, the post-hoc checks
```
