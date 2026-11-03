# Tools review: open-source repositories for the Solana investigation

Date: 2026-11-03. Scope: repositories that add a capability to `forensics_v2`. The 15 repositories in `forensics_v2/docs/EXTERNAL_REPOS_AUDIT.md` were not re-audited.

Rules followed: read only. Nothing was cloned, forked, starred or opened as an issue, and no code from any repository was run. Files were read through `gh api`. JSON, CSV and SQL files were parsed as data by my own throwaway scripts in the session scratchpad. Stars were ignored.

Verdict meanings. INTEGRATE: take the named data or method into our stack at the pinned commit, and test it there first. READ ONLY FOR REFERENCE: use it to design or check our own code, do not copy or run it. REJECT: no use here.

## Main findings

1. The official IDL of the fee program exists: `pump-fun/pump-public-docs`, `idl/pump_fees.json`. All 206 instruction and event discriminators across the three pump IDLs recompute correctly, and the two values hand-written in `code/ana_10_deployer.py` match it.
2. Correction to the brief: only `create_fee_sharing_config` and `update_fee_shares(_v2)` live on the fee program. `distribute_creator_fees(_v2)` is on the pump program and `transfer_creator_fees_to_pump(_v2)` is on PumpSwap. A filter on `pfeeUx...` alone will miss them.
3. The latest IDL is not enough for history: `reset_fee_sharing_config` and `_v2` were removed at commit `e0687ae` (2026-09-12). Older transactions need the copy at `3c6721a`.
4. Mapping a transaction to its Jito bundle has one public source, the undocumented explorer API behind `explorer.jito.wtf`. One repository measured about seven days of retention on 2026-10-15. If that holds, it cannot answer for older transactions, and an empty answer there must be read as unknown, never as "not bundled". The sources conflict and I did not test it (section 2).
5. For labels, the strongest sourcing is what exchanges publish themselves (Bitstamp wallet transparency, Bybit proof of reserves), found through DefiLlama. No repository offers KOL labels with per-label sourcing.

## Candidates

| # | Repo and pin | Last push | Licence | What it adds that we do not have | What I read | Security concerns | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | `pump-fun/pump-public-docs` `639b87fb45c3` | 2026-10-13 | None declared | Official IDL of the fee program (31 instructions, 22 events, 9 accounts), IDLs of pump and PumpSwap, account tables for the v2 fee-sharing instructions, and the IDL history in git. | `idl/pump_fees.json`, `idl/pump.json`, `idl/pump_amm.json`, all 8 commits of `idl/pump_fees.json`, `docs/FEE_PROGRAM_README.md` (first 50 lines), `docs/instructions/CREATOR_FEE_SHARING.md` (first 120 lines). | No keys, no scripts. JSON and Markdown only in what I read. `.ts` type files not read. No licence file: check before republishing the files. | INTEGRATE (data) |
| 2 | `hrekokovgmmek-lab/pumpswap-fee-decoder` `c8ef12aa172d` | 2026-10-21 | MIT | A small IDL-driven Borsh decoder, reading the on-chain Anchor IDL account as a second source for the IDL, and a reconciliation check: event totals against the vault balance change. It claims that since late September 2026 the creator fee and half the protocol fee stay in the pool vault until swept (not verified). It does not decode fee-sharing instructions. | `README.md`, `package.json`, `src/idl.ts` (first 110 lines), `src/config.ts`, `scripts/fetch-idl.ts`, pattern scan of `src/breakdown.ts`, instruction names in `idl/pump_fees.json`. | No keys asked. No post-install script. One pinned runtime dependency (`@solana/web3.js` 1.98.4). Default endpoint is the public RPC. Single author, repo two days old at last push. Its vendored IDL is older than the docs repo. | READ ONLY FOR REFERENCE |
| 3 | `LBruyne/solana-sandwich-avengers` `43107597a96c` | 2026-08-27 | MIT | The fullest Jito client: `bundles/transaction/{sig}`, `bundles/slot/{n}` (every bundle of a slot), `bundles/recent`. Measured rate ladder (2 req/s gave 97.5 % success, 4 req/s gave 45 %). A committed map of 25,751 signature to bundle id rows, but only for sandwich legs in slots 408,672,000 to 428,111,999. | `README.md`, `sandwich-detector/README.md` (Jito parts), `sandwich-intent/0_crawl_jito_bundle_ids.py`, `sandwich-detector/jito/request.go`, parts of `recent.go`, `slot.go` and `request_test.go`, `sandwich-detector/.env.example`, `dataset/README.md` (parts), `signature_bundle_map.csv`. | No private keys. `.env` holds RPC keys and ClickHouse credentials. Sends browser headers to the Jito API to reduce Cloudflare rejections. Needs ClickHouse and Go. Go dependencies and parquet files not reviewed. | READ ONLY FOR REFERENCE |
| 4 | `Pratiikpy/opening-cross` `72fee934dc7a` | 2026-10-15 | Apache-2.0 | The only repo I found that measures explorer retention (oldest bundle seven days old, 2026-10-15) and models three states: bundled, not-bundled, unknown. Reads the tip payer from the transfers because `tippers` lists fee payers (3 of 40 live bundles differ). Derives tip accounts from PDA seeds. | `packages/integrity/src/jito.ts` (first 240 lines), root `package.json` scripts. | No key handling in that file. Hard-coded `bundles.jito.wtf`. No post-install at root. The rest of the repo (a market protocol) was not read. | READ ONLY FOR REFERENCE |
| 5 | `hrekokovgmmek-lab/solana-fund-tracer` `39f1296d0d2e` | 2026-10-21 | MIT | Three methods missing from `trace.py`: `sinks` (addresses receiving from several wallets of a group, with one-off intermediaries credited to their origin), `relay` (one exact amount passed wallet to wallet within seconds, reading busy hubs from a block just after the window), `deposit` (exchange deposit address by sweep behaviour). Plus explicit stop reasons: exchange, busy address, loop, dead end. | `README.md`, `fundtrace/labels.py`, `sinks.py`, `trace.py`, `relay.py` (first 120 lines), `parse.py`, `rpc.py` (first 60 lines), `pyproject.toml`. | No keys. Standard library only, no post-install. `subprocess` only as a curl fallback, with list arguments. Default endpoint is the public RPC. `labels` downloads from the `main` branch of Spellbook, unpinned. Single author, 4 commits in one day, generated-looking account name. Weak spots in section 3. | INTEGRATE (methods, rewritten on our decoder) |
| 6 | `SnowBar0v0/crosschain-fund-flow` `a76e1f60a77c` | 2026-07-17 | None declared | An intent taxonomy applied before graph edges exist (only `direct_value_transfer` and `token_owner_transfer` can score; swaps, rent, wraps, bridge legs stay as evidence). Bridge orderbook endpoints for gas.zip, THORChain midgard, Mayan and deBridge, which I did not see in `crosschain.py`. | `README.md`, `references/cluster-expansion.md`, `classification-rules.md`, `bridge-orderbooks.md`, `data/solana_platforms.json`, `scripts/label_match.py`, pattern scan of `scripts/common.py`, `scripts/expand_crosschain_cluster.py` (constants, `classify_solana_transaction`, `analyze_common_patterns`). | No keys in the repo. It is an agent skill: `SKILL.md` and `agents/openai.yaml` are instructions to an agent, not followed and not read. Suggests a logged-in Arkham session. Bridge addresses are "from prior sampling", unsourced. No licence, so nothing can be copied. Code errors in section 3. | READ ONLY FOR REFERENCE |
| 7 | `duneanalytics/spellbook` `2257cb49f091` | 2026-11-02 | BUSL-1.1 (GitHub shows `other`), change date 2027-03-03 to GPLv3+ | 112 Solana exchange addresses across 24 exchanges, with name, `added_by` and `added_date`. Names `FWznbcNX...` as Kraken 1, which `service_attributions.json` only calls an exchange hot wallet. It holds no entry for `G2YxRa6w...` (ChangeNOW). | `dbt_subprojects/hourly_spellbook/models/_sector/cex/addresses/chains/solana/cex_solana_addresses.sql` (parsed in full), `LICENSE` (parameters), commit log of that file. | SQL data only, nothing to run. No per-row evidence: `added_by` is one person for all 112 rows, latest `added_date` 2025-07-07. The licence excludes use for a data or analytics platform: read it before publishing the list. | INTEGRATE (data, tagged as Dune curated) |
| 8 | `DefiLlama/DefiLlama-Adapters` `884590da4092` | 2026-11-03 | None declared | Exchange-published sources: `https://www.bitstamp.net/api/v2/wallet_transparency/` and `https://api2.bybit.com/common-static/por/bybit_por_YYYYMM.csv`. Also 57 Solana addresses for 27 exchanges in `cex/index.js`, mostly smaller ones (Deribit, VALR, Poloniex, BitMEX), and 3 for MEXC. | `cex/index.js` (parsed, `fileConfigs` list), `cex/bybit.js`, `cex/mexc-cex.js`, `projects/bitstamp/index.js`, `projects/helper/cex.js` (first 40 lines). | Adapters are executable Node code with `@defillama/sdk`: parse as text, do not run. No keys in what I read. Only 3 source comments in `cex/index.js`, so most rows carry no evidence. Other `cex/*.js` and `projects/*` not enumerated. | INTEGRATE (addresses and the two published feeds) |
| 9 | `apostleoffinance/Solana-Forensic-Analysis-Tool` `51bae8c98bda` | 2025-06-20 (CSV last changed 2025-04-15) | MIT | `data/raw/solana_cex_labels.csv`: 100,000 Flipside label rows, 99,986 of them exchange deposit wallets (Binance 29,133, Coinbase 20,472, KuCoin 9,172, Bybit 9,169, Gate.io 8,152). Provenance is in `notebooks/05_entity_labeling.ipynb`, cells 4 to 6 (a Flipside Studio query). Nothing else I found comes close for deposit wallets. | The CSV (parsed in full), `notebooks/05_entity_labeling.ipynb` and `notebooks/01_data_exploration.ipynb` (cells matching label sources), README (pattern scan), file tree. | CSV only. App code (`app.py`, frontend) not read, do not run it. Exactly 100,000 rows looks like an export cap (my inference). No per-row date, Flipside's method not shown. Bad rows: 2 lowercased addresses, 1 address in Bitcoin format, 1 BOM row. Its Vybe file has 2,667 keys all lowercased, which destroys base58: unusable. | INTEGRATE (CSV only, tagged INDEXER_REPORTED, lead only) |
| 10 | `Noobmaster169/liquidity-data` (fiber-data) `3d99b4634537` | 2026-10-16 | None declared | The clearest design for LP tracking: typed tables per program and event (PumpSwap `CreatePoolEvent`, `DepositEvent`, `WithdrawEvent`; DLMM `AddLiquidity`, `RemoveLiquidity`, `PositionCreate`, `PositionClose`; DAMM v2 `EvtInitializePool`, `EvtAddLiquidity`, `EvtRemoveLiquidity`, `EvtLockPosition`, `EvtPermanentLockPosition`), a decode-failure table (`unknown_discriminator`, `log_truncated`), CPI and log events deduplicated, and IDL provenance in `idl/SOURCES.md`. `decode.py` has no LP events and no DAMM v2 program id. | `README.md`, `idl/SOURCES.md`, `package.json`, `.env.example`, `src/decoders/events.ts`, `src/decoders/dlmmPosition.ts`, head of `config/venues.json`, pattern scan of `src/rpc.ts`, `src/writer.ts`, `src/cli.ts`, event names in three IDLs. | Only an RPC URL in `.env`. No post-install. One native dependency (`@duckdb/node-api`). `Dockerfile` and `compose.yaml` not read. By its own README it walks whole blocks: 23.9M credits and up to about 770 GB for 90 days, far over our 150,000 credit ceiling. No licence. Created and last pushed on the same day. | READ ONLY FOR REFERENCE |
| 11 | `prezis/scraperx` `e8336a42de05` | 2026-11-02 | MIT | Account timelines and replies without an X account: `https://api.fxtwitter.com/2/profile/{handle}/statuses` and `/2/conversation/{id}`. Keyless search through public Nitter RSS. `col_10_x_posts.py` only reads by post ID. | `scraperx/x_timeline.py` (first 215 lines), `nitter.py` (first 70 lines), `wayback.py` (first 110 lines), `explorer_label.py` (first 90 lines), `github_analyzer/telemetry.py` (header), `pyproject.toml`, README parts, pattern scan of `__main__.py`. | No account, no keys, no `subprocess` or `eval` in the 4 files scanned. Telemetry is a local file. Relays see which handles we ask about. Optional extras to avoid: `stealth` (Cloudflare bypass), `twscrape` (account-backed). The package is large and mostly unrelated. Weak spots in section 6. | INTEGRATE (the endpoint pattern, in `col_10_x_posts.py`, not the package) |
| 12 | `edgi-govdata-archiving/wayback` `c307bff44ae6` | 2026-10-27 | BSD-3-Clause | Wayback CDX search and memento retrieval, including prefix search, so archived post URLs of a handle can be listed, including posts since deleted if a capture exists. Handles rate limits and malformed CDX lines. | `src/wayback/_client.py` (constants, `search` signature and query build, pattern scan), `pyproject.toml` dependencies, test file list. | No keys. Two dependencies (`requests`, `urllib3`). Hard-coded `web.archive.org`. X coverage of our targets not tested. A plain stdlib call to the CDX URL may be enough, so try that first. | INTEGRATE (or a stdlib CDX call) |

Full pins, for the file reads above:
`pump-public-docs 639b87fb45c3adeffa6f7c4a1bf0cb85e392bf22`, `pumpswap-fee-decoder c8ef12aa172d9da1e9f6bdbebd17c4dc4c77eba2`, `solana-sandwich-avengers 43107597a96cbd637a870ec67b4d6f00e6af8261`, `opening-cross 72fee934dc7a3c01381cb6188746d9a6231e9731`, `solana-fund-tracer 39f1296d0d2ef9d0e7847839f53fa79d8bc9ddcf`, `crosschain-fund-flow a76e1f60a77c9ec60d265a95c1135e484150a168`, `spellbook 2257cb49f091615149f47e06c605e1c7808892a3`, `DefiLlama-Adapters 884590da4092ac341cc656fc467a7aeb29d6f0c4`, `Solana-Forensic-Analysis-Tool 51bae8c98bda7570b3f8fc3a26e88ca64a38ee10`, `liquidity-data 3d99b4634537ae8ba6e975d47bb9ffffff5bf90e`, `scraperx e8336a42de05d93dd1ead784a57a38cb01737e1b`, `wayback c307bff44ae6a753ebc2294f0eba6995f657a5a9`.

For candidate 8, `cex/index.js` is byte-identical at this pin and the MEXC list was rechecked there. Its other files were read minutes earlier at the branch head, which moves many times a day: re-read them when pinning.

## 1. Pump.fun fee sharing and creator fees

Source: `pump-public-docs` at `639b87f`. Discriminators recomputed as `sha256("global:<name>")[:8]` and `sha256("event:<Name>")[:8]`: 206 checked over the three IDLs, 0 mismatches. This checks the file, not mainnet.

File sha256 at `639b87f`:
- `idl/pump_fees.json`: `6b9fa3eccc6e06273076a47b581f9fcb9e531bb7c3c88acbcd44db55a4002b29`
- `idl/pump.json`: `7616681ea557975f9f623ac211080f22a93060781eaf4765b0a488d980997207`
- `idl/pump_amm.json`: `b7d8c57a4d9c4dd0109a9ab893052352333252d4eedced10ac091d4d66cab89b`

| Program | Instruction | Discriminator | Note |
|---|---|---|---|
| `pfeeUx...` | `create_fee_sharing_config` | `[195,78,86,76,111,52,251,213]` | 13 accounts, no args |
| `pfeeUx...` | `update_fee_shares` | `[189,13,136,99,187,164,237,35]` | hex `bd0d8863bba4ed23`, matches `ana_10_deployer.py` |
| `pfeeUx...` | `update_fee_shares_v2` | `[111,251,49,6,78,78,106,18]` | hex `6ffb31064e4e6a12`, matches `ana_10_deployer.py` |
| `pfeeUx...` | `revoke_fee_sharing_authority` | `[18,233,158,39,185,207,58,104]` | IDL lists no accounts and no args |
| `pfeeUx...` | `transfer_fee_sharing_authority` | `[202,10,75,200,164,34,210,96]` | IDL lists no accounts and no args |
| `pfeeUx...` | `admin_cto_sharing_config` | `[60,100,144,156,64,138,182,37]` | arg `new_admin` |
| `pfeeUx...` | `reset_fee_sharing_config` | `[10,2,182,95,16,127,129,186]` | Removed from the IDL at `e0687ae`, present at `3c6721a` |
| `pfeeUx...` | `reset_fee_sharing_config_v2` | `[169,245,17,209,94,91,248,128]` | Same |
| `6EF8rr...` (pump) | `distribute_creator_fees` | `[165,114,103,0,121,206,247,81]` | Not on the fee program |
| `6EF8rr...` (pump) | `distribute_creator_fees_v2` | `[255,203,19,79,244,68,8,159]` | arg `initialize_ata` |
| `6EF8rr...` (pump) | `collect_creator_fee` / `_v2` | `[20,22,86,123,198,28,219,132]` / `[207,17,138,242,4,34,19,56]` | |
| `6EF8rr...` (pump) | `migrate_bonding_curve_creator` | `[87,124,52,191,52,38,214,232]` | |
| `pAMMBa...` (PumpSwap) | `transfer_creator_fees_to_pump` | `[139,52,134,85,228,229,108,241]` | Not on the fee program |
| `pAMMBa...` (PumpSwap) | `transfer_creator_fees_to_pump_v2` | `[1,33,78,185,33,67,44,92]` | |
| `pAMMBa...` (PumpSwap) | `collect_coin_creator_fee` | `[160,57,89,42,181,139,43,66]` | |

| Program | Event | Discriminator | Fields |
|---|---|---|---|
| `pfeeUx...` | `CreateFeeSharingConfigEvent` | `[133,105,170,200,184,116,251,88]` | timestamp, mint, bonding_curve, pool, sharing_config, admin, initial_shareholders, status |
| `pfeeUx...` | `UpdateFeeSharesEvent` | `[21,186,196,184,91,228,225,203]` | timestamp, mint, sharing_config, admin, new_shareholders, version |
| `pfeeUx...` | `ResetFeeSharingConfigEvent` | `[203,204,151,226,120,55,214,243]` | timestamp, mint, sharing_config, old_admin, old_shareholders, new_admin, new_shareholders, old_version, new_version |
| `6EF8rr...` | `DistributeCreatorFeesEvent` | `[165,55,129,112,4,179,202,40]` | timestamp, mint, bonding_curve, sharing_config, admin, shareholders, distributed, quote_mint |
| `6EF8rr...` | `CollectCreatorFeeEvent` | `[122,2,127,1,14,191,12,175]` | timestamp, creator, creator_fee, quote_mint |
| `6EF8rr...` | `MigrateBondingCurveCreatorEvent` | `[155,167,104,220,213,108,243,3]` | Starts with timestamp, mint, bonding_curve, sharing_config, old_creator |
| `pAMMBa...` | `CollectCoinCreatorFeeEvent` | `[232,245,194,238,234,218,58,89]` | |
| `pAMMBa...` | `MigratePoolCoinCreatorEvent` | `[170,221,82,199,147,165,247,46]` | |

Points to use:
- Current shareholders can be read from the account instead of walking transactions. `SharingConfig` has discriminator `[216,74,9,0,56,140,93,75]`, PDA seeds `[b"sharing-config", mint]`, and fields bump, version, status, mint, admin, admin_revoked, shareholders. A `Shareholder` is `{address: pubkey, share_bps: u16}`.
- The docs describe `update_fee_shares_v2` as setting the final list and revoking further admin updates. The same document limits shareholders to at most 10, summing to 10,000 bps.
- Key decoders on program id plus discriminator. Anchor hashes only the name, so `pfeeUx...` and PumpSwap both have `WithdrawEvent` as `[22,9,133,26,160,44,71,192]`.
- IDL history of `idl/pump_fees.json`: `0c64400` (2025-08-28, 5 instructions), `f0ef005` (2026-01-09, fee sharing added), `1059c0d` (2026-03-05), `9d874ec` (2026-03-19), `3c6721a` (2026-05-18, v2 added), `e0687ae` (2026-09-12, reset removed), `8cda1fa` (2026-10-07), `639b87f` (2026-10-13, `withdraw` added).
- Already audited, cross-check only, Rust so not runnable here: `sevenlabs-hq/carbon` now has `decoders/pump-fees-decoder/`, and `0xfnzero/sol-parser-sdk` has `src/instr/pump_fees.rs`. `0xfnzero/solana-program-idls` at its head has `pump_fees.json` without the reset instructions.

I read no open-licensed Python or TypeScript decoder for these instructions. The official `@pump-fun/pump-sdk` is on npm, not read here, and `nirholas/pump-fun-sdk` is proprietary (see screened list). Writing the Python decoder from the IDL is the small path: the layouts are `Vec<Shareholder>` and fixed structs, and `ana_10_deployer.py` already does the first one.

## 2. Jito bundle identification

No repository offers a historical map or an on-chain way to do this. All clients I read call the same undocumented API. `D2` in the existing audit said no public membership source was shown in `jito-labs/searcher-examples`, and that stays true of that repo, but the explorer API is such a source, within its retention.

| Endpoint (base `https://bundles.jito.wtf/api/v1/bundles`) | Returns | Seen in |
|---|---|---|
| `/transaction/{signature}` | `[{"bundle_id": ...}]` | candidates 3, 4 and `weeaa/jito-go`, `svmScope`, `MemeTrans`, `rugsnipe` |
| `/bundle/{bundle_id}` | bundleId, slot, validator, tippers, landedTipLamports, landedCu, blockIndex, timestamp, txSignatures | candidate 4, `svmScope` docs, `weeaa/jito-go`, `rugsnipe` |
| `/slot/{slot}` | Every bundle of a slot, same fields. About 4 % of slots have none, per candidate 3 | candidate 3 |
| `/recent?limit=N&sort=Time&asc=false&timeframe=Week` | Recent bundles with `transactions` | candidate 3 |

Conflicts between sources, unresolved:
- Retention. `opening-cross` measured about seven days (2026-10-15) and treats anything older as unknown. `solana-sandwich-avengers` publishes verdicts for 45 epochs from `/slot/{n}` and `/transaction/{sig}`, has a bounded backfill mode, and its README says the ceiling is what "public RPC and Jito APIs still expose". The verdicts were committed on 2026-08-27. I could not tell how far back its calls reached or when they ran.
- 404 meaning. `solana-sandwich-avengers` says `200 []` is "no bundle" and 404 is "unknown signature". `opening-cross` and `svmScope` say 404 with `{"error":"Bundle not found"}` means not in a bundle.

Before relying on it: one GET on a known bundled transaction older than a few weeks, one on a recent one. Not done here, since this review only reads repositories. Until then, record failure, 404 or empty on any transaction older than a week as unknown. For live or new tokens, capture answers when first read, as `opening-cross` does.

Design points worth keeping from candidates 3 and 4: rate near 2 req/s with control on a rolling success rate, `/slot/{n}` costs one request for a whole creation slot instead of one per signature, and tip payer read from the transfer instead of `tippers`.

## 3. Wallet clustering and funding graphs

No repo is ready to adopt. The useful parts are methods.

`solana-fund-tracer`, rewrite instead of run, because of these weak spots:
- `deposit` returns `is_deposit` on any single transaction where the address lost SOL or tokens and a labelled wallet gained. A one-off send to a hot wallet counts. No false-positive control.
- `is_trade` reads instruction names from logs against a fixed list. Truncated logs or a venue with other names make a trade look like a transfer. Our decoder should replace this.
- A null `getTransaction` is skipped silently in `funder`, `biggest_out` and `deposit`.
- Its README claims real-case results (16 PumpSwap pools, about 12,000 SOL) that I did not verify.

`crosschain-fund-flow`, take the taxonomy only:
- Scores are hand-set and uncalibrated, the same objection as Splink in audit section C3.
- Service detection is a substring match on labels, including `bot`, `gate` and `gas`, so a label like "delegate" hits.
- `program_ids` is empty in `data/solana_platforms.json`, so platform matching rests on log keywords and labels.
- `SOLANA_PROGRAMS` holds a wrong Token-2022 id: `TokenzQdBNbLqP5VEhdkAS6EPFJJZq8L1YdPzjzJVd2`. `idl/pump.json` contains `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` and never the former.

A better deposit detector to read is `WHyadji/soltrace`, `internal/labels/detect.go` (see screened list): it needs both a minimum of distinct funders and an outgoing edge to a known exchange. Its plan file also records that traversal must stop at barriers, a bug it found in its own graph code.

## 4. Address labels

Exchange labels: usable, and the lists agree where they overlap.

| Comparison | Overlap | Real disagreements |
|---|---|---|
| Dune vs `soltrace` seed (17 rows) | 8 | 0 |
| Dune vs `gelato.sh` (12 rows) | 12 | 0 (one row is HTX against Huobi, the same exchange) |
| Dune vs MetaSleuth extract (16 rows) | 3 | 0 |
| Dune vs Flipside dump | 10 | 0 |
| `soltrace` vs Flipside dump | 3 | 0 |
| `soltrace` vs `gelato.sh` | 6 | 0 |

Names were compared on their first five letters. These lists can copy each other, so agreement does not prove independence.

Suggested source order, each row keeping its source:
1. Exchange-published: Bitstamp wallet transparency, Bybit proof-of-reserves CSV (candidate 8).
2. Curated lists: Dune (candidate 7), DefiLlama (candidate 8).
3. Indexer dump: Flipside CSV (candidate 9), lead only, confirmed by an observed sweep into a list 1 or 2 wallet before it appears in any finding.

Bridges: no sourced public list. `crosschain-fund-flow` has addresses "from prior sampling". `crosschain.py` already holds program ids.

KOL lists: no credible repo. The data is KolScan and GMGN scraped under restrictive licences (see `nirholas/kol-quest` below). KolScan pairs each wallet with a name and an X link, with no proof that the person controls the wallet. Using it as anything but a lead would turn a third party's claim into a finding.

## 5. Liquidity and LP tracking

No small read-only tool exists for "who added and removed liquidity on this token". PumpSwap events are in the IDL already pinned in section 1:

| Event | Discriminator |
|---|---|
| `CreatePoolEvent` | `[177,49,12,210,160,118,167,116]` |
| `DepositEvent` | `[120,248,61,83,31,142,107,144]` |
| `WithdrawEvent` | `[22,9,133,26,160,44,71,192]` |

Meteora events are in the IDLs of audit item B3, or at the sources listed in fiber-data's `idl/SOURCES.md` (`MeteoraAg/dlmm-sdk`, `MeteoraAg/zap-program`). The small path is to add these events to `decode.py` for the pools in question, using candidate 10 as the design reference for dual CPI and log decoding and for the failure table. Do not run its block-wide backfill. `decode.py` also needs the DAMM v2 program id, `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG`.

Other LP tools I saw in search results (`Rastacowboy0131/pumpliquid`, `ricky10p/lp-monitor`, `katarsis-dev/Liquidius`) look like position dashboards or screeners. I read only the Liquidius README, which is a DexScreener screener. The others were not read and are not assessed.

## 6. X archive and OSINT without an account

Two usable paths, none Solana-specific:
- Live timelines through FxTwitter v2 (candidate 11).
- Deleted or older posts through Wayback CDX (candidate 12).

Treat both as relay-reported. Keep the raw answer and hash it, as `col_10_x_posts.py` does for syndication.

Weak spots to handle if the FxTwitter pattern is added:
- `scraperx`'s own measurement: 4 of 10 requests answered, the failures being HTTP 404. So 404 cannot mean deleted.
- `_pages` returns what it has when a later page fails, with only a log warning. A partial timeline must be marked partial.
- `/2/search` returned 404 for every query per its notes (since 2026-10-09).
- Nitter instances churn. X Corp sent cease and desist letters on 2026-08-24 per the `zedeus/nitter` README, and that repo is archived.
- Reposts are mixed into timelines (9 of 19 in its measurement).
- None of this gives a wallet to X link.

## Screened and not retained

Same read-only method. Not counted as candidates.

| Repo | Last push | Licence | Read | Reason | Verdict |
|---|---|---|---|---|---|
| `nirholas/wallet-sleuth` | 2026-10-31 | "PROPRIETARY AND CONFIDENTIAL. SOURCE AVAILABLE, NOT OPEN SOURCE" | `LICENSE`, `README.md`, `packages/core/src/cluster.ts`, `labels/index.ts`, `signals/funding.ts` (first 90 lines) | 14 linkage signals and a `reachedGenesis` gate look well thought out, but the licence rules out use. | REJECT |
| `nirholas/kol-quest` | 2026-10-09 | "All rights reserved" | `LICENSE`, `README.md` parts, `fetchers/sources/kolscan.ts`, `scrape-kolscan.ts`, `output/kolscan-leaderboard.json` | 472 KolScan wallets with name and X link. Proprietary licence, unverified provenance. | REJECT |
| `nirholas/pump-fun-sdk` | 2026-11-03 | "All rights reserved" (GitHub shows `other`) | `LICENSE`, `DECODERS.md` (first 60 lines), `package.json` scripts, pattern scan of `pumpkit/packages/channel/src/claim-monitor.ts` | Has TypeScript claim decoders, and its own note says four copies have drifted. Licence rules out use. Its note warns that `claim_social_fee_pda` emits no CPI event, so a filter on one signal alone misses claims (not verified). | REJECT |
| `WHyadji/soltrace` | 2026-07-19 | None declared | `internal/labels/detect.go`, `internal/labels/seed/cex_labels.csv`, `cmd/soltrace/labels.go` (first 40 lines), a plan file, `README.md` | Only list with a per-row `src` column (17 rows, Solscan labels found by web search), and the fan-in deposit detector. Needs Postgres, Redis, ClickHouse. | READ ONLY FOR REFERENCE |
| `ImMike/crypto-wallet-address-labels` | 2026-03-08 | MIT | Solana dataset README, CSV, MetaSleuth and Vybe files | Re-host of candidate 9, same git blob `e3eeb5ff1b9b`. | REJECT |
| `ashpoolin/gelato.sh` | 2025-07-06 | MIT | `src/data/exchanges.js` | 12 addresses, all in Dune. | REJECT |
| `HailemariamMersha/MemeTrans` | 2026-03-19 | None declared | `data_pipeline/bundle/bundle_jito.py`, `bundle_fundflow.py`, `README.md`, a SQL template | Same Jito endpoint. `resp.json()[0]` raises on an empty list, which ends as "error" after retries, and 404 is stored as "None". Ships `.pkl` files, unsafe to load. One pointer: it queries `bigquery-public-data.crypto_solana_mainnet_us.Transactions`, a data source not tested here. | REJECT |
| `weeaa/jito-go` | 2025-07-30 | Apache-2.0 | `api/api.go` (first 140 lines) | Go client, same endpoints, `RetrieveRecentBundles` disabled in code. | REJECT |
| `alizeeshan1234/svmScope` | 2026-10-24 | MIT | `src/jito.rs` (first 120 lines), `docs/BUNDLE_PLAN.md` (first 50 lines) | Rust transaction replay. Documents the endpoints. No cargo here. | REJECT |
| `xin10ylop/rugsnipe` | 2026-10-28 | None declared | `analysis/scripts/gap2_firstslot/jito.py` | Short script, same endpoints, adds nothing. | REJECT |
| `no-limit-nodes/every-solana-program-decoded` | 2026-05-08 | MIT | `programs/pump_fees/README.md`, one event page | Marketing pages for a paid gRPC service, 17 pump_fees instructions against 31 now. | REJECT |
| `dnafund/Degen-Scanner` | 2026-03-13 | None declared | `README.md`, `.env.example` only | Telegram bot needing a bot token and Helius keys. The 171 KB `dev_tracer.py` was not read, so its code is not assessed. | REJECT |
| `vladkens/twscrape`, `d60/twikit` | 2026-10-31, 2026-03-10 | MIT | READMEs | Need X accounts or login. Fails the brief. | REJECT |
| `zedeus/nitter` | 2026-10-09 | AGPL-3.0 | `README.md` | Archived, needs sessions, cease and desist. | REJECT |
| `portalpayments/solana-wallet-names` | 2023-07-17 | MIT | `README.md`, file list | Name resolution. README says `@twitter` support was removed because few users mapped accounts to wallets. | REJECT |

## Capabilities with no credible repository

- Historical transaction to Jito bundle mapping beyond the explorer API. The only committed map covers sandwich legs.
- KOL or service labels with per-label sourcing.
- A sourced public list of Solana bridge addresses.
- A small, read-only LP history tool for one token on PumpSwap and Meteora.
- A wallet to X link from public data, in any repo I read.

## Not verified

- Nothing was run, so no decoder output, endpoint answer or test claim from these repos was checked. That includes retention and 404 behaviour of the Jito API, FxTwitter behaviour, and Wayback coverage of X for our targets.
- Discriminators were checked against the files, not against mainnet transactions, except that two match values already used in `ana_10_deployer.py`.
- Supply-chain review is partial: only the listed files were read, and full git histories and transitive dependencies were not. Absence of a bad pattern in those files is not a guarantee.
- Flipside labels were not re-queried. The Flipside connector returned HTTP 502 in this session and I did not retry it.
- My claim that the 100,000 row count is an export cap is an inference.

## Search queries used

GitHub search returns a capped result list (20 repos, 30 code hits per query here), so a repo missing from these lists may still exist. "0" marks an empty result.

Repository search (`gh search repos`):
- Fees: `solana fee sharing`
- Jito: `solana jito bundle explorer`, `solana jito history`, `solana bundle parser`, `solana jito indexer`, `solana jito dataset`, `solana bundle tracker`, `pumpfun bundle analysis`, `solana mev bundle analytics` (0)
- Clustering: `solana wallet clustering`, `solana funding graph`, `solana wallet graph`, `solana fund flow`, `solana forensics`, `solana sybil detection`, `solana transaction graph`, `pumpfun cluster wallets`, `solana common funder`, `solana entity resolution`
- Labels: `solana address labels`, `solana wallet labels`, `solana exchange addresses`, `solana cex wallets`, `solana labels dataset`, `solana hot wallets`, `solana kol wallets`, `solana kol list`, `pumpfun kol wallets`, `solana known addresses`, `solana address book`
- Liquidity: `pumpswap liquidity`, `pumpswap lp`, `pumpswap pool tracker`, `pumpswap indexer`, `meteora lp tracker`, `meteora position history` (0), `meteora dlmm analytics`, `meteora liquidity indexer`, `solana lp tracker`, `solana liquidity events`, `solana lp removal` (0)
- X: `solana twitter archive` (0), `solana twitter osint`, `solana twitter scraper`, `pumpfun twitter history` (0), `solana x osint`, `solana twitter wallet`, `pumpfun twitter scraper` (0), `solana username history` (0), `solana nitter` (0), `solana wayback`

Code search (`gh search code`, spaced by at least 6 s within a run):
- Fees: `pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`, `create_fee_sharing_config solana`, `update_fee_shares solana`, `transfer_creator_fees_to_pump`, `distribute_creator_fees`, `CreateFeeSharingConfigEvent`, `repo:duneanalytics/spellbook pump_fees` (0)
- Jito: `bundles.jito.wtf`, `explorer.jito.wtf solana`, `getInflightBundleStatuses solana bundle_id`, `bundles/transaction jito`, `get_bundles_by_slot jito` (0), `jito_bundle_id solana`, `getBundleStatuses solana bundle history retention`, `jito bundle_id parquet solana dataset`
- Labels: `5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9`, `H8sMJSCQxfKiFTCfDR3DUMLPwcRbM61LGFJ8N4dK3WjS Coinbase`, `AC5RDfQFmDS1deWZos921JfqscXdByf8BKHs5ACWjtW2 Bybit`, `solana exchange hot wallet label Kraken MEXC`, `G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`, `repo:duneanalytics/spellbook solana bridge addresses`, `repo:DefiLlama/DefiLlama-Adapters AC5RDfQFmDS1deWZos921JfqscXdByf8BKHs5ACWjtW2` (0), `repo:DefiLlama/DefiLlama-Adapters solana cexExports`, `kolscan.io solana wallet twitter`
- Liquidity: `repo:duneanalytics/spellbook pumpswap liquidity` (0)

Looked up by name, because a search scoped to Solana cannot find general tools: `zedeus/nitter`, `d60/twikit`, `vladkens/twscrape`, `JustAnotherArchivist/snscrape`, `edgi-govdata-archiving/wayback`, `akamhy/waybackpy`, `tomnomnom/waybackurls`, `nirholas/XActions`. Of these, only the Nitter, twikit and twscrape READMEs and the `wayback` code were read. The rest had metadata only and are not assessed.
