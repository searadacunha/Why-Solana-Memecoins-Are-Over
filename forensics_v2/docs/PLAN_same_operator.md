# Plan: do the wallets not established behave like the author's other wallets?

Written and committed before these measures are computed. Results stay in the private folder; this page has no figure from them.

`PLAN_attribution_2024.md` gives each wallet a level from transfers and cards. That rule stays as it is: nothing here changes a level. If this test finds something, it is reported as new evidence, and changing a level needs a dated amendment decided by the author.

**Where the idea came from.** Reading the first and last dates of three wallets not established, one wallet seemed to stop when the next began. The second measure comes from that glance, so it is not independent of those three wallets. They stay in the test, and the report says so.

## Two measures

The bot of the cards takes a fee on each trade, and its settings belong to the person using it, not to one wallet. One person using several wallets should therefore show the same settings at the same time, and may use them one at a time.

A trade is a successful transaction of the wallet with a token change and a transfer to the bot's fee account `9yMwSPk9…`.

- **M1, same settings:** for each of the wallet's trades, the reference trade on the same side (buy or sell) nearest in time, within 24 hours. `M1_tip` is the share with the same Jito tip in lamports, in that wallet's own transactions of the same slot. `M1_prio` is the share with the same fee above the 5,000 lamports per signature.
- **M2, one at a time:** the wallet's trades fall into 10-minute bins. M2 is the share of those bins in which a reference wallet also trades.

A wallet with fewer than 10 comparable trades is reported as `insufficient`.

**Reference:** the CERTAIN and PROBABLE wallets, without the wallet measured. PROBABLE is a weaker level, which is a limit of the reference.

## Comparison groups

- **Positive control:** each of the 8 CERTAIN wallets against the others, leaving itself out. A measure that fails here says nothing.
- **Negative control:** 30 other users of the same bot, read in the same period. 30 moments drawn uniformly from 2024-09-15 to 2025-01-31 with `random.Random(20261105)`. At each one, a page of the bot's fee account, and the first fee payer outside the perimeter and outside the wallets already read. Then up to 3 pages of that wallet from 3 days before the moment. Nothing shows that they are unrelated to the author. They are only a random draw of the bot's users.

## How it will be read

- A measure **qualifies** if at least 6 of the CERTAIN wallets with enough trades beat the negative control: above its 95th percentile for M1, below its 5th percentile for M2. A measure that does not qualify is not used. If none qualifies, the report says the test cannot tell, and stops.
- A wallet **matches** if it beats the same limits on every qualifying measure. Otherwise it **does not match**. A match says the behaviour fits one person's settings. It does not prove it: two people can share settings, or one person can lend a key.
- The 8 lookalike addresses have no trades and are not measured. The 25 PROBABLE wallets are reported too, against the others, as a check of that level, never as a change to it.

## Also listed, no test

Shared funders and destinations of the wallets not established with CERTAIN or PROBABLE wallets, leaving out exchanges, the gateway and services. Each wallet's first and last trade, in order. These describe, nothing more.

## Resources

At most 1,500 credits for the negative control, on the pool's keys. Everything else is already cached. A stop keeps what was read and is reported.
