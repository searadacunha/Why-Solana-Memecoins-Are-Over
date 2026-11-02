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
5. **Rate.** At most 10 requests per second per process, spread over the keys, and up to three processes ran at once in this
   session: about 6 per key at worst, under the free plan's documented 10. Whether several free accounts are allowed was not
   established (BLOCKERS.md).
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
12. **Amendment to the burst plan, after results.** The negative control draws 12 members from 12 bursts across the whole sample, not
    one day: 150 bursts over 49 days rarely give 12 on a day. It met none of the outcomes in 200 draws. A one-day version was not run.
13. **Amendment to the co-signer plan, after results.** The plan's verdicts are reported as computed. A post-hoc reading shows the
    "distinct other signers" measure mostly counts disposable keys, so the report says the test does not discriminate. No threshold
    was changed.
13b. **Amendment to the trade-context plan, before reading.** The plan named the trips of frozen class P for group A, inside a sample of curve
    entries. Part of them did not enter on the curve, so group A is smaller than that class. Noticed when drawing the sample, before any launch was
    read. A few trips are in both A and B, and are counted in each group's own row.
13c. **Amendment to the trade-context analysis, before reading any result.** An independent review noted that `window_covers_entry` can be
    true when his own buy was not seen. The reported subset is now `entry_seen`, which needs it. The review also noted S1 and S2 are lower bounds:
    8 buyers per trip, each one's first 100 transactions. The report says so.
13d. **Independent review of the new code, 2026-11-02.** No arithmetic defect. Checked on the data: every direct deposit survives the edge
    rules and the total matches the frozen ledger up to fees, no token account without owner in the 2024 cache, no
    burst member with an empty history. Fixed: a wallet credited twice in a burst counted twice for O3 (124 unchanged, null 48.7 to 48.6); an
    empty final page of `getTransactionsForAddress` is now asked again before it is believed, as signature walks already did. Not re-checked for
    runs before that fix: the 447 empty windows in checkpoints. Over the whole month, 6 of the 8 wallets marked "no activity" in the co-signer
    study do have transactions, so that label means "none in those eight days", no more.
13e. **Credits wasted.** Two verification scripts cost about 11,000 credits for nothing: one spent 3,000 and lost its result, and one had no
    `__main__` guard, so each worker process repeated its network part. Both were mine. Total spent is in RUN_MANIFEST.json.
14. **Work area on the internal disk.** The external drive stalled under several sessions, 5 pages in 8 minutes. The cache runs in
    `~/.local/state/forensics_v2/hot`, capped at 1.5 GB then 1.8 GB, reserved through the disk guard. Past the cap, or near the 13.5 GB floor,
    it continues on the external volume by itself, as the author asked on 2026-11-02; that switch happened once on its own. `sync_cold` copies
    everything out, adding only.
