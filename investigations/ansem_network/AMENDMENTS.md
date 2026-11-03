# Amendments to PLAN.md

Dated. The plan itself was not rewritten.

## 2026-11-03

1. **Seeds of the rarity test.** Fixed after step 1 as planned: the creation-slot wallets and `GV6UUmNx`. Six of the ten are not in the local corpora, so only four were tested. Written in `evidence/rarity.json`.
2. **The rarity comparison group is small.** The group of like wallets holds 0 to 4 wallets for each seed. Empirical p-values carry the conclusion, not the rank in the group.
3. **Tests added after seeing data, all exploratory:** posts against launches (`code/ana_40_posts.py`), Kolscan overlap (`code/ana_50_numbers.py`), the deployer's fee pushes by recipient (`code/ana_11_deployer_cranks.py`), one-slot groups (`code/ana_50_numbers.py`). No correction for multiple tests. They were prompted by what the chain showed.
4. **Rule added: a token transfer counts as sent by a wallet only if that wallet signed it.** Found while reading the data: Token-2022 permanent delegates move balances without the holder. Without this rule there would be a false return flow.
5. **Mint-window walk cut.** The window of 21 to 25 June was skipped for cost, the rest read. Stated in the report's limits.
6. **Two addresses were first typed from their prefixes and were wrong** (`CEUA7zVo...`, `6gUCcs86...`). They returned no transactions, which exposed the error, and cost 40 credits. All addresses now come from query output, and `code/resolve.py` plus a test enforce it.
7. **Rung R4 is not claimed for the family.** The plan requires a rarity test that rejects chance. The planned test looks at co-sniping, and it does not reject chance here. The direct flows stay at R3.

Credits used: see `RUN_MANIFEST.json`. The ceiling of 150,000 was not raised.
