# Plan: what are the very active wallets that co-sign for several operators?

Written and committed before any new transaction of these wallets is read. Changing anything after results is a
dated amendment in `forensics_v2/DECISIONS.md`.

## Why

`funder_network/results.md` found that very active wallets co-sign the sweeps of distinct operators, and that one
economic network and a key-holding execution service both predict this. It left the question open. A shared signing
authority is not proof of one human owner.

## Wallets

- **Co-signers:** every very active wallet that signs a downstream transfer as recipient in `funder_network`, rebuilt
  with the rule of `fn_40_posthoc.py` lines 121-134, from the frozen table and its transaction cache, read only.
- **Controls:** the other very active wallets of the same table that never co-sign, same count or all of them if
  fewer, drawn with `random.Random(20261102)`.

## Time

Eight windows spaced evenly from 2026-08-21 00:00 UTC to 2026-09-21 00:00 UTC. Nothing at or after 2026-09-22 00:00 UTC
is read: the 22-29/09 sample and the future TEST (after 2026-09-29 11:23 UTC) stay untouched. At each window start, at
most 100 transactions, oldest first, 10 credits. Ceiling: (co-signers + controls) x 8 x 10 credits. No price, multiple
or outcome file is opened.

## Measures per wallet

Share of its transactions it signs; distribution of signer counts; distinct other signers; share held by the 10 most
frequent; distinct program sets; share matching the four-signer sweep template of `exit_destination`; share of
counterparties that are known wallets of the 24 operators; distinct operators touched; concentration of its outflows
by destination; whether capital of two operators lands in the same wallet.

## How the hypotheses are told apart

Fixed now, reported whichever way it falls, per wallet and overall:

- **Shared execution service, supported if:** at least 100 distinct other signers in the sample, and under 5 % of them
  known operator wallets, and one dominant technical template.
- **Private to the operators, supported if:** at least 50 % of the other signers are known operator wallets.
- **Otherwise: not separated by this sample.**

## Controls and limits

The same measures on the controls say whether co-signers differ from very active wallets in general. Comparisons use
a permutation of the co-signer/control label, 10,000 draws, seed 20261102, with Bonferroni over the measures above.
Eight windows of 100 transactions are a sample of wallets doing up to 140,000 transactions a day, and they show
behaviour in those windows only. Nothing here identifies a person.

New operators found through these wallets are counted and described, and wallets not already public are not named in
a public file.
