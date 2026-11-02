# External repositories audit (decoders, data tooling, cross-chain, bundles)

Audit date: 2026-11-02. Scope: 15 public repositories, judged from real source files, not READMEs.
Stack constraint: Python stdlib RPC client (Helius JSON-RPC, `getSignaturesForAddress` + `getTransaction` jsonParsed), no Rust toolchain (no `cargo`), node checked separately.
Rules followed: read only. No `npm install`, `pip install`, `cargo`, build, test or script from any audited repo was run, nothing was imported. Everything inside those repos was treated as untrusted data.
Local copies (shallow, `--depth 1`, blobs over 2 MB filtered): `/Volumes/PHI-Data/solana_forensics_v2/external_src/<name>`. Large repos and the 303 MB dataset were read through `gh api` only.
Also placed in `external_src/_crates_ref/`: the crates.io tarball `solana-keypair-3.1.2`, downloaded only to diff against a vendored copy (section B1).

## 1. Decision table

| # | Repo | Decision | One-line reason | Pin |
|---|------|----------|-----------------|-----|
| A1 | sevenlabs-hq/carbon | ADAPT (reference only) | Rust, no cargo here. Instruction-level Codama decoders, 1 test, 3 core fixtures. Use as an independent source of discriminators and account layouts, not as an engine. | `bebd1085f7cb7d0bc9d30c7367142ff620086681` (v2.0.0 is a release tag, HEAD is newer) |
| A2 | rpcpool/yellowstone-grpc | REJECT | Live streaming server/client. No historical `getTransaction` path. Geyser plugin and tools are AGPL-3.0. `proto` dir is Apache-2.0 if ever needed. | `43a827c31604e534d93f18c1883a1870c565f553` (only if the .proto is ever copied) |
| B1 | 0xfnzero/sol-parser-sdk | ADAPT (fixtures and cross-check only) | Rust, streaming-first (Yellowstone gRPC, ShredStream). Has an offline RPC parser but Rust only. Its 109 fixture files are the useful part. | `fade467b534289639502b4ddc36551b217152fa5` |
| B2 | cxcx-ai/solana-dex-parser | ADAPT (candidate second decoder, isolated) | Only repo with an offline entry point taking a `getTransaction` object (`DexParser.parseAll`). Stale (2025-10-02): no pump `buy_v2/v3`. Needs node + npm install in a quarantined dir. | `0c67d8ffa78c7fb2e80230ec53d0627c9531566a` + `package-lock.json` sha256 |
| B3 | 0xfnzero/solana-program-idls | INTEGRATE as pinned data, with a pump caveat | Plain JSON IDLs, no code. Shipped `pump.json` and `pump_amm.json` lag upstream (missing `buy_v3`, `sell_v3`, `multi_hop_*`). Re-source pump files from `pump-fun/pump-public-docs`. | `d5205f8bc42d443bfe5e85c6f2bba80b2e4365d0` + per-file sha256 (section B3) |
| B4 | solsonar/solana-multi-dex-decoder | REJECT | Outer-instruction swaps and pool accounts only, no inner instructions, no Jupiter, no balance reconciliation. One commit, 0 stars. Its constants match IDLs, so keep only as a cross-check. | `8ae4c238c23fd337e08dc4c1377b839a4675bba3` |
| B5 | solana-program/token-2022 | INTEGRATE as specification | Apache-2.0 ground truth for fee, interest and scaled-amount rules. Re-implement the arithmetic in Python, do not run it. | `5251dcc07ecbcb721d6c4f0231090defadf00311` |
| C1 | duckdb/duckdb | INTEGRATE (analysis engine) | MIT, current release v2.0.0. Query parquet/JSONL of decoded transfers. | release `v2.0.0`, HEAD `a76f27551c0903647d9484fcbf07086683aeeb92` |
| C2 | pola-rs/polars | REJECT (redundant) | MIT, but duckdb covers the need. Extra dependency for no gain. | none |
| C3 | moj-analytical-services/splink | REJECT for wallet-linkage probabilities | Calibration needs a prior and conditional independence that wallet features do not meet. See section C3. | none (if explored: `v5.0.0`, `41ef8b1db1311e3d95151524a7c392ed2141a362`) |
| C4 | networkx/networkx | ADAPT (graph primitives, exploratory) | BSD-3-Clause (GitHub shows NOASSERTION because the file is `LICENSE.txt`). Connected components, no calibration claims. | tag `networkx-3.7`, HEAD `a325f6a948c0c2959fb48db205fa36534ea9429d` |
| C5 | jayrabol/solana-holder-clusters | ADAPT (method notes only), REJECT as data | A TypeScript tool, not a dataset. First-funder heuristic with documented blind spots. 5 hand-picked labels. | `a75a72965479a7b715b041148803d8004fe25079` |
| C6 | ian05012/solana-memecoin-dataset | REJECT as control population | Convenience sample from GMGN, survivorship bias, 20 days, labels are forward returns, not our labels. Parquet contents not opened. | `7070d00e1e4492f8604d988549d91785cc5f43f7` |
| D1 | wormhole-foundation/wormhole-sdk-ts | ADAPT (VAA layout and Solana message attribution) | Apache-2.0. Clear VAA layout. The SDK does not verify guardian signatures itself. | `2a8ea439ef7c928aa0d0d139ec008c1a11909b2a` |
| D2 | jito-labs/searcher-examples | REJECT as a membership source | Submission code. Bundle results are returned only to the submitter. No public, verifiable membership source is shown. | `efa92a9f90f3954532057324b6f81c6120466fb8` |

Supply-chain summary: no malicious pattern found in any cloned repo. Three hazards worth noting (not malware): `solana-memecoin-dataset/scripts/gmgn_client.py:62` builds a `shell=True` command from API-returned strings (optional path); `sol-parser-sdk/patches/solana-keypair` is a vendored crate whose only diff to crates.io 3.1.2 is an error-wrapping change and which is not wired into the build; `solana-multi-dex-decoder` is oriented to backrunning (its CHANGELOG mentions "victim" transactions and "backrun arb executors"), which is a purpose mismatch, not a risk.

## 2. Method and what "verified" means here

- "Verified in source": I opened the file at the pinned commit and read the value on the cited line. No value comes from memory.
- Line numbers refer to the file as checked out at the pinned SHA. For `gh api` reads the SHA is the one listed in the table.
- Anchor discriminators were also recomputed as `sha256("global:<snake_name>")[:8]` (instructions) and `sha256("event:<Name>")[:8]` (events) and compared with the value written in the source. "sha256 MATCH" below means this recomputation agrees. It is a consistency check on the file, not a check against mainnet.
- The IDL scan helper was a throwaway script in the session scratchpad that only reads JSON as data. Nothing from the audited repos was executed.

## 3. Program ids and discriminators (the table that matters most)

Legend: IDL = `solana-program-idls` (B3, pinned `d5205f8`). CARBON = carbon at `bebd108`, `decoders/<x>-decoder/src/...`. SOLSONAR = B4 `src/constants.js`. DEXP = B2 `src/constants/`. SPS = B1. "sha" = recomputed Anchor hash agrees.

### 3.1 Program ids

| Program | Program id | Source (file:line) |
|---------|-----------|--------------------|
| pump.fun | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | IDL `pump.json:2`; CARBON `pumpfun-decoder/src/lib.rs:5`; DEXP `programId.ts:254`; SPS `src/instr/program_ids.rs:11` |
| PumpSwap | `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | IDL `pump_amm.json:2`; CARBON `pump-swap-decoder/src/lib.rs:5`; SOLSONAR `constants.js:7` |
| Raydium AMM v4 | `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8` | IDL `raydium_amm.json:2399`; CARBON `raydium-amm-v4-decoder/src/lib.rs:5`; SOLSONAR `constants.js:8`; DEXP `programId.ts:83` |
| Raydium CPMM | `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C` | IDL `raydium_cpmm.json:2`; CARBON `raydium-cpmm-decoder/src/lib.rs:5`; DEXP `programId.ts:93` |
| Raydium CLMM | `CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK` | IDL `raydium_clmm.json:2`; CARBON `raydium-clmm-decoder/src/lib.rs:5` |
| Raydium Launchpad | `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj` | IDL `raydium_launchpad.json:2` |
| Meteora DLMM | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` | IDL `meteora_dlmm.json:2`; CARBON `meteora-dlmm-decoder/src/lib.rs:5` |
| Meteora DAMM v2 | `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG` | IDL `meteora_damm_v2.json:2`; CARBON `meteora-damm-v2-decoder/src/lib.rs:5` |
| Meteora DAMM v1 (dynamic amm) | `Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB` | IDL `meteora_amm.json:2`; DEXP `programId.ts:138` |
| Orca Whirlpool | `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` | IDL `orca_whirlpool.json:2`; CARBON `orca-whirlpool-decoder/src/lib.rs:5` |
| Jupiter v6 | `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4` | CARBON `jupiter-swap-decoder/src/lib.rs:5`; DEXP `programId.ts:6` (not in IDL repo) |

### 3.2 Instruction and event discriminators

| Program | Item | Bytes | Source (file:line) | Check |
|---------|------|-------|--------------------|-------|
| pump.fun | `create` | `[24,30,200,40,5,28,7,119]` | IDL `pump.json:4104`; CARBON `pumpfun-decoder/.../instructions/create.rs:42`; DEXP `discriminators.ts` PUMPFUN.CREATE | sha |
| pump.fun | `buy` | `[102,6,61,18,1,218,235,234]` | IDL `pump.json:1026`; CARBON `.../buy.rs:43` | sha |
| pump.fun | `sell` | `[51,230,133,164,1,127,131,173]` | IDL `pump.json:7197`; CARBON `.../sell.rs:41` | sha |
| pump.fun | `TradeEvent` | `[189,219,127,211,78,230,97,238]` | IDL `pump.json:10292`; CARBON `pumpfun-decoder/src/events/trade_event.rs:47` | sha |
| pump.fun | `CreateEvent` | `[27,114,169,77,222,235,99,118]` | IDL `pump.json:10110` | sha |
| pump.fun | `CompleteEvent` | `[95,114,97,156,212,46,152,8]` | IDL `pump.json:10084` | sha |
| pump.fun | `migrate` | `[155,234,231,146,236,158,162,30]` | IDL `pump.json:5894` | sha |
| pump.fun | `buy_v2` / `sell_v2` / `buy_exact_sol_in` / `create_v2` | `[184,23,238,97,103,197,211,61]` / `[93,246,130,60,231,233,64,178]` / `[56,252,116,8,158,223,205,95]` / `[214,144,76,236,95,139,49,180]` | IDL `pump.json:2534 / 7487 / 2138 / 4432` | sha |
| pump.fun, NEWER than shipped IDL | `buy_v3` / `sell_v3` / `buy_exact_quote_in_v3` / `multi_hop_curve_swap` | `[7,5,29,196,245,23,101,80]` / `[28,146,222,119,38,196,105,213]` / `[225,247,80,30,213,179,132,136]` / `[225,154,117,22,215,86,246,103]` | upstream `pump-fun/pump-public-docs` `idl/pump.json:3710 / 9330 / 2154 / 7878` at `639b87fb45c3adeffa6f7c4a1bf0cb85e392bf22` (read via `gh api`, not in B3) | sha |
| PumpSwap | `buy` | `[102,6,61,18,1,218,235,234]` | IDL `pump_amm.json:577`; CARBON `pump-swap-decoder/.../buy.rs:52`; SOLSONAR `constants.js` DISC_PUMP_AMM_BUY `66063d1201daebea` | sha |
| PumpSwap | `sell` | `[51,230,133,164,1,127,131,173]` | IDL `pump_amm.json:3310`; CARBON `.../sell.rs:43`; SOLSONAR DISC_PUMP_AMM_SELL `33e685a4017f83ad` | sha |
| PumpSwap | `BuyEvent` / `SellEvent` | `[103,244,82,31,44,245,119,119]` / `[62,47,55,10,165,3,220,42]` | IDL `pump_amm.json:5323 / 5505`; CARBON `events/buy_event.rs:47`, `events/sell_event.rs:40` | sha |
| PumpSwap, NEWER than shipped IDL | `buy_v2` / `sell_v2` / `multi_hop_swap` | `[184,23,238,97,103,197,211,61]` / `[93,246,130,60,231,233,64,178]` / `[43,100,73,19,233,246,111,148]` | upstream `pump-public-docs` `idl/pump_amm.json:1683 / 4411 / 3818` at `639b87f` | sha |
| Raydium AMM v4 | `swapBaseIn` | single byte `9` | IDL `raydium_amm.json:933` (array index 9, file declares `instruction_selector_type: "index"` at `:2398`); CARBON `raydium-amm-v4-decoder/.../swap_base_in.rs:41` `[9]`; SOLSONAR `constants.js` `=9` | index recomputed from the file |
| Raydium AMM v4 | `swapBaseOut` | `11` | IDL `raydium_amm.json:1119` (index 11); SOLSONAR `constants.js` | index recomputed |
| Raydium AMM v4 | `swapBaseInV2` / `swapBaseOutV2` | `16` / `17` | IDL `raydium_amm.json:1443 / 1498` (indices 16, 17); SOLSONAR `constants.js` | index recomputed |
| Raydium CPMM | `swap_base_input` | `[143,190,90,218,196,30,51,222]` | IDL `raydium_cpmm.json:1786`; CARBON `raydium-cpmm-decoder/.../swap_base_input.rs:42` | sha |
| Raydium CPMM | `swap_base_output` | `[55,217,98,86,163,74,180,173]` | IDL `raydium_cpmm.json:1939` | sha |
| Raydium CPMM / CLMM | `SwapEvent` | `[64,198,205,232,38,8,113,226]` | IDL `raydium_cpmm.json:2423`, `raydium_clmm.json:4396` | sha |
| Raydium CLMM | `swap` / `swap_v2` | `[248,198,158,145,225,117,135,200]` / `[43,4,237,11,26,201,30,98]` | IDL `raydium_clmm.json:3430 / 3619`; CARBON `raydium-clmm-decoder/.../swap.rs:44`, `swap_v2.rs:46` | sha |
| Raydium Launchpad | `buy_exact_in` / `TradeEvent` | `[250,234,13,123,213,156,19,236]` / `[189,219,127,211,78,230,97,238]` | IDL `raydium_launchpad.json:11 / 4590` | sha |
| Meteora DLMM | `swap` | `[248,198,158,145,225,117,135,200]` | IDL `meteora_dlmm.json:3999`; CARBON `meteora-dlmm-decoder/.../swap.rs:37` | sha |
| Meteora DLMM | `swap2` | `[65,75,63,76,235,91,91,136]` | IDL `meteora_dlmm.json:4090`; CARBON `.../swap2.rs:42` | sha |
| Meteora DLMM | `swap_exact_out` / `swap_exact_out2` / `swap_with_price_impact` / `swap_with_price_impact2` | `[250,73,101,33,38,207,75,184]` / `[43,215,247,132,137,60,243,81]` / `[56,173,230,208,173,228,156,205]` / `[74,98,192,214,177,51,75,51]` | IDL `meteora_dlmm.json:4191 / 4282 / 4383 / 4480` | sha |
| Meteora DLMM | event `Swap` | `[81,108,227,190,205,208,10,196]` | IDL `meteora_dlmm.json:5193` | sha |
| Meteora DAMM v2 | `swap` / `swap2` | `[248,198,158,145,225,117,135,200]` / `[65,75,63,76,235,91,91,136]` | IDL `meteora_damm_v2.json:2783 / 2898`; CARBON `meteora-damm-v2-decoder/.../swap.rs:38`, `swap2.rs:38` | sha |
| Meteora DAMM v2 | event `EvtSwap2` | `[189,66,51,168,38,80,117,153]` | IDL `meteora_damm_v2.json:3711`; CARBON `.../events/evt_swap2.rs` | sha |
| Meteora DAMM v1 | `swap` | `[248,198,158,145,225,117,135,200]` | IDL `meteora_amm.json:632` | sha |
| Orca Whirlpool | `swap` / `swap_v2` | `[248,198,158,145,225,117,135,200]` / `[43,4,237,11,26,201,30,98]` | IDL `orca_whirlpool.json:4969 / 5091`; CARBON `orca-whirlpool-decoder/.../swap.rs:69`, `swap_v2.rs:78` | sha |
| Orca Whirlpool | `two_hop_swap` / `two_hop_swap_v2` | `[195,96,237,108,68,162,219,230]` / `[186,143,209,29,254,2,194,117]` | IDL `orca_whirlpool.json:5313 / 5501` | sha |
| Orca Whirlpool | event `Traded` | `[225,202,73,175,147,43,160,150]` | IDL `orca_whirlpool.json:5977`; CARBON `.../events/traded.rs:25` | sha |
| Jupiter v6 | `route` | `[229,23,203,151,122,227,173,42]` | CARBON `jupiter-swap-decoder/src/instructions/route.rs:37` | sha |
| Jupiter v6 | `shared_accounts_route` | `[193,32,155,51,65,214,156,129]` | CARBON `.../shared_accounts_route.rs:42` | sha |
| Jupiter v6 | `route_v2` | `[187,100,250,204,49,196,175,20]` | CARBON `.../route_v2.rs:39` | sha |
| Jupiter v6 | event wrapper + `SwapEvent` | `[228,69,165,46,81,203,154,29]` then `[64,198,205,232,38,8,113,226]` | DEXP `discriminators.ts` JUPITER.ROUTE_EVENT (16 bytes) | the 8-byte tail equals the Raydium `SwapEvent` hash; the 8-byte prefix is the Anchor self-CPI event tag, not recomputed here |

Cross-source agreement: for every pump.fun, PumpSwap, Raydium CPMM/CLMM, Meteora DLMM, Orca `swap`/`swap_v2` item, the IDL (B3), CARBON, SOLSONAR (where present) and DEXP (where present) give identical bytes. Four independent files agreeing plus the SHA-256 recomputation is the strongest verification available without mainnet.

Not found in source (do not fill from memory):
- Raydium CLMM `SwapEvent` as emitted by the live program: present in the IDL, but whether mainnet CLMM emits it through a CPI event or a log was not checked.
- Raydium AMM v4 swap "event": the program is not Anchor and writes a `ray_log:` base64 log. Parser: `solana-dex-parser/src/parsers/raydium/parser-raydium-logs.ts:86-91` (base64 decode). The log layout was not independently verified against `raydium-io/raydium-amm`.
- Jupiter `exact_out_route`, `route_with_token_ledger`, `shared_accounts_route_v2`, `exact_out_route_v2` exist as files in carbon (`decoders/jupiter-swap-decoder/src/instructions/`) but their bytes were not extracted here.
- Jupiter route instruction bytes are NOT in any of: solana-program-idls, solana-multi-dex-decoder (it states it does not parse Jupiter), sol-parser-sdk (`jupiter` appears only in `src/core/account_dispatcher.rs`), solana-dex-parser (only event discriminators). The only source is carbon.
- Meteora DAMM v1 swap event discriminator, Raydium CLMM-legacy and Orca-legacy IDLs: those legacy IDLs are old Anchor format with no `discriminator` field (`orca_whirlpool_legacy.json:746`, `raydium_clmm_legacy.json:830`) and no `address`. Discriminators would have to be computed, which was not done for them.

## 4. Per-repo sections

### A1. sevenlabs-hq/carbon

1. Exists: yes. Default branch `main`. HEAD `bebd1085f7cb7d0bc9d30c7367142ff620086681` (2026-11-02T03:23:34Z). Last push 2026-11-02. Latest release `v2.0.0` (2026-09-05). 638 stars.
2. License: root `LICENSE` is MIT, "Copyright (c) 2024 SevenLabs IT Consulting - FZCO" (read via `gh api`, line 1-3). Only one LICENSE file in the tree (`carbon_tree.tsv` search for "LICENSE" returns the root file only), so there is no per-directory variation.
3. Dependencies: Rust workspace (`Cargo.toml`: members `crates/*`, `datasources/*`, `decoders/*`, `examples/*`, `metrics/*`; some datasources excluded for Solana v3 stacks). Also `package.json` and `pnpm-workspace.yaml` for the code generator in `packages/`. Needs a Rust toolchain, which this Mac lacks.
4. Tests and fixtures: `crates/core/tests/fixtures/{simple_tx,cpi_tx,nested_cpi_tx}.json` and `crates/core/tests/README.md` (three Solscan links); `decoders/token-2022-decoder/tests/extension_nullability.rs`; `packages/cli/tests`, `packages/renderer/tests`. Decoders themselves are auto-generated (header "AUTOGENERATED using the Codama library") and have essentially no tests. 11,521 files in the tree, mostly generated decoders.
5. Capabilities: 60+ program decoders under `decoders/` (pumpfun, pump-swap, raydium-amm-v4/cpmm/clmm/launchpad, meteora-dlmm/damm-v2/dbc/pools, orca-whirlpool, jupiter-swap/dca/limit-order, system-program, token-program, token-2022, associated-token-account). Datasources: Yellowstone, RPC block/transaction crawler, Helius, Jito shredstream. Core: `crates/core/src/transaction.rs`, `instruction.rs` (nested instruction handling), `transformers.rs`.
6. Versus our need: decodes instructions and events by program, not full-transaction accounting (no WSOL wrap/close reconciliation, no rent-refund attribution, no net-balance view). Useful as an independent reference for discriminators and account ordering (see section 3).
7. Decision: ADAPT, reference only. Reason: cannot be built here, decoder crates are generated, the only executable value is the constants, which we already take from IDLs.
8. Pin: commit SHA above; if used, record the sha256 of each referenced `decoders/<x>/src/instructions/<y>.rs`.

Supply chain: not a small repo; no per-file scan of 11k files. Checked: root manifests and the files cited above only. Status: no finding, coverage partial (see Not verified).

### A2. rpcpool/yellowstone-grpc

1. Exists: yes. Default branch `master`. HEAD `43a827c31604e534d93f18c1883a1870c565f553` (2026-10-31T19:08:21Z). Last push 2026-11-02. Latest release `v16.2.0+solana.4.3.2` (2026-10-30). 1,020 stars. The tree has 199 files.
2. License, read from files:
   - `LICENSING.md` (371 bytes): "The default license for this project is AGPL-3.0-only (LICENSE)." It then lists, as Apache-2.0: `examples`, `yellowstone-grpc-client`, `yellowstone-grpc-client-nodejs`, `yellowstone-grpc-proto` "and their subdirectories".
   - Root `LICENSE` is the GNU AGPL v3 text. Root `Cargo.toml:19` says `license = "AGPL-3.0"`.
   - Apache directories each carry `LICENSE_APACHE2`: `examples/LICENSE_APACHE2`, `yellowstone-grpc-client/LICENSE_APACHE2`, `yellowstone-grpc-client-nodejs/LICENSE_APACHE2`, `yellowstone-grpc-proto/LICENSE_APACHE2`. Crate manifests agree: `yellowstone-grpc-client/Cargo.toml:9` and `yellowstone-grpc-proto/Cargo.toml:9` say Apache-2.0, `yellowstone-grpc-client-nodejs/package.json:4` says Apache-2.0.
   - AGPL by default (everything not listed): `yellowstone-grpc-geyser` (the validator plugin), `yellowstone-grpc-tools`, `yellowstone-grpc-e2e-test`, `yellowstone-grpc-e2e-macros`, `ci`, and the root files. Their manifests use `license = { workspace = true }` (AGPL).
   - What it means for us (engineering reading, not legal advice): a project that only speaks the gRPC protocol to a Yellowstone server copies no code, so no license attaches to the connection itself; the server operator is the one who runs the AGPL plugin. Copying code from the Apache directories (`proto/geyser.proto`, the client crate) is permitted with notice. Copying anything from `yellowstone-grpc-geyser` or `yellowstone-grpc-tools` into a public repo would bring AGPL obligations on that code and on a modified network service built from it. Rule: copy only from the four Apache directories.
3. Dependencies: Rust workspace, tonic, prost, solana crates. Not needed for us.
4. Tests: `yellowstone-grpc-e2e-test/` (22 files) is an end-to-end harness against a running node. No offline transaction fixtures.
5. Capabilities: `yellowstone-grpc-proto/proto/geyser.proto` defines `service Geyser` with `Subscribe`, `SubscribeReplayInfo`, `GetSlot`, `GetBlockHeight`, `GetLatestBlockhash`, `IsBlockhashValid`, `GetVersion` (lines 10-20). `from_slot` replay exists (`geyser.proto:50`) but is a short-horizon replay of a live node, not an archive.
6. Versus our need: our pipeline is `getSignaturesForAddress` + `getTransaction` on historical data. Yellowstone gives a live feed from a node we do not operate.
7. Decision: REJECT.
8. Pin: nothing. If `geyser.proto` is ever needed, pin `43a827c` and copy only `yellowstone-grpc-proto/proto/*.proto` with the Apache notice.

### B1. 0xfnzero/sol-parser-sdk

1. Exists: yes. Default `main`. HEAD `fade467b534289639502b4ddc36551b217152fa5` (2026-11-01). Last push 2026-10-31. 43 stars. Crate version 0.10.0 (`Cargo.toml:3`).
2. License: `LICENSE` is MIT, "Copyright (c) 2024 MiracleAI-Labs" (note: not the repo owner's name). `Cargo.toml:9` `license = "MIT"`. The vendored `patches/solana-keypair/Cargo.toml` is Apache-2.0 (Anza), consistent with upstream.
3. Dependencies (`Cargo.toml`): solana-sdk 4.0.1, solana-client 4.2.2, solana-transaction-status 4.2.2, yellowstone-grpc-client 13.5.0, yellowstone-grpc-proto 12.7.0, tonic, tokio, borsh, spl-token, spl-token-2022, rayon, libc. `rust-version = "1.91"`. `Cargo.lock`: 724 packages, all `registry+https://github.com/rust-lang/crates.io-index`, zero git sources.
4. Tests and fixtures: 168 files under `tests/`, 109 under `tests/fixtures` (17 MB). Includes raw `getTransaction`-shaped JSON with `transaction` as a base64 pair: `pumpfun_rpc_transaction.json`, `pumpswap_rpc_transaction.json`, `raydium_cpmm_rpc_transaction.json`, `meteora_dlmm_orca_rpc_transaction.json`, `pumpfun_migrate_v2_rpc_transaction.json`, `stonkfun_*_rpc_transaction.json`, `rpc_corpus/` (27 files). Some fixtures are explicitly synthetic: `dbc_swap2.json` begins `"source": ... "synthetic fixtures, not mainnet transactions"`. Which of the other files are real mainnet transactions was not verified.
5. Capabilities: it is both. Streaming: `src/grpc/` (Yellowstone), `src/shredstream/`. Parsing: `src/rpc_parser.rs` says "independent RPC transaction parser ... does not depend on gRPC streaming ... usable for offline analysis" (lines 1-4). Entry points `parse_rpc_transaction` (`:92`), `parse_rpc_transaction_with_cost` (`:115`) take an `EncodedConfirmedTransactionWithStatusMeta` (JSON-deserializable, no network), and `parse_transaction_from_rpc` (`:49`) fetches over RPC. Language: Rust only.
6. Versus our need: output is `DexEvent` for DEX programs (pump.fun, PumpSwap, Raydium, Meteora, Orca, LaunchLab). It is not a general transfer/ATA/rent decoder. Cannot run here (no cargo).
7. Decision: ADAPT. Use the fixtures as extra test transactions for our own decoder (after verifying each against RPC), and use `src/instr/program_ids.rs` and `src/logs/*.rs` as cross-check. Do not depend on it.
8. Pin: SHA above, plus sha256 of each fixture file actually copied.

Supply-chain review (what I checked, `git grep` over `src`, `examples`, `benches`, `tests` except fixtures):
- `build.rs`, `.cargo/`, shell scripts, `.github`: none in the tree (checked with `git ls-files`).
- Process, network, env, fs: no `Command::new`, `std::process`, `reqwest`, `hyper`, `TcpStream`, `include_bytes` in `src`. Only `libc::clock_gettime` (`src/core/clock.rs:241-252`). Network code is the documented Yellowstone/ShredStream client (`src/grpc/geyser_connect.rs:41`). Examples read `SOLANA_RPC_URL`, `TX_SIGNATURE`, `ACCOUNTS`, `MINT` env vars and accept endpoints from the user.
- Blobs: `src/logs/optimized_matcher.rs:2223,2255` hold base64 `Program data:` log lines inside the test module (the leading bytes decode to the pump TradeEvent hash `bddb7fd34ee661ee`). No other 200+ character strings outside fixtures.
- Hidden Unicode (bidi, zero-width): none in non-doc, non-JSON files.
- `scripts/capture_stonkfun.py:29` and `scripts/discover_stock_pools.py:52` call `RPC_URL` / `https://solana-rpc.publicnode.com` via `urllib`; they read no wallet files.
- `patches/solana-keypair/`: a vendored copy of the keypair crate (a crate that handles secret keys, so I diffed it). Downloaded `solana-keypair-3.1.2.crate` from `static.crates.io` and compared: `Cargo.toml`, `src/seed_derivable.rs`, `src/signable.rs` identical; `src/lib.rs` differs only at line 53 (decode error wrapped in `std::io::Error` with a Chinese comment). The root `Cargo.toml` has no `[patch]` section and `git grep` finds no reference to `patches`, so it is not built. Finding: benign diff, dead directory.
- Result: no finding. Residual risk: 118 Rust source files in `src` were pattern-scanned, not fully read.

### B2. cxcx-ai/solana-dex-parser

1. Exists: yes. Default `main`. HEAD `0c67d8ffa78c7fb2e80230ec53d0627c9531566a` (2025-10-02T23:38:53+08:00). Last push 2025-10-02 (13 months stale at audit date). Single commit in the shallow history (shallow clone, so the real count is unknown). Commit author `Caspod`. 114 stars. Package version 2.6.7.
2. License: `LICENSE` is MIT, "Copyright (c) 2025 Caspod". `package.json` says MIT. Note the owner name `cxcx-ai` differs from the copyright holder; not a licensing problem, but record it.
3. Dependencies (`package.json`): `@solana/web3.js ^1.87.0`, `borsh 0.7.0`, `dotenv ^16.4.7`; dev: jest, ts-jest, typescript, eslint, prettier. `package-lock.json` and `yarn.lock` present; all `resolved` URLs in `package-lock.json` point at `registry.npmjs.org` (checked: no non-npm hosts). No `postinstall`/`preinstall`; scripts are `build: tsc`, `pretest: npm run build`, `prepublishOnly`, `test: jest`, `lint`, `format` (`package.json`).
4. Tests and fixtures: 26 files in `src/__tests__/`. Most tests call `connection.getTransaction(...)` and need `SOLANA_RPC_URL` (e.g. `parser-pumpfun.test.ts:12-20`), so they are not offline. Four `*.test.case.ts` files (`parser.test.case.ts` 27 KB, `grpc-tx.test.case.ts` 44 KB, `grpc-block.test.case.ts` 38 KB, `shred-tx.test.case.ts` 23 KB) hold embedded transactions and expected outputs usable offline.
5. Capabilities and the offline entry point:
   - Entry point: `new DexParser().parseAll(tx, config?)` at `src/dex-parser.ts:357`; also `parseTrades` (`:336`), `parseLiquidity` (`:343`), `parseTransfers` (`:350`). Exported via `index.ts` (`export * from './src/dex-parser'`).
   - Input type `SolanaTransaction` (`src/types/trade.ts:7-10`) is `ParsedTransactionWithMeta | VersionedTransactionResponse | ...`, so a jsonParsed `getTransaction` result is the native input. `TransactionAdapter` (`src/transaction-adapter.ts:10-20`) reads `tx.transaction.message`, `meta`, handles `'parsed' in instruction` (`:154,228,237`). `grpc-tx.test.ts` runs it on a stored object with no network.
   - No network code in `src`: `git grep -nE "Connection|fetch|http"` over `src` excluding `__tests__` returns nothing. The only runtime use of web3.js is type checks (`instanceof MessageV0` at `transaction-adapter.ts:~28`), so `@solana/web3.js` must still be installed.
   - Covers: Jupiter (route events, DCA, limit order, VA), pump.fun, PumpSwap, Raydium v4/CPMM/CL/Launchpad, Orca, Meteora DLMM/DAMM/DBC, Moonit, Boop, Heaven. Also `parseTransfers` and `transfer-utils.ts`, `transfer-compiled-utils.ts`, `transaction-utils.ts` (token/WSOL handling).
   - Gap: `src/constants/discriminators.ts` PUMPFUN lists only `CREATE/MIGRATE/BUY/SELL` and events; it has no `buy_v2`, `buy_v3`, `sell_v3`, `multi_hop_*` (compare section 3.2). Expect missed or mis-attributed trades on recent pump.fun transactions. A decoder disagreement there is informative, not a bug in our engine.
6. Would running it offline as our second decoder be sensible? Yes, as a quarantined, optional second opinion, because it is independent code with a different design (balance-change driven) and our rule is to keep disagreements. Conditions: (a) install in a dedicated directory outside the repo, `npm ci --ignore-scripts` against the shipped `package-lock.json`, with network allowed only for that install; (b) build with `tsc` once, then run a small driver written by us that reads JSON from disk and calls `parseAll`, with the process run without network; (c) pin the lock hash; (d) feed it jsonParsed transactions, record its `ParseResult` (fields `trades`, `liquidities`, `transfers`, `memeEvents`, `fee`, `txStatus`) next to ours and never reconcile automatically.
   What must be installed: node (checked elsewhere), `@solana/web3.js@^1.87`, `borsh@0.7.0`, `dotenv`, `typescript` (dev, for `tsc`). jest/eslint are not needed. Not tested here because installing is out of scope for this audit.
7. Decision: ADAPT (optional second decoder, quarantined).
8. Pin: commit SHA, sha256 of `package-lock.json`, node version used, and the output of `npm ls --all` after install.

Supply-chain review: `git grep` for `eval(`, `new Function`, `child_process`, `execSync`, `spawn(`, `atob(`, `fromCharCode`, `process.env`, `dotenv`, `readFileSync`, `os.homedir`, `keypair`, `secretKey`, `privateKey`, `.ssh`, `fetch(`, `axios`, `XMLHttpRequest`, `http(s)://` across `src`, `index.ts`, configs.
- `process.env` and `dotenv` appear only in `src/__tests__/*.test.ts` (reading `SOLANA_RPC_URL`; e.g. `parser-pumpfun.test.ts:6,12`), never in non-test code.
- `base64` appears at `src/parsers/raydium/parser-raydium-logs.ts:86-91` to decode the `ray_log:` payload.
- No long encoded blobs (200+ chars) in non-fixture code; no hidden Unicode; `jest.config.js`, `.eslintrc.js`, `.vscode/launch.json` read in full and contain only config.
- Result: no finding. Residual: node_modules would be fetched by npm; the dependency tree (web3.js transitive) is not audited here.

### B3. 0xfnzero/solana-program-idls

1. Exists: yes. Default `main`. HEAD `d5205f8bc42d443bfe5e85c6f2bba80b2e4365d0` (2026-10-22). Last push 2026-10-22. 34 stars. Catalog snapshot string `v2026.09.13` (`README.md:29`).
2. License: `LICENSE` MIT, "Copyright (c) 2025 0xfnzero". Individual IDLs carry the licenses of their upstream authors (not restated in the files). That is a gap: the repo relicenses third-party IDLs as MIT. Prefer the upstream source for anything copied into our public repo.
3. Dependencies: none. 20 JSON files plus README, README_CN, LICENSE (`git ls-files`: 23 entries). No code, no scripts, no package manifest.
4. Tests: none.
5. Contents: pump, pump_amm, pump_fees; raydium_amm, raydium_pool_v4, raydium_clmm (+legacy), raydium_cpmm, raydium_launchpad; meteora_amm (+052), meteora_cp_amm 011/015, meteora_damm_v2, meteora_dlmm (identical to meteora_lb_clmm, same sha256), meteora_dynamic_bonding_curve; orca_whirlpool (+legacy), orca_lyf_orca.
6. Findings that matter:
   - `README.md:96-110` publishes a canonical sha256 per file ("`jq -S -c . | sha256sum`"). I recomputed with `jq` for `pump.json`, `pump_amm.json`, `raydium_cpmm.json`, `meteora_dlmm.json`: all four equal the README values. So the files are what the README says they are.
   - But the README also claims pump files track `pump-fun/pump-public-docs` "at commit `4795463...` or newer". The upstream file at that commit hashes to a different value (`pump.json`: `ab1b3b5a...`, README says `5a00cdb8...`), and upstream HEAD (`639b87fb45c3adeffa6f7c4a1bf0cb85e392bf22`, 2026-10-13) hashes to `a35349f3...`. So the claim that the shipped file equals upstream was NOT reproduced.
   - Structural diff shipped vs upstream HEAD, discriminators of common items: zero differences, program address identical. Upstream HEAD adds `buy_v3`, `sell_v3`, `buy_exact_quote_in_v3`, `multi_hop_curve_swap`, `sweep_*`, `set_quote_control_*` and 4 events to pump; `buy_v2`, `sell_v2`, `multi_hop_swap`, `sweep_*` and `SweepPoolFeeEvent` to PumpSwap. A decoder built from the shipped IDL silently skips those instructions.
   - `raydium_pool_v4.json` is NOT Raydium AMM v4 swap: its instructions are a leveraged-farm program (`initializeStrategy`, `borrow`, `swapLimit`, ...); `swapBaseIn` there is index 9 by coincidence (`raydium_pool_v4.json:645`). Use `raydium_amm.json` for AMM v4 (program id at `:2399`).
   - Legacy files (`orca_whirlpool_legacy.json`, `raydium_clmm_legacy.json`) have no `address` and no `discriminator` fields.
7. Decision: INTEGRATE as pinned data for the non-pump programs; for pump and PumpSwap take the IDL from `pump-fun/pump-public-docs` at a pinned commit (HEAD `639b87f` read today) and keep this repo only as a second copy to diff.
8. Pin: repo SHA plus sha256 of each file used. Raw sha256 (`shasum -a 256`) of the shipped files, first 12 hex, recomputed: `pump.json` `ffe966c42f1a`, `pump_amm.json` `2091433899b0`, `raydium_cpmm.json` `1202f6dc8e1c` (recompute at pin time).

Supply-chain review: only JSON and Markdown. `grep -l http *.json` finds one file (`orca_whirlpool.json`) containing two GitHub documentation URLs for Metaplex. No executable content. Result: clean.

### B4. solsonar/solana-multi-dex-decoder

1. Exists: yes. Default `main`. HEAD `8ae4c238c23fd337e08dc4c1377b839a4675bba3` (2026-05-12T14:58:36+02:00, message "bump version"). Last push 2026-05-12. 0 stars. 46 KB. Package `@solsonar/solana-multi-dex-decoder` 0.2.5.
2. License: `LICENSE` MIT, "Copyright (c) 2026 Andrija Vujovic" (as written in the file). `package.json` MIT.
3. Dependencies (`package.json`): none at runtime in `dependencies`; `@solana/web3.js`, `@coral-xyz/anchor`, `@meteora-ag/dlmm`, `@orca-so/whirlpools-sdk` are listed under `devDependencies` while the README treats them as peer/optional. `src/PoolDecoder.js:28-52` loads anchor, `@meteora-ag/dlmm` and `@orca-so/whirlpools-sdk` lazily with `createRequire`.
4. Tests: `test/decoder.test.js` (331 lines, 17 `test(` blocks), explicitly mock-based ("no real RPC needed"). No transaction fixtures.
5. Capabilities: `decodeAccount(owner, data)` for pool and token accounts of six DEXes; `parseSwapsFromTx(vtx, resolvedKeys, trackedPools)` (`src/SwapParser.js`) over `compiledInstructions` of the outer message. README states: no Jupiter, no ALT resolution, no quotes. Raydium AMM v4 direction is returned as `'unknown'`.
6. Versus our need: does not read inner instructions, `meta` balances, or jsonParsed; cannot decode transfers, WSOL, ATA, rent. Takes a `VersionedTransaction`, not RPC JSON. CHANGELOG entries describe use for "victim" transactions and "backrun arb executors" (`CHANGELOG.md` 0.2.2), i.e. a different problem (sandwich/backrun building).
7. Decision: REJECT. Keep its constants (`src/constants.js:14-69`) as one more cross-check, which already agrees with the IDLs (section 3.2).
8. Pin: `8ae4c23` only if the constants are cited.

Supply-chain review: `git grep` over `src`, `examples`, `test` for network, env, fs, process, eval. Findings: `examples/decode-pool.js:14` and `examples/parse-tx.js:13` default `SOLANA_RPC` to `https://api.mainnet-beta.solana.com`; `src/SwapParser.js:369` is a doc comment URL; `createHash` from `node:crypto` is used to compute discriminators (`SwapParser.js:3,25-37`). No lifecycle scripts, no `eval`, no fs, no `process.env` in `src`. `.gitignore` ignores `.env`. Result: clean. Small and single-commit, so provenance is weak, not malicious.

### B5. solana-program/token-2022

1. Exists: yes. Default `main`. HEAD `5251dcc07ecbcb721d6c4f0231090defadf00311` (2026-11-02T16:38:08Z). 223 stars. 729 files; `program/` 74, `interface/` 50, `confidential/` 33, `clients/` 547.
2. License: root `LICENSE` is Apache License 2.0 (read, lines 1-3); `clients/js-legacy/LICENSE` is a separate Apache file.
3. Dependencies: Rust workspace (pinocchio-based program). Not built here.
4. Tests: 63 files under `tests/` directories plus in-file unit tests (for example `interface/src/extension/transfer_fee/mod.rs` has `epoch_fee` test at `:226`; `program/src/processor.rs` has hundreds of lines of tests past line 9000).
5. Which extensions change the amount actually received (all paths are in the repo at the pinned SHA):

| Extension | Effect | Evidence |
|-----------|--------|----------|
| TransferFeeConfig / TransferFeeAmount | Credited amount is `amount - fee`. Fee = `min(ceil(amount * bps / 10000), maximum_fee)`; zero when bps is 0 or amount is 0. Fee schedule switches by epoch (`older_transfer_fee` before `newer_transfer_fee.epoch`). The fee is not burned: it is added to the destination account's `withheld_amount`. | fee formula `interface/src/extension/transfer_fee/mod.rs:58-70`; epoch selection `:151-157`, `calculate_epoch_fee :160`; inverse `calculate_pre_fee_amount :89`; processor computes fee at `program/src/processor.rs:419`, debits source by `amount`, credits `amount - fee`, adds fee to `withheld_amount` at `:574-587` |
| Withheld fees moving later | `HarvestWithheldTokensToMint` moves account-level withheld to the mint; `WithdrawWithheldTokensFromMint/FromAccounts` pays it to an authority account. These change token balances with no `transfer` instruction. | `program/src/extension/transfer_fee/processor.rs:117-192` (withdraw from mint), `:195-213` (harvest), `:229-292` (withdraw from accounts) |
| ConfidentialTransfer (+Fee, MintBurn) | Amounts are encrypted; the instruction data holds no plaintext amount. Public balance changes only on deposit/withdraw/apply-pending. | `program/src/extension/confidential_transfer/`, `confidential_mint_burn/`; processor gate `non_confidential_transfer_allowed` at `processor.rs:~566` |
| InterestBearingConfig | Raw amount never changes; the UI amount grows with time (`rate_authority`, `initialization_timestamp`, `last_update_timestamp`). A decoder must not mix UI and raw amounts. | `interface/src/extension/interest_bearing_mint/mod.rs:47-83` |
| ScaledUiAmount | Raw amount unchanged; UI amount = raw * multiplier, multiplier switches at `new_multiplier_effective_timestamp`. | `interface/src/extension/scaled_ui_amount/mod.rs:58-73`, `amount_to_ui_amount :82` |
| PermanentDelegate | Delegate can transfer or burn without owner signature, so a balance can fall with no owner-signed instruction. | `program/src/extension/permanent_delegate.rs`; used at `processor.rs:217,431` |
| TransferHook | Executes another program (`Execute`) during transfer; amount is unchanged but extra inner instructions and accounts appear. | `processor.rs:26,432,443`; `program/src/extension/transfer_hook/` |
| NonTransferable, Pausable, DefaultAccountState, CpiGuard, MemoTransfer | Reject or gate transfers (`TokenError::NonTransferable`, `MintPaused`), no amount change. Failed transfers must be excluded by `meta.err`. | `processor.rs:395-398, 425-428, 474-480` |
| MintCloseAuthority | Mint can be closed; not an amount effect. | `program/src/extension/mint_close_authority.rs` |

   What a decoder must therefore do: (1) read the instruction amount as the gross debit and compute the credit as `post_balance - pre_balance` of the destination, never assume equality; (2) for a mint with a `TransferFeeConfig`, record the withheld fee separately (instruction `transferCheckedWithFee` also carries an expected fee; jsonParsed shape not checked in this audit); (3) treat harvest/withdraw-withheld instructions as balance movements without a transfer; (4) never use `uiAmount` from `pre/postTokenBalances` as raw units for interest-bearing or scaled mints, use the string `amount`; (5) detect mint extensions from the mint account data (an extra `getAccountInfo`, not available offline) or flag "token-2022 mint, extensions unknown" instead of guessing; (6) skip failed transactions.
6. Decision: INTEGRATE as the specification (Apache-2.0). Re-implement the fee arithmetic in Python from `interface/src/extension/transfer_fee/mod.rs:58-70`, with unit tests built from the in-repo test vectors, not from this summary.
7. Pin: `5251dcc07ecbcb721d6c4f0231090defadf00311` and the sha256 of each cited file at that commit.

Supply chain: official `solana-program` org repository; only the cited files were read. No finding; coverage partial.

### C1. duckdb/duckdb

1. Exists: yes. `main`. HEAD `a76f27551c0903647d9484fcbf07086683aeeb92` (2026-11-02T18:55:18Z). Latest release `v2.0.0` (2026-10-21). 42,750 stars.
2. License: `LICENSE` (1,072 bytes) is MIT, "Copyright 2018-2026 Stichting DuckDB Foundation".
3. Dependencies: not audited (C++ project, wheels from PyPI).
4. Tests: large internal suite (not inspected).
5. Capabilities: SQL over parquet/JSONL/CSV, usable from Python. `/Volumes/PHI-Data/solana_forensics_v2/duckdb` exists but is empty; no duckdb is installed in the system Python (`import duckdb` fails).
6. Decision: INTEGRATE as the analysis engine, installed only from a pinned wheel when the project needs it.
7. Pin: wheel version and hash, tag `v2.0.0`.

### C2. pola-rs/polars

1. Exists: yes. `main`. HEAD `5075c5334fdf1436fa018db6cc5e736a792801a8`. Latest release `py-2.1.0` (2026-10-25). 40,251 stars.
2. License: `LICENSE` MIT, "Copyright (c) 2025 Ritchie Vink" with a second line crediting portions to NVIDIA (read via `gh api`).
3. Decision: REJECT, redundant with duckdb for this project and adds a second query engine to pin and audit.

### C3. moj-analytical-services/splink

1. Exists: yes. Default `master`. HEAD `41ef8b1db1311e3d95151524a7c392ed2141a362` (2026-11-02). Latest release `v5.0.0` (2026-09-18). 2,555 stars.
2. License: `LICENSE` MIT, "Copyright (c) 2020 Ministry of Justice".
3. Dependencies (`pyproject.toml`): `duckdb>=0.9.2`, `pyarrow>=18.0.0`, `sqlglot>=17.6.0`; optional altair, igraph, pyspark, sqlalchemy, psycopg2-binary.
4. Tests: 546 files in the tree including `tests/test_estimate_prob_two_rr_match.py`, `tests/test_expectation_maximisation.py`.
5. What it requires for calibrated probabilities (from `docs/topic_guides/training/training_rationale.md`):
   - a prior λ (`probability_two_random_records_match`) obtained from user-written deterministic rules plus a user-supplied recall guess (`linker.training.estimate_probability_two_random_records_match(deterministic_rules, recall=0.7)`); the doc says the guess must be roughly within half or double the truth;
   - `u` probabilities from random pair sampling (`estimate_u_using_random_sampling`, `splink/internals/linker_components/training.py:163`), valid because random pairs are almost all non-matches;
   - `m` probabilities by EM on blocked pairs (`estimate_parameters_using_expectation_maximisation`, `training.py:233`), which has no global-optimum guarantee;
   - the Fellegi-Sunter assumption that comparison columns are independent: "observations from different column/comparisons are independent" (`docs/topic_guides/theory/fellegi_sunter.md:129`);
   - optional labelled pairs (`estimate_m_from_pairwise_labels`, `training.py:361`) to check or train.
6. Would wallet linkage meet them? No, as things stand. (a) There is no ground-truth definition of "same entity" to build deterministic rules and a recall guess; any rule we choose is the hypothesis under test, so the prior is circular. (b) Wallet link features (shared funder, same slot, similar amounts, shared token set, program overlap) are strongly dependent, violating the independence assumption and inflating match weights. (c) Population structure (bundler farms, CEX hot wallets, router accounts) breaks the "random pairs are non-matches" premise for `u`. (d) There are no labelled pairs to calibrate against. Output "probabilities" would be uncalibrated scores.
7. Decision: REJECT for wallet linkage probabilities. It could be reconsidered only for a labelled benchmark where entity truth is known.

### C4. networkx/networkx

1. Exists: yes. `main`. HEAD `a325f6a948c0c2959fb48db205fa36534ea9429d` (2026-10-31). Latest release `networkx-3.7` (2026-09-21). 17,381 stars.
2. License: `LICENSE.txt` begins "NetworkX is distributed with the 3-clause BSD license." (Copyright 2004-2026 NetworkX Developers). GitHub's API reports `NOASSERTION` only because of the file name.
3. Decision: ADAPT for exploratory graph primitives (connected components, degrees). Exclude any "community" outputs from claims without a null model.
4. Pin: release `networkx-3.7` (installed wheel hash at install time).

### C5. jayrabol/solana-holder-clusters

1. Exists: yes. `main`. HEAD `a75a72965479a7b715b041148803d8004fe25079` (2026-07-30). One commit in the shallow history. 0 stars. Version 0.1.0.
2. License: `LICENSE` MIT, "Copyright (c) 2026 J Tools (j.tools)".
3. Dependencies (`package.json`): `@solana/web3.js ^1.95.0`; dev: tsx, typescript, vitest, `@types/node`. `package-lock.json` resolves only to `registry.npmjs.org`. `bin: solana-holder-clusters`. No lifecycle scripts (scripts are `build`, `test`, `typecheck`, `example`, `cli`).
4. Tests and fixtures: 21 test files in `test/`, built on `test/helpers/mock-connection.ts`. No recorded chain data.
5. What it is: a TypeScript library and CLI that, for one mint, fetches holders via `getProgramAccounts`, resolves each wallet's first funder, groups wallets sharing a funder, and scores concentration (`docs/METHODOLOGY.md`). It is not a dataset.
6. Biases and label origin (all from `docs/METHODOLOGY.md` and `data/`):
   - Label source: `data/known-entities.json` (1,041 bytes) has five entries (Binance, Binance.US, Coinbase, OKX x2), each "verified against Solscan's public account label". The description says the registry "grows ... during milestone 1", so this is a seed, not a labelled corpus.
   - First-funder resolution reads `getSignaturesForAddress` with `funderPageLimit = 1000` (`src/config.ts:94`); if the page is full the funder is left unresolved (`METHODOLOGY.md:91-92`). Section 7 admits "established wallets are systematically under-clustered" (`:163`) and "only first-funder links are computed" (`:164`). So the method detects young, single-funder wallets, which is exactly the bundle-farm case, and misses everything else: a selection bias toward the hypothesis.
   - Population is the top N holders (default 500) of a chosen mint, not a random sample of wallets or tokens. Supply coverage is reported, but the sample is conditioned on holding.
   - CEX and common-infrastructure funders are excluded by thresholds (`connectorHardShare 0.7`, `config.ts:91`) whose values the repo says differ from the author's production values (`config.ts:5` comment).
7. Can it be a control population? No. No data, no negatives, one author's heuristic output. Do not mix it with any population of ours.
8. Decision: ADAPT as method notes (document our own first-funder blind spots the same way); REJECT as data.
9. Pin: SHA above if cited.

Supply-chain review: `git grep` over `src`, `examples`, `test`, configs. Findings: `RPC_URL` / `SOLANA_RPC_URL` env read for the endpoint (`src/cli.ts:139`, `examples/*.ts`); the only file write is the CLI `--out` (`src/cli.ts:15,131`); the only embedded external link is `https://j.tools` in generated HTML (`src/html-report.ts:288`); no `child_process`, `eval`, telemetry, keystore access, or hidden Unicode; no 200+ character blobs. Result: clean. The repo advertises a commercial site; treat benchmark claims ("398 tests passing", "runs in production") as unverified.

### C6. ian05012/solana-memecoin-dataset

1. Exists: yes. `main`. HEAD `7070d00e1e4492f8604d988549d91785cc5f43f7` (2026-07-02). 5 stars. 303.6 MB across 16 files.
2. License: `LICENSE` is MIT, "Copyright (c) 2026" (holder name cut off by my read of the first lines; confirm at pin time). README states "Dataset and code are released under the MIT License".
3. Dependencies (`requirements.txt`): `pandas>=2.0`, `pyarrow>=14.0`, `curl_cffi>=0.6` (impersonates a Chrome TLS fingerprint), `aiohttp>=3.9`. No pins.
4. Shipped data (per README, NOT opened by me: no pyarrow or duckdb available and I did not install any): `tokens.parquet` 44,460 rows (11.0 MB), `trades-000..003.parquet` 9,500,565 rows (about 274 MB), `ohlcv.parquet` 272,426 rows, `sequences.parquet` 506,628 rows, `wallets.parquet` 11,817 rows, `wallet_funding.parquet` 15,493 rows. File sizes match the repo tree listing; row counts are README claims.
5. Sampling and labels (README):
   - Window: 2026-06-10 to 2026-06-30, "~20 days", "a single market regime".
   - Sampling frame: "freshly-graduated pump.fun tokens and the GMGN trending board", observed by one collector polling GMGN every 10 minutes. Tokens that never graduate or never trend are absent. The README itself lists survivorship bias ("2x rate (~11%) somewhat higher than the true population rate").
   - Labels: forward `max_return_1h/6h/24h/3d`, `reaches_2x`, `runner_peak_x`, exit simulations, back-filled from GMGN candles; "glitch candles ... have been removed and re-labeled", an undocumented cleaning step. Wallet labels (`smart_money`, `insider`, `normal`) come from GMGN tags and the author's own definition ("hit rate >= 40% (n>=5) and realized cash PnL >= 1.0").
   - Only `wallet_funding` comes from Helius history; everything else is GMGN's proprietary view, including `bundler_pct_holders`, `insider_pct_holders`, `cluster_*`, `sniper_*`. These are third-party classifier outputs, not ground truth.
6. Gap between the published scripts and the shipped data: the README says "the open-sourced scripts are a trimmed rewrite of the original collection pipeline (PostgreSQL; GMGN, DexScreener, GeckoTerminal, Birdeye, Helius)" and "the dataset itself has more columns than these scripts currently produce". The three scripts (`scripts/collect.py` 172 lines, `gmgn_client.py` 266, `label_returns.py` 100; read in full via `gh api`) write SQLite from GMGN only. So the dataset cannot be regenerated from the scripts, and the Helius funding table has no collector at all. The README also notes `tg_mention_count` is unreliable.
7. Can it be a control population? No, for three reasons: it is a convenience sample conditioned on graduation or trending (selection on the outcome side), it is one 20-day regime with a different definition of "early", and its labels (forward return, GMGN tags) are not our labels. Mixing it with any population defined by our own protocol would be mixing populations. It could at most serve to sanity-check a feature pipeline schema; no inference should cross over.
8. Decision: REJECT as a control. Do not download the parquet files into the project.
9. Pin: SHA above only if the schema is cited.

Supply-chain review (scripts read in full through `gh api`, not run):
- `requirements.txt`: unpinned `curl_cffi`, `aiohttp`; `curl_cffi` is a legitimate package but a TLS impersonation library, which is what you would use to evade bot protection; it is documented in the README as the way to reach GMGN.
- Network: only `https://gmgn.ai` (`gmgn_client.py:16`) via `curl_cffi`. `GMGN_API_KEY` is read from the environment (`gmgn_client.py:18`) and passed to `gmgn-cli` (`:60`). Nothing else read from env, no `.env`, no keystore or wallet file access, no webhook, Telegram or Discord endpoints (grep for `webhook|discord|telegram|keypair|private|secret|id.json|pickle|marshal|__import__|exec(|eval(` found only `has_telegram` field names).
- Hazard: `gmgn_client.py:62` runs `subprocess.run(f"gmgn-cli {cmd} --raw", shell=True)`, and `cmd` embeds `addr` taken from GMGN responses (`:127,156,171,227`). A hostile or compromised API response could inject shell syntax. It is active only when `GMGN_API_KEY` is set and `gmgn-cli` is on PATH (`:19`). Do not run these scripts with a key set.
- Result: no malware found; one real command-injection hazard in an optional path.

### D1. wormhole-foundation/wormhole-sdk-ts

1. Exists: yes. `main`. HEAD `2a8ea439ef7c928aa0d0d139ec008c1a11909b2a` (2026-10-27T12:27:42-03:00). 84 stars. 1,026 files; workspace version 1.20.0.
2. License: root `LICENSE` is Apache 2.0 (read lines 1-3). Core packages declare Apache-2.0 (`core/definitions` manifest omits the field; root and `connect`, `core/base` state it).
3. Dependencies: a large npm workspace (`platforms/*`, `core/*`, `connect`); Solana platform pins `@coral-xyz/anchor 0.29.0`, `@solana/spl-token 0.3.9`, `@solana/web3.js ^1.95.8`. Root `package.json` has a `prepare: husky` lifecycle script and `prepublishOnly`; no `postinstall`/`preinstall` found (`git grep`).
4. Tests and fixtures: `__tests__/` (integration, tilt, mocks), `platforms/aptos/__tests__/integration/fixtures/*.json`, `platforms/solana/__tests__/{unit,integration}`. No offline Solana VAA vector confirmed.
5. What makes a cross-chain message verifiable (with paths):
   - VAA layout: header `version` (1 byte), `guardianSet` (4 bytes, `core/definitions/src/layout-items/guardianSet.ts`), `signatures` array each with guardian index and secp256k1 signature (`core/definitions/src/vaa/vaa.ts:37-41`); envelope `timestamp` (4), `nonce` (4), `emitterChain`, `emitterAddress`, `sequence`, `consistencyLevel` (1) (`vaa.ts:44-51`); then payload.
   - Identity of a message: (emitterChain, emitterAddress, sequence). The SDK builds the lookup `.../v1/signed_vaa/${chainId}/${emitterAddress}/${sequence}` against `api.wormholescan.io` (`connect/src/whscan-api.ts:134-146`, `connect/src/config.ts:17`).
   - Hash that guardians sign: `keccak256` over envelope plus payload (`core/definitions/src/vaa/functions.ts:189`, `create.ts:47`); the `vaa.ts:69-71` TODO notes that on EVM the core bridge actually uses a double keccak.
   - Guardian signature checks in the SDK: `deserialize` only enforces ascending, unique guardian indices (`functions.ts:171-175`). Signature recovery primitives exist (`core/definitions/src/signature.ts:27-42`) but outside tests they are not called to verify a VAA against a guardian set. The authoritative verification is the core bridge contract (Solana: `verify_signatures` + `post_vaa`; account readers in `platforms/solana/protocols/core/src/utils/accounts/{guardianSet,signatureSet,postedVaa}.ts`). So a forensic claim "verified" needs (a) the signed VAA bytes (from Wormholescan or guardians), (b) the guardian set at that index, (c) a quorum check, none of which this SDK performs for us.
   - Solana-side attribution: `platforms/solana/protocols/core/src/core.ts:52` `SOLANA_SEQ_LOG = 'Program log: Sequence: '`; `parseSequenceFromLog` (`:236-269`) reads the sequence from the log and the emitter from `accounts[ix.accounts[2]]` of an inner core-bridge instruction; `parseTransaction` (`:374-420`) falls back to the posted message account (`parsePostMessageAccount :347`, layout `postMessageLayout.ts`). Heuristic: it takes the first sequence log and indexes by position. Core bridge on Solana: `worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth` (`core/base/src/constants/contracts/core.ts:8`).
6. Decision: ADAPT. Use the layout and the log/account recipe as a specification to write our own Python parser and to link a Solana transaction to (chain, emitter, sequence); verification of the VAA remains an explicit extra step. Do not depend on the SDK.
7. Pin: `2a8ea439ef7c928aa0d0d139ec008c1a11909b2a`; sha256 of `vaa.ts`, `functions.ts`, `core.ts` (Solana), `whscan-api.ts`.

Supply-chain review: lighter than for the small repos because of size (1,026 files, mostly generated docs and per-chain platforms). Checked with `git grep`: lifecycle scripts, `eval(`, `child_process`, `execSync`. Findings: `tokenRegistry/src/scripts/importConnect.ts:93` calls `eval(tokenObjJsStr)` in a development import script (not part of the SDK runtime); `.github/workflows/claude.yml` exists (CI, not read in full). No other finding. Coverage partial.

### D2. jito-labs/searcher-examples

1. Exists: yes. Default `master`. HEAD `efa92a9f90f3954532057324b6f81c6120466fb8` (2026-10-19T10:34:40-05:00). 432 stars. 21 files.
2. License: `LICENSE` Apache License 2.0.
3. Dependencies: Rust workspace (`Cargo.toml`, `Cargo.lock`): `cli`, `jito_protos`, `searcher_client`. `jito_protos/protos` is a git submodule (`.gitmodules`: `https://github.com/jito-labs/mev-protos.git`), empty in my clone because submodules were not fetched. `jito_protos/build.rs` compiles `auth`, `block`, `block_engine`, `bundle`, `packet`, `relayer`, `searcher`, `shared` protos with `tonic_build`. `Dockerfile` downloads `protoc` from `github.com/google/protobuf/releases` and uses `rust:1.66.0` (build only).
4. Tests: none.
5. What it shows (`cli/src/main.rs`, `searcher_client/src/lib.rs`): authenticate to a block engine (challenge-response with a local keypair, `read_keypair_file` at `main.rs:121-124, 237`), fetch tip accounts and next scheduled leader, send a bundle (`SendBundle`, `main.rs:229`), and wait for `SubscribeBundleResults` (`main.rs:249-250`, `lib.rs:97-160`), matching `Accepted{slot, validator_identity}` or `Rejected{...}` for the bundle we just sent, keyed by the UUID returned by the block engine (`lib.rs:116-117`).
6. Is any public, verifiable source of bundle membership shown? No. The results stream is returned to the authenticated submitter for its own bundles. `git grep -niE "getBundleStatuses|bundle_status|landed_slot|explorer|get_bundle"` returns nothing. There is no code that, given an arbitrary landed transaction, tells whether it belonged to a bundle. Therefore membership of past bundles cannot be established from this repository. Temporal proximity (same slot, adjacent transactions, same tip pattern) is not bundle membership and must never be written as such; at most it supports the weaker statement "adjacent in the same slot", with the evidence class named. A tip transfer to one of the documented tip accounts is a clue that a bundle may have been used, not proof of which transactions were bundled.
7. Decision: REJECT as a source. If the protos are ever needed, pin `mev-protos` separately.

Supply-chain review (21 files, read where relevant): the file named `s` (338 bytes) is a deploy helper: it does `export $(cat .env | grep -v '#' | awk '/=/ {print $1}')` and then `rsync -avh --delete ... "$HOST":~/` (`s`, lines 5-14). It reads a local `.env` and syncs the repo to `$HOST`; `--delete` makes it destructive on the remote. Not run. It is not exfiltration of secrets but it is a script that reads `.env` and contacts a host, so it must not be executed. The CLI reads a keypair file only when the user passes a path (`main.rs:121-124, 237`) and sends only to the user-supplied `block_engine_url` (`main.rs:35`) and `rpc_url`. No hard-coded endpoints, no telemetry. Result: no malicious finding; one script flagged.

## 5. Not verified

- Parquet contents of `solana-memecoin-dataset` (row counts, columns, label rates, date range, overlap with our tokens): README claims only. No parquet reader was available and none was installed.
- The `LICENSE` holder name for `solana-memecoin-dataset` (line truncated in my read) and whether upstream licenses of third-party IDLs inside `solana-program-idls` permit MIT redistribution.
- Whether the shipped pump IDLs ever equalled upstream at the claimed commit `4795463...`: my hash of upstream at that commit differs from the README's.
- Any value in section 3 against live mainnet transactions. All agreement is between files plus SHA-256 recomputation; no discriminator was observed in a real transaction in this audit. Jupiter `exact_out_route`, `route_with_token_ledger`, `*_v2` variants not extracted.
- Raydium AMM v4 `ray_log` layout and the Raydium CLMM event emission path.
- `transferCheckedWithFee` field names in jsonParsed output and which fields RPC puts in `parsed.info` for Token-2022 extension instructions.
- The behaviour of `solana-dex-parser` when actually run (never installed or executed): its accuracy on Token-2022 fees, WSOL wrap/close, rent refunds, inner instructions, and pump.fun `*_v3`; that is to be measured on a hard-transaction set before relying on it.
- Whether `sol-parser-sdk` fixtures are real mainnet transactions (only `dbc_swap2.json` is self-declared synthetic) and whether they carry full signatures.
- Whether `sol-parser-sdk` decodes plain system or SPL transfers (not checked; it appears event-oriented).
- Supply chain, partial coverage: `carbon` (11,521 files, only cited files read), `wormhole-sdk-ts` (1,026 files, pattern scan only, `.github/workflows` not read), `token-2022`, `yellowstone-grpc`, `duckdb`, `polars`, `splink`, `networkx` (license and metadata only; no code audit). For the small repos (`solana-dex-parser`, `solana-multi-dex-decoder`, `solana-holder-clusters`, `sol-parser-sdk`, `searcher-examples`, `solana-program-idls`) the scan was pattern-based over all source files plus full reads of manifests, configs and the files cited; 118 Rust files in `sol-parser-sdk/src` were not read line by line. Transitive npm/crates dependencies were not audited.
- Whether the git history (only HEAD was fetched, `--depth 1`) ever contained secrets or removed malicious code; single-commit appearance in `solana-dex-parser`, `solana-holder-clusters` is a consequence of the shallow clone and is not evidence of a squashed history.
- Star counts and "push dates" come from the GitHub API on 2026-11-02 and drift.
- Legal readings (AGPL scope, relicensing of IDLs) are engineering interpretations, not legal advice.
