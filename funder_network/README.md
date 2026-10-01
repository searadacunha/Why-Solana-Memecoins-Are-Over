# Funder network and final capital destination

Where the capital goes after the sniper → exit wallet → funder loop, and whether operators that look separate
end up in one capital network. Follows [exit_destination](../exit_destination/README.md). No price outcome is
used, nothing after the start of the future TEST is read, and no wallet is attributed to a person.

**Answer: not as a whole, partly through specific bridges.**
- **Most operators close their own loop.** Capital comes back to their own snipers 97 % of the time (null 13 %).
  It often goes through a very active treasury that both creates the operator's funders and receives its
  proceeds. Operators share fewer wallets than random wiring would give.
- **Two groups are bridged.** One of 7 operators and one of 5 are linked by a few wallets that pool capital and
  pass it on, in order, from one operator's side to another's. For example, 682.5 SOL from c:Gug21's funder,
  then 160 SOL creating c:8uM3's funder a day later.
- **Every recipient co-signs.** In all 408 outgoing transfers of the funders and collectors, the receiving wallet
  signs. These are not exchange deposits. Counting the very active wallets that co-signed receipts from several
  operators joins 14 of the 24 operators. One actor and a service holding its clients' keys cannot be told
  apart from this.

| 62 funders and collectors, 24 operators | value |
|---|---:|
| outgoing SOL to very active wallets / to unseen wallets | 64 % / 32 % |
| outgoing transfers co-signed by the recipient | 408 of 408 |
| non-hub wallets shared by two operators (null A) | 16 (24.7) |
| operators in the largest group, plan's rule (null A) | 7 (16.7) |
| ordered cross-operator capital sequences | 13, through 8 bridges |
| recycling links back to the same operator (null D) | 97 % (13 %) |
| capital reaching deployer networks | 6 SOL, 3 paths |

Scope B (chosen after the estimate of ~9.3 million transactions for a full census): lifecycle endpoints of the 38
short-lived wallets, a sample around the sweeps of the 24 very active ones, at most 5 hops each way; 3,553
calls. [results.md](results.md) gives sections A to J and the four closing sections;
[analysis_plan.md](analysis_plan.md) was committed with the collector before any flow was read.

## Reproduce

From the repository root. The collection needs Helius keys in the environment and writes the raw cache to
`funder_network/data/cache/` (untracked); everything after it runs offline from that cache.

```bash
python3 funder_network/code/fn_00_inventory.py --probe   # population and activity probe (62 calls)
HELIUS_API_KEYS=$(cat post_detection_forensics/.helius_keys) FRPC_KEY_RPS=2 \
    python3 funder_network/code/fn_10_collect.py         # the calls (cap 6,000 on top of the probe)
python3 funder_network/code/fn_20_build.py               # table, freeze, integrity
python3 funder_network/code/fn_30_analysis.py            # pre-registered tables B to J
python3 funder_network/code/fn_40_posthoc.py             # table K, the post-hoc checks
```
