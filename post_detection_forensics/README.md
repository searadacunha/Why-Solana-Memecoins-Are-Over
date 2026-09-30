# Post-detection forensics: does the on-chain structure of a bundle snipe say which ones double?

The third study on the detector's alerts, after [post_detection_edge](../post_detection_edge/README.md),
which found a statistical signal and no tradable edge and whose survivor turned out to be, on audit,
mostly the actor label and the entry premium. This one asks a narrower question, set up to be refuted:

> Is there an on-chain structure, observable before the entry, that separates the bundle snipes
> that double quickly (a 2x from the alert price confirmed by two reads within 15 minutes) from the
> others, beyond what the actor label and the entry premium already carry?

**Answer: NO ROBUST ON-CHAIN SEPARATION FOUND.** The price at entry and the operator family explain
what separates; the on-chain features add some ROC-AUC on top of them, but not at the confidence the
plan fixed before the table was frozen.

On 1,657 alerts (2026-08-21 to 09-29), 1,502 with an observed 15-minute window:

| | |
|---|---|
| confirmed 2x within 15 min, TRAIN / VALIDATION | 22.4 % / 26.4 % |
| P0, entry premium, pool reserve, market cap | one variable (Spearman 0.91 to 0.98) |
| actor label and premium | the same information (off-diagonal cells: 15 and 6 alerts) |
| on-chain features on top of actor and premium, VALIDATION ROC-AUC | +0.063 [-0.018, +0.114] |
| best selection, top 20 % of the screened model, VALIDATION | 45.5 % (51/112), all inside the cheap "single" corner, 71 of 112 from one operator |
| rules evaluated / reaching 70 % in TRAIN | 1,582,590 / 0 |
| common funding among similar launches, TRAIN / VALIDATION | +6.6 / -21.8 points: the sign flips |
| early buyers with a fresh wallet majority | 0 alerts: they are all seasoned bots |

The account, sections A to H, is in [results.md](results.md). The plan, its verdict rules and every
amendment made before the table was frozen are in [analysis_plan.md](analysis_plan.md); the verdict is
applied by `code/ana_90_verdict.py`, not written by hand.

## Layout

| path | content |
|---|---|
| `analysis_plan.md` | the steps, the labels, the robustness variants and the verdict rules, fixed before the table was frozen, with the dated amendments |
| `feature_dictionary.md` | every feature: family, exact source, causal status (PRE_ENTRY, POST_ENTRY, UNKNOWN) |
| `temporal_leakage_audit.md` | per feature: source, timestamp or slot used, cut-off, verdict SAFE / LEAK / AMBIGUOUS; then the empirical check on untruncated windows |
| `ticket_reconciliation_phase3.md` | the per-wallet SOL of the creation-slot buyers, old parser against the corrected one and against the detector's tickets |
| `data/onchain_cache/` | the raw on-chain windows and wallet histories, fetched from Helius. Not committed (size), rebuilt by the collection scripts |
| `derived/` | `analytic_table.jsonl.gz`, the frozen analytic table, and `TABLE_FREEZE.json`, its sha256, row counts and coverage; the step outputs (`D*_summary.json`, the kept rule and model) |
| `tables/` | `D0` (the dry run on synthetic tables) to `D9` (the verdict) |
| `code/` | the scripts below, standard library only |

## Data

One row per detector alert of the first snapshot of `post_detection_edge/data/` (1,657 alerts,
2026-08-21 to 2026-09-29 11:23 UTC). TRAIN is before 2026-09-15 00:00 UTC, VALIDATION from then to the
snapshot. VALIDATION was the previous study's TEST and was read once there. The future TEST (alerts
after the snapshot) is a separate question and is not touched here.

Per alert, from Helius: every transaction on the mint from the creation slot to the alert + 30 s
(`col_10_windows.py`); then, for the core wallets (5 SOL or more on the curve in the creation slot),
the creator and the first 25 other buyers, their earlier history and their genesis funding, and the
funders walked back two more hops, each before its earliest funding in the corpus
(`col_20_wallets.py`). Features are computed at four cut-offs: alert - 1 s (the primary), - 2 s,
- 5 s, and + 29 s for the +30 s entry variant. The raw window is truncated at the cut-off before
anything is parsed.

## Reproduce

Collection (network, Helius keys in the untracked `post_detection_forensics/.helius_keys`, one per
line or comma-separated):

```bash
sh post_detection_forensics/code/run_collection.sh
```

Freeze, once:

```bash
python3 post_detection_forensics/code/ana_00_freeze.py
```

Checks and analysis (offline, on the frozen table; `ana_lib.load` refuses a table whose sha256 differs
from `TABLE_FREEZE.json`):

```bash
python3 post_detection_forensics/code/qa_10_leakage.py
python3 post_detection_forensics/code/qa_20_tickets.py
sh post_detection_forensics/code/run_analysis.sh
```

`run_analysis.sh` runs `ana_10` (winners against losers, every feature) to `ana_90` (the verdict,
applied by code from the plan's rules). Every step reads only the frozen table, except `ana_40`
(funding per sniper), which also reads the wallet histories of `data/onchain_cache/`. The `mod_*` scripts and `snap_50_freeze_test.py` belong to the
first design of this phase (a 1 h target and a locked model set) and are not run by this analysis;
the future TEST will be evaluated on the signals this analysis keeps.

## Corrections made before the table was frozen

- Per-wallet SOL of a creation-slot buy: read from each wallet's own System transfers to the curve,
  not split pro rata of tokens (off by up to 20 SOL in multi-wallet transactions).
- The creator's own first buy, inside the creation transaction, was never read as a buy (the curve's
  token balance rises there). It is now, and counts as a bundle ticket at 5 SOL or more, as the
  detector counts it. `b_creator_buy_sol` read a field the parser never wrote and was 0 everywhere.
- Remaining curve SOL could read past the cut-off: the raw window is now truncated before parsing.
- SOL/USD: the previous hour's close, not the alert hour's.
- A funder's hub status: measured before its earliest funding in the corpus, not with today's history.
- Solana transaction version 1 (on mainnet from mid-September 2026): requests capped at version 0
  failed on 542 windows, nearly every alert from 2026-09-15 on; the collectors now ask for version 1.
  The detector still reads with the old cap, so on 20 alerts (2026-09-17 to 09-27) it missed a sniper
  who bought through a version-1 transaction. The bundle features count that sniper: they describe
  the chain, while the alert population is what the detector raised, blind spot included.
