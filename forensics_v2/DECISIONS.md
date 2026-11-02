# Decisions

Append only. Each line says what was chosen and why. Anything that needs the author's call is in BLOCKERS.md.

## 2026-11-02

1. **Branch and base.** Worktree `WSMO-forensics-v2`, branch `forensics-v2`, from `origin/main` at `6565245`. Nothing outside
   `forensics_v2/` changes; `tests/test_integrity.py` enforces it.
2. **External volume.** `solana_forensics_v2/` on the APFS image `PHI-Data`, chosen by config and never by name in code. The
   FAT32 disk underneath cannot hold permissions or files over 4 GiB. That disk is a mechanical USB drive (about 230 IOPS as
   measured by the PolySentinel session), not an SSD, so the design avoids small files.
3. **Key pool.** Five keys used. Three study keys and two from an old backup file. Six stay out of the pool because services
   or scripts use them. No key value is copied anywhere: sources and fingerprints only.
4. **Credit ceiling.** 300,000 credits for this mission, in `~/.config/forensics_v2/config.json`, plus a ceiling per run. The
   project rule asks for a numeric cap on Helius calls, and the mission did not give one, so this one is mine and is reported.
5. **Rate.** At most 8 requests per second per key and 10 overall, below the free plan's documented 10 per key. The overall
   limit is deliberate: it means the pool spreads credits and does not add speed, because whether several free accounts are
   allowed was not established (BLOCKERS.md).
6. **`getTransactionsForAddress` over signature walks.** Checked against the classic path on one wallet: same 88 transactions,
   same decoded result. Ten times cheaper, gives the exact order inside a slot, and returns inflows to token accounts.
7. **Second decoder.** The node's own `jsonParsed` reading, an implementation independent of ours, used for comparison.
   `solana-dex-parser` stays quarantined: it would mean installing and running third-party code, and the node's parser
   already gives an independent reading of transfers. It does not cover venue-level swap decoding.
8. **Rejected after reading their source** (`docs/EXTERNAL_REPOS_AUDIT.md`): yellowstone-grpc (no history, AGPL), polars
   (DuckDB covers it), splink (its calibration assumptions do not hold for wallet features), the memecoin dataset as a control
   (survivorship, 20 days, labels are forward returns), searcher-examples as a source of bundle membership (none public).
9. **Trades of the author: reuse.** The frozen `historical_edge_2024` study already holds a ledger of his trading wallets.
   This engine re-derives it rather than collecting again; results go to the git-ignored `private_trades/`.
10. **Time limit on 2026 reads.** Nothing at or after 2026-09-22 00:00 UTC, so that the untouched 22-29/09 sample and the future
    TEST stay untouched. No price or outcome file is opened for the co-signer study.
11. **Commit trailers.** No `Co-Authored-By` line in this repository's commits: the author removed them on 2026-08-19.
