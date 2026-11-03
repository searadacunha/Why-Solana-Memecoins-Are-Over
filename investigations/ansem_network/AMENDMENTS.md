# Amendments to PLAN.md

Dated. The plan itself was not rewritten. Items 8 to 12 were found by an independent audit of the conclusions on the same day.

## 2026-11-03

1. **Seeds of the rarity test.** Fixed after step 1: the creation-slot wallets and `GV6UUmNx`. The plan also listed wallets that received tokens from them within the first hour, and those were dropped apart from `GV6UUmNx`. Six of the ten seeds are not in the local corpora, so only four were tested.
2. **The rarity comparison group is small.** It holds 0 to 4 wallets for each seed. Empirical p-values carry the conclusion, not the rank in the group.
3. **Tests added after seeing data, all exploratory:** the whole table of tests of H1, the comparison group of gifts of at least 100 M tokens, posts against launches (`code/ana_40_posts.py`), Kolscan overlap, the deployer's fee pushes by recipient (`code/ana_11_deployer_cranks.py`), gifts by recipient and one-slot groups. The thresholds in them (15 minutes, 5 SOL, 100 M, 650 M, 3 points) were chosen then. No correction for multiple tests, and there is no test registry for this work.
4. **Rule added: a token transfer counts as sent by a wallet only if that wallet signed it.** Token-2022 permanent delegates move balances without the holder. All 36 mints with unsigned transfers out of `GV6UUmNx` have one.
5. **Mint-window walk cut.** 21 to 25 June was skipped for cost.
6. **Two addresses were first typed from their prefixes and were wrong** (`CEUA7zVo...`, `6gUCcs86...`). They returned no transactions, which exposed the error, and cost 40 credits. All addresses now come from query output, and `code/resolve.py` plus a test enforce it.
7. **R4 is not claimed for the family.** The plan requires a rarity test that rejects chance. The planned test looks at co-sniping, and it does not. The direct flows stay at R3.
8. **Rarity test deviations.** The plan's population included the detector's alerts and launches found by walking the seeds; the test used three local corpora only, because the detector's journal holds no buyer list. The plan's statistic was launch pairs sharing a seed; the code uses each wallet's best partner. The plan's Monte Carlo error is reported in the text only as a bound.
9. **Hub test.** First written with a 1 SOL cut that the plan does not have. The report now uses the plan's 0.01 SOL, and `evidence/shared_addresses.csv` classifies all 29 addresses by owner program and activity. The 500-counterparty service test was run only where stated.
10. **Corrections from the audit.** The comparison group is not independent (at least 6 tied senders). The 15-minute window was recounted from the pool, because the first count missed an aggregator buy. The Ansem wallet's buys and sales were recounted, because a fee-payer filter had dropped 5 transactions. "Adoption" now dates from 28 June, because the 27 June post names no token. Tables that double counted transfers read from both sides were fixed. The rungs are now stated as the plan writes them.
11. **Removed from publication.** The list of wallet-to-person pairs from the third-party Kolscan snapshot. Only counts stay, because the pairs are unverified and one is disputed by the person named.
12. **Handles in links.** Counts of cited accounts go by the handle in the link URL, which X does not verify. 6 of 107 readable citations have another author.
13. **For the author to decide.** Whether these deviations are acceptable for a published conclusion, and whether `BY4StcU9` should be classified before anything cites it.

Credits used: see `RUN_MANIFEST.json`. The ceiling of 150,000 was not raised.
