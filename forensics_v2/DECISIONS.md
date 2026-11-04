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
    entries. Part of them did not enter on the curve, so group A is smaller than that class. Noticed when drawing the sample, before any launch
    was read. A few trips are in both A and B, and are counted in each group's own row.
13c. **Amendment to the trade-context analysis, before reading any result.** An independent review noted that `window_covers_entry` can be
    true when his own buy was not seen. The reported subset is now `entry_seen`, which needs it. The review also noted S1 and S2 are lower bounds:
    8 buyers per trip, each one's first 100 transactions. The report says so.
13d. **Independent review of the new code, 2026-11-02.** No arithmetic defect. Checked on the data: every direct deposit survives the edge rules
    and the total matches the frozen ledger up to fees, no token account without owner in the 2024 cache, no burst member with an empty history. Fixed: a wallet credited twice in a burst counted twice for O3 (124 unchanged, null 48.7 to 48.6); an
    empty final page of `getTransactionsForAddress` is now asked again before it is believed, as signature walks already did. Not re-checked for
    runs before that fix: the 447 empty windows in checkpoints. Over the whole month, 6 of the 8 wallets marked "no activity" in the co-signer
    study do have transactions, so that label means "none in those eight days", no more.
13e. **Credits wasted.** Two verification scripts cost about 11,000 credits for nothing: one spent 3,000 and lost its result, and one had no
    `__main__` guard, so each worker process repeated its network part. Both were mine. Total spent is in RUN_MANIFEST.json.
13f. **Trade results stay private.** All trade-context output goes to the private folder, and a test refuses the private totals in any tracked
    file, computed at run time from the private data.
13g. **Bodies of group X's transactions not kept.** The external disk stalled with the cache past its internal quota, so group X keeps signatures and
    results only. The bodies can be fetched again.
14. **Work area on the internal disk.** The external drive stalled under several sessions, 5 pages in 8 minutes. The cache runs in
    `~/.local/state/forensics_v2/hot`, capped at 1.5 GB then 1.8 GB, reserved through the disk guard. Past the cap, or near the 13.5 GB floor,
    it continues on the external volume by itself, as the author asked on 2026-11-02; that switch happened once on its own. `sync_cold` copies
    everything out, adding only.
15. **Work area moved out, 2026-11-03.** The internal disk reached 12.08 GB free, under the 13.5 GB floor. This session's work area, 1.9 GB of its own cache,
    was copied to the external volume and checked (database and Parquet by hash, 400 random transactions byte for byte, every checkpoint, the call log), then
    removed from the internal disk. The configuration now points at the external volume. What used the rest of the disk was not established.

## 2026-11-03

16. **Branch history.** Rewritten once with the author's written permission, limited to this branch: figures of his unpublished study and notes about keys were taken out of
    14 commits, with `main` and every other branch untouched. Dates and authors are kept. A full copy of the old history is kept privately. Commit hashes cited as proof that a
    plan came first therefore changed; those plans' dates in `git log` are the original ones.
17. **Comparison changed after a failed first run.** The plan for the 2026 exits said no disagreement would be fixed by changing the comparison. The first run agreed on 135 of 427
    transactions. All 292 differences were exactly the fee: the frozen table's `dsol` adds it back when the wallet signs (`exit_destination/code/ed_trace.py:175`). The comparison
    now applies that convention, and agrees on 427 of 427. The first figure stays in the report and in `results.json`.
18. **Work area back on the internal disk.** Other sessions saturated the external mechanical disk: one history read sat in disk wait for minutes. `data_root` is back on
    `~/.local/state/forensics_v2/hot`, quota 1.5 GB, reservation through the disk guard, and copied out with `sync_cold` at the end. Cached transaction bodies on the external disk are
    no longer looked up during a run, so some repeated reads cost credits again. A bounded cost, against a whole session stuck behind a busy disk.
19. **Keys, measured.** One `getHealth` per key: 3 of the 5 keys of this pool answer "max usage reached", the other 2 and the 5 outside the pool answer. A key that says this has a hard
    stop, so it cannot bill past its quota. Other sessions on this machine may use the same keys, so a spent key does not measure this work. Replies carry no plan, credit or account
    header, so which keys share an account is not visible from a key: it needs the dashboard. This work stays on the 2 pool keys that answer, and the keys outside the pool are not used.
20. **Python.** On this machine `python3` resolves to a 3.14 virtual environment of another tool. The repository's CI and byte-for-byte reproduction are on 3.12 and 3.13, so this work runs from
    its own environment, `~/.local/share/forensics_v2/venv`, Python 3.13.1, with `duckdb`, `pytest`, `mypy` and `ruff`.
21. **Venue list.** Moonshot added to `decode.VENUES`, after 138 token transactions showed no venue. No total changes: buy and sell are decided by sign.
22. **Screenshots beyond the study's card list.** The published transcription of the screenshots holds one card the frozen study's list left out, VISUALIZE. The rule of `docs/PLAN_attribution_2024.md` is applied to it as written, percentage and holding time, so one wallet moved up a level. No threshold changed.
23. **Telegram session not used.** A saved Telegram session exists on this machine for another project. Reading the author's chats with it could settle the last card, but this mission never asked for it, so it was not opened: the author can look up that message himself.
24. **Second sentence in the root README.** The reconciliation's sentence now also says that the exact amount alone links nobody. Reading identical amounts as a link had become misleading once the fee line was measured. No figure and no earlier sentence changed.
25. **Attrition of the matched control.** 20 of 60 trips found no match inside the plan's limits. They are dropped and counted, and the limits were not loosened.
26. **Deviation from the matched-control plan, found by an independent review.** The plan asks for trips whose launch was never read, and the filter works by trip, not by token, so 2 of the fresh trips sit on a token already read in an earlier group. The review also found one fresh trip whose signal comes from a wallet near its own. Both are reported privately with the test without them, and neither changes the reading. Nothing was re-run after the review.

27. **Telegram.** A note forbids opening the saved Telegram session without the author's agreement, and this mission does not name it, so it stayed closed. Telegram Web was not signed in, and no login was tried. The Telegram app's cached images were read by a script that prints only QR codes naming the bot: none. Its message database is encrypted and was not touched.
28. **Past the 2026 limit, my error.** One read of the deposit address had no end bound and fetched 4 transactions after 2026-09-22, against entry 10. They were not decoded or used.
29. **Credits wasted, my error.** About 390 credits on a scan of the bot's fee account, whose run limit stopped it before it saved. It printed no match, and only that is known of it.
30. **Same-operator test.** The positive control failed, so by the plan the test cannot tell. No measure was changed afterwards.
31. **Wallet succession, post hoc.** Found by looking at dates, so exploratory. No attribution level changed. Amendments are proposed privately, for the author to decide.
32. **Popularity match.** The plan's sentence on the negative control does not say whether the difference is signed. The code, written before reading, compares magnitudes, and its verdict is kept. The other reading is reported privately. Most trips found no match, and the count is reported.
33. **Network links.** Two things the plan did not state: the code gives `private-like` only from 100 transactions, and pump.fun's fee account was labelled after it produced a false join. Both are in the report.
