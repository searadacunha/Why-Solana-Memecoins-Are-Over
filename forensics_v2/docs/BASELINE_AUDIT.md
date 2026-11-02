# Baseline audit of the existing Solana forensics code

Scope: worktree `WSMO-forensics-v2`, branch `forensics-v2`, HEAD 6565245 (= origin/main). Read-only audit, written 2026-11-02.
Purpose: let the new engine reuse what is correct and not rebuild it, and not inherit the defects listed in section 4.

Method: knowledge graph first (`graphify query ... Why-Solana-Memecoins-Are-Over/graphify-out/graph.json`, 3504 nodes, used only to find the pagination and 429 modules), then every file below was read. Nothing was executed except `wc`, `gzip -dc | head/jq` on derived files. No collector, no `run_all.py`, no network. Line numbers refer to this worktree.

Baseline test state, from `forensics_v2/docs/baseline/_m_pytest__q_.log`: `95 passed`. `SUMMARY.txt`: `run_all.py --strict rc=0`, `ruff rc=0`. These 95 tests cover `rpc_client`, `lib_verif.first_signature`, `splitlib`, `expl_ledger.wallet_view`, `pumplib`, `statlib`, settings, redaction and the cache preflight. There is no test for `ed_trace.txflow`, `fn_trace.funder_of`, `fparse.parse`, any versioned-transaction fixture, or an empty page in the middle of a history.

## 1. Read this first: the five facts that matter most

1. The shared paginator treats an empty page as genesis. `code/rpc_client.py:197-198` (`if not page: break`) and the short-page stop at `:205-206`. The repository itself documents that Helius sometimes answers `result: []` mid-history under load (`data/trace_temoins/14_corrige_pages_vides.py:1-30`: 3 of 111 addresses wrongly marked "genesis reached", one of them an industrial address read as resolved in 6 witnesses). That fix (re-ask the same page 3 times, conclude only on 3 empty answers) was applied only in that one script. `walk_sigs`, `ed_trace.Fetch.page` consumers, `fn_trace`, `col_20_wallets`, `lib_verif.first_signature` and `04_early_buyers_funding.all_signatures` all still conclude "genesis" on one short or empty page.
2. A truncated history is often used as if complete. Worst cases: `code/03_split_detector.py:79-90`, `code/04_early_buyers_funding.py:101-106`, `code/v07_exit.py:39-48`, `code/a8_wallet_horde.py:88`.
3. The best destination logic is `exit_destination/code/ed_trace.py:150-225` (`txflow`): net lamport delta, owner-level token deltas, WSOL netted in, Jito tips excluded, co-signers recorded. It was written because the "first System transfer" rule is wrong (comment at `:189-194`). Every older module in `code/` (02, 05, 06, a8, 04, 03) uses a cruder rule. The new engine should build on `txflow`, with the fixes in section 4.
4. Money is float SOL almost everywhere, and token amounts use `uiAmount` (float) rather than the integer `amount` string: `ed_trace.py:172`, `fparse.py:53`, `v07_exit.py:50-51`, `v03/v04/v05/v06`. Only `a9` and `splitlib` round to 9 decimals, which is exact to the lamport but still float-keyed.
5. The "two collections" for the FNqJtYs...pump case (section 6) share zero wallets. The repository says in `code/a9_g2y_prelaunch.py:13-16` that neither file proves which one is complete. The new engine must settle it from chain data, not from either file.

## 2. Module inventory

Status legend: OK = correct for its stated scope; PARTIAL = correct but bounded or flagged incompletely; GAP = missing capability.

### 2.1 `code/rpc_client.py` (262 lines)

Computes: the single Helius client. JSON-RPC (`rpc`), parsed-by-address "enhanced" API, disk cache.

Works:
- One error rule, enforced: a call returns or raises `HeliusError` (`:11-15`, `:141-164`). `result` missing raises (`:160-161`). `getSignaturesForAddress` non-list raises (`:162-163`). Only `tolerate_codes` yields `None` (`:157-158`).
- HTTP 429/5xx retried with backoff (`_http` `:82-109`); key rotation with 6 s cooldown on 429 (`_http_rotating` `:112-137`, `_available_key` `:64-79`). Exhaustion raises (`:136-137`).
- `walk_sigs` raises when `max_pages` (400) is exhausted before genesis or `until_ts` (`:190-194`). That is the right default. Tested at `tests/test_rpc_client.py:110-126`.
- Atomic cache write (`:259-261`).

Partial / defects:
- `:197-198` empty page = genesis (fact 1). `:205-206` short page = genesis.
- `:207-208` the `until_ts` stop happens after appending the whole page, so the result contains entries older than `until_ts` although the docstring says "exclusive". Callers must re-filter (`expl_ledger.py:157-159` does; `04_early_buyers_funding.py:40-41` does not, it only sorts).
- `walk_sigs` returns `(sigs, pages)` with no `genesis_reached` flag. When it stops on `until_ts` the caller cannot tell it from genesis.
- `:123` and `:130-131` classify errors by substring of the message (`"429" in last`). Works, fragile.
- `tx()` `:212-214` returns `None` on a null result and does not raise. Every caller then silently skips: `02_cn_outflows.py:164-165`, `05_trace_origin.py:120-121`, `04_early_buyers_funding.py:57-58,108-109`, `09_bundle_snipe.py:295`, `03_split_detector.py:92-93`.
- `cached()` `:246-262` writes whatever `fn()` returns, including `None`, so a null `getTransaction` (not yet available, or pruned) is cached forever as `null` (`lib_verif.get_tx` `:62-64` goes through it).
- `maxSupportedTransactionVersion` is 0 in `tx` (`:213`), `block` (`:218`), `lib_verif.py:65`, `expl_ledger.py:96`, `03_split_detector.py:144`. The newer collectors use 1 (`post_detection_forensics/code/col_10_windows.py:15`, `ed_trace.py:36`) with the comment that a cap of 0 fails with -32015 on version-1 transactions (`col_10_windows.py:11-14`: 542 windows lost on 2026-09-29). With `rpc_client` the failure raises, so it is loud, but the legacy `code/` modules cannot read a version-1 transaction at all.
- No batch JSON-RPC in this client.

### 2.2 `post_detection_forensics/code/frpc.py` (111 lines), used by all newer collectors

Per-key pacing (`:40-51`), 429 handled separately with doubling wait (`:73-80`, up to 40 429s), same raise-never-None rule (`:93-101`). Better than `rpc_client` for long collections. Defects: `:99` returns `None` if the response has no `result` key (malformed answer), which `Fetch._call` (`ed_trace.py:96-99`) converts into an error, but direct users such as `col_10_windows.window` check `None` themselves (`:75-76`) while `frpc.sigs` checks it (`:109-110`).

### 2.3 `code/02_cn_outflows.py` (193 lines)

Computes: all outflows of one service address in a date window, then split detection (`splitlib`).

Works: the lamport-delta approach, not "first System transfer" (`outflows_of_tx` `:93-119`, rationale `:96-98`). It catches a wrapped-SOL close that moves lamports with no System transfer. Window selection by signature page then read only the window (`:58-90`).

Partial:
- `:67` `for page_i in range(max_pages)` ends silently at the cap; only a printed warning (`:143-145`) and `window_fully_covered` in the meta file (`:153`). No raise.
- `:162` `kept[:a.max_tx]` (default 5000, `:130`) silently truncates the window. `n_tx_read` is recorded (`:176`) but nothing flags that the window was cut.
- `:72-79` failed transactions are not excluded (`err` is never read), so a failed transaction is fetched and its zero deltas are harmless but cost calls.
- `:74` signatures with null `blockTime` are skipped silently.
- `:164-165` `if tx:` drops null transactions.
- `:113-118` every other account whose balance rose by 1 to 20 SOL is credited as an outflow of `addr`, even when `addr` is not the sender of that SOL (several senders in one transaction, bundles). No netting of what `addr` actually lost.
- `:116` float division; recipients only by lamports, so SOL kept wrapped (WSOL token account balance) is invisible.
- Recipient index uses `accountKeys` only (`:101-104`), see section 3 item 3.

### 2.4 `code/03_split_detector.py` (174 lines)

Computes: given a wallet set (token top holders or explicit list), the incoming SOL of each, then `find_splits`, plus a control group for the false-positive rate.

Works: the control-group idea (`:139-158`) and the balance-delta funding read (`:72-103`).

Defects:
- `:79-90` `max_pages=3` (3000 newest signatures), then `sigs[-60:]` is read as "the oldest = the initial funding". If the wallet has more than 3000 signatures, or the loop ended on the page cap, those 60 are not the oldest. No genesis flag is kept. Silent.
- `:82-89` ends on a short page without the empty-page confirmation.
- `:58-69` `getTokenLargestAccounts` returns at most 20 accounts on the RPC side (known RPC behaviour, not run here), so `--top 30` cannot give 30. Owners are current holders, which says nothing about the launch (the repo says so itself in `04_early_buyers_funding.py:4-8`).
- `:98` swallows missing fields (`continue`), `:92-93` drops null transactions.
- `:153` seeds the global `random`.
- Exploratory, absent from `run_all.py` (`:18-20`).

### 2.5 `code/05_trace_origin.py` (219 lines)

Computes: multi-generation upstream trace of a distributor, keeping the top-3 funders per level.

Works: the honest flagging for strategy `deep`: `deep_signatures` returns `(sigs, genesis_reached)` (`:67-83`), printed and stored (`:170,182,210`). The docstring (`:4-8`) names the pagination trap.

Partial / defects:
- Strategy `sample` (`:86-106`) keeps about 60 signatures per page and always returns `complete=False` (`:106`). It cannot establish an origin; output says "NON atteinte" (`:170`, `:210`).
- `:117` `sigs[:max_tx]` (default 600, `:150`) on the time-ascending sample: reads only the oldest 600 retained signatures.
- `:129-137` source = every other account whose balance fell by 1 SOL or more, excluding only three program ids (`SYSTEM` `:58-60`). A pool vault or any router account in a swap becomes a "source". No WSOL decoding. Fee not added back for the fee payer.
- `:120-121` null transaction skipped. Floats.
- `KNOWN` (`:50-57`) is duplicated in `06_hub_map.py:36-43` and in all six `data/trace_*/lib_trace.py` with different contents (the six `lib_trace.py` copies hash to 4 distinct md5 values).

### 2.6 `code/06_hub_map.py` (122 lines)

Computes: inflows, outflows, repeated outflow amounts and recycling for a hub, from the Helius enhanced API (`nativeTransfers`, 100 per page).

Works: uses already-decoded transfers, cheap for hubs; recycling set intersection (`:89-90`).

Defects:
- `:58` `a.pages` default 30 = 3000 transactions; the loop ends silently. The JSON (`:113-117`) records `n_tx`, `oldest`, `newest` but no "history complete" flag.
- `:68-82` only `nativeTransfers`: no WSOL, no token-account owner mapping.
- `:82` `round(amt, 6)` as the repeated-amount key; floats.
- `:86` `fromtimestamp(oldest)` raises if every timestamp is 0.
- Whether the enhanced API lists failed transactions and inner-instruction transfers separately (risk of double counting a sweep): not verified.

### 2.7 `code/splitlib.py` (67 lines) and `tests/test_splitlib.py`

Computes: `find_splits(funding)`, wallets grouped by near-equal amount (relative tolerance `REL_TOL = 1e-4`, `:22`) within a window (`WINDOW_S = 3600`, `:23`), at least 3 wallets (`:24`).

Works: pure function, no network, deterministic, fuzz-tested against an independent copy (`tests/test_splitlib.py:60-80`, `a1_null_model.py`). The only reusable piece of the old splitting heuristic.

Limits (design, not bug): clusters are anchored on the lowest-amount event of the group (`:40-51`), the window is measured to the anchor, not to the group span, so the true span can reach twice the window. Tolerance is relative 0.01 %, not "equal at nine decimals", so it is looser than the claim the README makes (the nine-decimal test lives in `a9`). `:57` imports inside the loop. Greedy, so it is order dependent for overlapping groups.

### 2.8 `code/a6_gateway_chains.py` (174 lines)

Computes: dated chains gateway (G2Y) -> distributor -> early buyer, per token, hop 0 and hop 1, reading committed files only (`:26`).

Works: the temporal rules are the correct ones and are applied before counting: gateway must pay the distributor before the distributor pays the buyer (`:109-113`), and a payment after token creation is dropped and counted separately (`:114-120`). Coverage per token is printed (`:123-127,141-145`). The honest scope note (`:19-22`).

Defects: `incomplete` (`:65`) is computed and its size exported (`:171`) but never attached to individual chains, so a chain through an address with unknown history is not distinguished. `:93` takes the earliest gateway payment only. Hop 2 and beyond absent. Input files `data/trace_*/e2_funding_*.json` carry the `nature == "financement"` label produced elsewhere (`:80`); that label is trusted without recomputation.

### 2.9 `code/a7_cross_token_links.py` (123 lines)

Computes: recurring exact amounts across tokens, shared wallets, funding sessions, from `data/split/all_buyers_g2y.json`.

Works: tests 1 and 2 (`:51-80`) are straightforward set operations.

Defects: the header promises that session clustering is "compared against the gateway's own traffic" (`:17-19`); no such base rate is computed (`:83-97`). Sessions chain any two payments less than 6 h apart (`:86`), so a busy gateway makes arbitrarily long sessions. Amount keys are `round(h["sol"], 9)` floats (`:44`). A null shared-wallet result is correctly labelled non-informative (`:77-80`).

### 2.10 `code/a9_g2y_prelaunch.py` (343 lines)

Computes: per phase-1 token, the virgin wallets credited by the gateway before token creation, largest exactly-equal amount group, delays; reconciles the reference token against the second collection.

Works: `groupe_montant_max` (`:72-94`) deterministic, exact equality at nine decimals, no tolerance; `mesure_token` returns rejections instead of dropping tokens (`:97-132`); the output reproduces README Act I (`docs/out/a9_g2y_prelaunch.json`: 9 wallets, `montant_sol 2.9768156`, `etendue_s 343`, delay 7.7131 h from first credit, 7.6178 h from last).

Defects: `:181-184` the "lecture" text is a constant that states "no shared wallet and no reference amount" regardless of the counters computed just above (`:165,180`); `:333` hard-codes 7.6. `:67` `float(g["sol"])`. It trusts the `avant_token` flag of the input file (`:63`) rather than recomputing it from `creation` and `ts`.

### 2.11 `code/expl_ledger.py` (291 lines) and `tests/test_ledger.py`

Computes: SOL landing on the author's exchange deposit address 2024-10-01..2025-02-02, valued per day at the Binance SOLUSDT close.

Works: reads the wallet's own balance delta (`wallet_view` `:102-125`); skips failed transactions (`:109-110`, and `:158`); raises on null transaction (`:97-98`), null blockTime (`:121-122`) and missing price day (`:181-182`, `:223-224`); walks signatures with the raising `walk_sigs` (`:89-90`); separates incoming from sweeps; publishes the return-of-capital candidates instead of hiding them (`:201-206`); every claim is tagged MESURE / INFERE / NON_ETABLI.

Defects: `:159` `(s.get("blockTime") or 0)` silently excludes any signature without a blockTime. `:117-118` floats; sums of float SOL. `:124` sender = most negative delta in the same transaction, which can be the fee payer or a tip account; the code says so (`:103-107`). `:94-99` the cache stores the transaction; a transaction that bundles two inflows counts as one (`:279-281`). Handles only the lamport balance, which is right for a deposit address.

### 2.12 `code/m5_roundtrip.py` (412 lines)

Computes: round-trip PnL under ten exit policies from captured swap flows (`P.load_captures`), not from RPC.

Works: the whole simulation is a pure function of the capture (`simulate` `:173-269`, `Book` `:105-166`); conventions X1 to X12 documented at `:10-34`; temporal-cluster unit (`CLUSTER_GAP = 1800`, `:70`; `P.cluster_bootstrap_mean_ci`); hard and soft non-fill conventions both reported (`:353-361`).

Defects: `:379-399` the printed "LECTURE" embeds numbers (+3.3 %, -12.9 %, "ten of ten") as constants, not computed. It does not touch the chain, so it is not a forensics component for the new engine; only reusable as the exit-policy cost model.

### 2.13 Other modules the new engine will meet (not in the requested list, noted because they hold the reusable chain logic)

- `post_detection_forensics/code/fparse.py` (211 lines): one transaction to one record, trade read from balance changes by token owner and from the pool's WSOL balance, not from instruction names (`:1-23`, `:101-143`). Handles WSOL (`:37,109,142-143,186-190`), Jito tips (`:96-99`), routers (`:46-49`), the creation-slot curve transfer (`:64-76`). Defects: `:21-22` states that the order of transactions inside one slot is unknown; `:209` `out.sort(key=(slot, bt))` is stable, and the input list `w["sigs"]` comes straight from the API in newest-first order (`col_10_windows.py:68-69`), so ties inside a slot stay in reverse order. `uiAmount` floats `:53`. `:111` balances indexed by position over `accountKeys`.
- `post_detection_forensics/code/col_10_windows.py` (window collector): pages the mint's signatures from a block cursor and raises if 50 pages do not reach the creation slot (`:96-111`, the raise at `:66-67` of the window function), raises on null transaction (`:75-76`) and when the creation slot is empty (`:78-79`). A good pattern.
- `post_detection_forensics/code/col_20_wallets.py`: wallet genesis. `prior()` (`:100-106`) marks `genesis: len(page) < 1000`; `funding_of()` (`:109-129`) takes the oldest signature's transaction and calls funder the account with the largest balance fall (`:119-120`). That is "first activity = creation" (section 3 item 6). Hubs: more than `HUB_PAGES` pages is recorded as a hub, not as complete (`genesis` `:132-165`, `genesis_before` `:210-240`), which is the honest handling.
- `code/lib_verif.py`: `first_signature` (`:75-93`) caps at 40 pages and returns `censored=True` (tested, `tests/test_lib_verif.py:51-59`) but `:87-88` `if not r: break` still treats an empty page as the end and the final return then flags `censored=True` only because it falls through the cap path: an empty page mid-history is flagged as censored, not as genesis, which is the safe direction. `get_tx` `:62-64` caches nulls (see 2.1).
- `code/09_bundle_snipe.py`: `buyers_of_tx` (`:210-230`) sums System transfers and `createAccount` funding into the bonding curve across inner instructions (`_instructions` `:201-207`), so a bundle co-signed by several wallets is attributed to each payer. `oldest_sigs` (`:241-269`) returns `complete` and `measure` refuses to measure if not complete (status `pagination_incomplete`). Defect: `:295` null transaction skipped; empty page at `:77` treated as complete.
- `code/04_early_buyers_funding.py`: produced `data/split/all_buyers_g2y.json`. Defects: `:101-106` reads `sigs[:40]` even when `complete` is False (only prints a warning); `:61` takes the first signer of each early transaction, so multi-signer bundles are attributed to one wallet; `:41,92` sorts by `blockTime` only so ties stay newest-first.
- `code/a8_wallet_horde.py`: `naissance` (`:65-83`) returns the oldest blockTime as the address "birth", and `etudie` (`:118`) calls an address fresh if that "birth" is within 3600 s of its first receipt. Pagination: `:88` `range(25)` x 100 = 2500 transactions then stops, status still `"ok"`. Only `nativeTransfers` (`:99`).
- `code/v07_exit.py`: ATA-centred exit chain (`ata_of` `:27-37`, `classify` `:51-80`): the right answer to the token-account gap, since it walks the account's own signatures. Defect: `sigs_all` `:39-48` caps at 6 pages without any flag; `:50-51` `uiAmount`.
- `code/v04_slot_order.py`: execution order inside the creation slot from `getBlock`, in block order (`:1-12`), the only place where intra-slot order is read from the right source.
- `data/trace_*/lib_trace.py` (six copies): `all_signatures` (`:109-169` in `trace_h2w6`) retries a lost page 3 times before refusing to declare genesis (`:124-131`), projects hyperactive wallets as unmeasured, and returns `genesis`. But `:137` `if not pg: genesis = True`, and `helius_parsed` (`:215-236`) returns `[]` when the key is missing (`:219`), on a 404 (`:232`) and after the retries fail (`:236`). That is a silent empty.
- `data/trace_h2w6/11_trace_h2w6.py`: the only JSON-RPC batch code. See section 4, item 1.

### 2.14 `exit_destination/` (code `ed_00` .. `ed_40`, `ed_lib.py`, `ed_trace.py`)

Computes: for 300 exit wallets (1,457 events), what each does after receiving a launch's tokens from snipers, and where the SOL goes (branches followed up to `MAX_HOPS = 5`, `ed_lib.py`).

Works (strongest piece of the repo):
- Budgeted fetcher: hard call cap, failure-share stop, null becomes an error (`ed_trace.py:75-100`); offline mode raises `NotCollected` instead of returning empty (`:76-77`).
- Coverage is carried in the data, not hidden: `reached_first`, `older_end`, `newer_complete` (`wallet_listing` `:341-392`), `status = "history not reached"` (`:410-412`), `truncated` (`:408`), `status = "cap"` (`:425`), `too active` (`:514`), terminal `H6` with a reason for budget, cycle, rpc failure (`Branch.step` `:581-600`). Hub status measured and recorded, not assumed (`:517-523`).
- `txflow` (`:150-225`): net lamport delta per account, fee added back to the fee payer (`:196`), token accounts excluded from the recipient candidates (`:198`), Jito tips excluded, wrapped-SOL owner delta netted into the loss (`:200`), fallback to the owner with the largest WSOL gain when SOL stays wrapped (`:204-207`), `signers` list kept so co-signing can be tested (`:164`), transfers inside a trade kept apart (`trade_out` `:216-224`). Includes inner instructions (`_instructions` `:143-147`).
- Offline rebuild from cache gives the same paths as the collection (`ed_20_build.py` reuses `run()` with an offline `Fetch`).
- Same-slot order: `event_trace` takes everything newer than the receipt signature when it is listed (`:402-405`).

Partial / defects:
- `:172` token amounts via `uiAmount` floats; `:177` rounded to 6 decimals.
- `:406` and `:512`: when the receipt (or inflow) signature is not listed, the fallback is by slot (`e["slot"] > rc["slot"]`, `next(... e["slot"] <= inflow["slot"]) - 1`), which drops or misplaces other transactions in the same slot. This is the intra-slot weakness (section 3 item 7).
- `Fetch.page` `:102-119` caches by `(addr, before, until)`; a `before=None` page is therefore frozen at first collection. Fine for a frozen study, wrong for a live engine.
- `Fetch.page` `:114-117` keeps `err` as a boolean, drops the error content.
- `txflow` indexes `meta.preBalances` by position over `message.accountKeys` with no length assertion (`:171,174`); `signer = keys[0]` (`:155`).
- The recipient is a single account, the one with the largest lamport gain (`:203`). A sweep that splits into two equal halves is attributed to one.
- Only the exit wallet's own signatures are listed (`wallet_listing`): a token transfer received into an existing token account is not in them; the code records `receipt_listed` (`:402`) and falls back to the slot, it does not look up the token account's signatures.

### 2.15 `economic_mechanics/` (`em_lib.py`, `em_10_build`, `em_20_analysis`, `em_30_extra`)

Computes: roles, funding architecture, lifecycle, returning flows, exit synchrony, reuse, with nulls. `em_lib.clusters` (`:378-402`) is a union-find over launch-wallet, funder-sniper, deployer-funder and common-source links.

Works: `hop(addr)` raises `MissingCacheError` when a required genesis-hop file is absent, so an absent cache cannot stand for an empty history (`:105-134`); `require_hops` fails before any write; permutation nulls (`perm_test`, `null_funding`, `null_pairs`). Tests: `tests/test_cache_preflight.py`.

Defects: `clusters` is a transitive closure with no size cap; one hub-like node can merge groups (hubs excluded through `fkey` `:87-98`, but only when the hub flag is known; `strict` option handles unknown). The collection that fed `snipers[*].gen_funder` is `col_20_wallets.py` (see 2.13), so the same first-activity assumption applies.

### 2.16 `coordination_detection/` (`cd_00_coverage`, `cd_10_build`, `cd_20_analysis`, `cd_lib`)

Computes: whether the sniper wallets of a launch show a funding and buying structure (two snipers on one non-hub funder, synchrony, ticket structure via `tickets` `:142`, funder graph `:166-265`, causal reuse `:267-300`), against nulls. `derived/cd_table.jsonl.gz`: 1,657 rows (`wc -l` after `gzip -dc`).

Works: purely offline on frozen tables (no urllib or rpc import, checked by grep); freeze and integrity JSON; `reuse_causal` uses only information at or before each launch. Reusable as the specification of the group definitions, not as chain code. No RPC code to reuse here.

### 2.17 `funder_network/` (`fn_00_inventory`, `fn_10_collect`, `fn_20_build`, `fn_30_analysis`, `fn_40_posthoc`, `fn_trace`)

Computes: after the sniper -> exit wallet -> funder loop, whether separate operators converge into a common capital network, over 62 funders and collectors, 24 operators.

Works: `fn_trace.Fetch` reads its own cache, then the exit study's cache, then the network (`:46-82` in the printed block). `upstream_step` (`:124-143`) returns `status: "hub"` when more than `UP_PAGES` pages, `"empty"` when no signature, `"read"` otherwise; `guard` converts budget and RPC errors into recorded reasons (`:85-93`). `fn_40_posthoc.py:121-147` tests co-signing from `message.accountKeys[*].signer`, which is the correct field.

Defects: `fn_trace.funder_of` (`:96-109`) = largest net loser, fee added back only at index 0; no WSOL, no inner-instruction awareness (same weakness as `funding_of`). `history_before` ends on a short page (`:111-122`). `read_node` (`:145-183`) duplicates `ed_trace.read_node` with small differences (3 pages hard-coded). The "16 co-signing very active wallets" are not persisted by name (section 7).

### 2.18 `known_group_reentry/` and `post_detection_edge/`

No RPC. `known_group_reentry` (`kg_10_features`, `kg_20_outcomes`, `kg_30_analysis`) builds recognition features chronologically with an audit hook (`kg_10_features.py:28`), outcomes from the frozen price snapshot, logistic models and matched designs. `post_detection_edge` (`pde.py`, `trade.py`, `an_*`, `build_10_dataset.py`, `snap_*`) is the live-detection edge test with a sealed TEST block (`dataset_test.sealed.jsonl.gz`). Reusable: the statistics helpers in `pde.py` (`auc`, `fisher_greater`, `bh`, `holm`, `cluster_boot_*`, `:150-268`) and the cost model in `trade.py`. Nothing here helps the chain engine.

### 2.19 `alpha_patterns/` (33 scripts)

Exploratory pattern search of 5-7 October 2026, no network. `ap_lib.py` carries the frozen-block gating (`check_freeze` `:110`, `allowed_blocks` `:121`), `registre.py` the test registry, and `feat_20_history.py` causal 1 h track records (prior if `t_j + 60 <= t_i`, resolved only after `RESOLVE_1H = 3810 s`, header `:6-17`). Reusable: the look-ahead discipline and the registry pattern. It states "never a transitive closure" for its keys (`:19`). No chain code.

### 2.20 `tests/`

13 files, 95 tests passing. Relevant to chain code: `test_rpc_client.py` (raise rules, cooldown, `walk_sigs` cap), `test_lib_verif.py` (`first_signature` cap), `test_splitlib.py`, `test_ledger.py`, `test_a1_missing_signature.py`, `test_cache_preflight.py`. Missing: any test of `ed_trace.txflow`, `funder_of`, `fparse.parse`, versioned transactions with `loadedAddresses`, an empty mid-history page, a 429 inside a batch, or intra-slot ordering.

## 3. The seven failure modes, checked in code

### 3.1 Pagination and 429s

- Silent truncation without raising, still present:
  - `code/02_cn_outflows.py:67` page cap ends the loop; only a warning, no raise.
  - `code/02_cn_outflows.py:162` `kept[:max_tx]` silently cuts the window.
  - `code/03_split_detector.py:81` `max_pages=3`, no flag.
  - `code/06_hub_map.py:58` 30 pages, no completeness flag.
  - `code/v07_exit.py:41` 6 pages, no flag.
  - `code/a8_wallet_horde.py:88` 25 pages x 100, status stays `"ok"`.
  - `code/04_early_buyers_funding.py:102-106` warning only, then reads `sigs[:40]`.
- Correct (raises or carries a flag): `rpc_client.walk_sigs :190-194`; `lib_verif.first_signature :82-93` (`censored`); `col_10_windows` (raises after 50 pages, `:66-67` of the function); `09_bundle_snipe.oldest_sigs`/`measure` (status `pagination_incomplete`); `ed_trace`/`fn_trace` (explicit `hub`, `history not reached`, `H6` reasons).
- Empty page as genesis: `rpc_client.py:197-198`, `ed_trace.py:357`, `fn_trace.py` `history_before` (`len(p) < 1000`), `col_20_wallets.py:103`, `lib_verif.py:87-88`, `04_early_buyers_funding.py:83-89`. Only `data/trace_temoins/14_corrige_pages_vides.py` and `data/trace_*/lib_trace.py:124-131` (retry on `None`, but not on a lying `[]`) address it, partially.
- Per-element 429 in batches: no batch code in `rpc_client`, `frpc`, or the studies. The only JSON-RPC batch is `data/trace_h2w6/11_trace_h2w6.py:59-70` (`rpc_batch`): an element that came back as a JSON-RPC error object has no `"result"` key (`:69`), so it stays `None`; `get_txs` `:73-89` retries each hole once individually (`:82-85`) and, if that second call is also `None`, drops it silently (`:86-87`). The helper `rpc` (`:54-56`) returns `(out or {}).get("result")`, so an error response also becomes `None`. So a per-element 429 is treated as "missing" and then as "absent". The Helius batch-by-signature endpoint in `scan_gateway_dispatch.py:45-56` (`post_parsed`) raises on transport failure, but a per-transaction hole in the returned list is not checked in the lines read.

### 3.2 Transfer to an existing SPL token account (owner not cited)

Walking only the owner's signatures misses inflows of tokens (and of SOL kept as WSOL) that land in an existing token account, because the owner is not in the transaction's account list. Modules that walk only the owner address:
- `ed_trace.wallet_listing` (`:341`), `read_node` (`:489`), `fn_trace.read_node`, `col_20_wallets.prior/genesis`, `03`, `04.funding_events`, `05`, `a8`. For token receipts, `ed_trace` records `receipt_listed` and falls back to slots (`:402-406`), so the gap is visible in the data but not closed.
- `v07_exit.py` is the only code that walks a token account's own signatures (`sigs_all(ata)`, docstring `:7-9`), which does close it for the sell/transfer chain of one ATA.
- `fparse.py` and `09_bundle_snipe.py` walk the mint or the bonding curve, which does list every trade on that venue; a plain `transfer` (not `transferChecked`) between wallets does not name the mint, so it is not guaranteed to be in the mint's signature list (reasoned from the instruction layout, not run).
- Owner-level attribution inside one transaction is correct in `txflow` and `fparse` because they key by `owner` from `pre/postTokenBalances`.

### 3.3 Versioned transactions and `loadedAddresses`

- `maxSupportedTransactionVersion`: 0 in `rpc_client.py:213,218`, `lib_verif.py:65`, `expl_ledger.py:96`, `03:144`, `07_harvest_creations.py:63`, `01_ancrage.py`, `data/trace_*`; 1 in `col_10_windows.py:15,32,74`, `col_20_wallets.py` (`C.TX_VERSION`), `ed_trace.py:36,136`. The tests do not cover this.
- `loadedAddresses` appended to the static keys before indexing balances: `v07_exit.py:30-31,58-59`, `v04_slot_order.py:54`, `v05_creation_block.py:40`, `v06_curve_ladder.py:54`. Not done in: `02:101-104`, `03:95`, `04:111`, `05:123`, `expl_ledger.py:111-117`, `a8`, `fparse.py:83,111`, `ed_trace.py:154,171,174`, `fn_trace.funder_of :96-109`, `col_20_wallets.funding_of :109-119`, `11_trace_h2w6.deltas :123`. With `encoding: jsonParsed` the RPC returns the lookup-table accounts inside `accountKeys` (they carry `source: lookupTable`), in which case position indexing is right and the explicit concatenation in `v0x` is redundant. I did not run a live v0 transaction to confirm; no code asserts `len(accountKeys) == len(preBalances)`, so a mismatch would be silent (`11_trace_h2w6.deltas :127` guards with `if i < len(pre)`, which also hides it).

### 3.4 Inner instructions, WSOL wrap and close, ATA close, rent, "first System transfer"

- Inner instructions are walked in: `ed_trace._instructions :143-147`, `fparse._instructions :56-61`, `09_bundle_snipe._instructions :201-207`, `fn_trace` (via `T.txflow`).
- WSOL: `ed_trace.txflow` (`:176,200,204-207`), `fparse` (`:109,119,142-143`), `pool_of :186-190`. Nowhere else. `02`, `03`, `04`, `05`, `06`, `a8`, `expl_ledger`, `fn_trace.funder_of`, `col_20.funding_of` see lamports only.
- ATA close and rent refund: no explicit handling. `txflow` excludes accounts present in `pre/postTokenBalances` from the recipient candidates (`:198`) so a closed ATA's own balance is not mistaken for a destination; the refund to the owner lands in `dsol`. The rent minimum constant `0.00089088` exists only in `r1lib.py:68`. `fparse.curve_transfers :64-76` avoids counting the curve's creation rent.
- "First System transfer" as destination: not used by the current code. `ed_trace.py:189-194` states that a first version did and that it was wrong ("a one-transaction sweep through a fresh address and wrapped SOL"); the current rule is the largest net lamport gain among non-token accounts, with the WSOL-owner fallback. But `trade_out` (`:216-224`) still lists System transfers out of `w` inside a trade, kept apart and "not followed". Older `code/` modules use net deltas (02, 03, 04, 05, a8 mix: a8 and 06 use `nativeTransfers`, which are per-instruction transfers, so they are exposed to the disposable-address-plus-WSOL pattern).
- Net-delta limits: `txflow` picks one recipient (`:203`); a fee payer who is also the recipient is understated by the fee unless handled (`:196` handles it for the signer).

### 3.5 Double counting and floats

- Two sides of one transfer: `06_hub_map.py:73-82` and `a8:99-105` each count a transfer from the hub's side only (inflow when `dst == addr`, outflow when `src == addr`), so a hub's inflows and a funder's outflows are separate datasets, not summed; no explicit de-duplication by signature across the two sides anywhere. `expl_ledger` counts one transfer per transaction (`:279-281`). `02:113-118` can assign one recipient's gain to `addr` even when another sender paid it.
- Replays: the build reads the same cached `tx` and the same cached pages (`ed_trace.Fetch.page :104-107`), so a replay gives the same rows. `fn_trace.Fetch.page` reads the exit study cache first (`:14-18`), so the same page can enter two studies; branch keys are `(primary, path)`; no cross-study double count was checked.
- `cd`/`em` event counts: `em_table` has 13,233 `exits_full` records across the 1,657 rows (3,863 sell, 9,369 transfer, 1 create; counted with `jq`), a given sale is recorded once per sniper wallet.
- Floats as primary money values: `02:116`, `03:97`, `04:113`, `05:129`, `06:69`, `a8`, `expl_ledger.py:59,117`, `ed_trace.py:175,196` (`/ LAMPORTS` with `LAMPORTS = 1e9`, `:41`), `fn_trace.py:63`, `col_20_wallets.py:116`, `fparse.py:111`. Token amounts `uiAmount` floats: `ed_trace.py:172`, `fparse.py:53`, `v03..v07`. Integer lamports are used only inside `splitlib` inputs after conversion and for `buyers_of_tx` (`09 :219-220`, `lp` ints) and `fparse.curve_transfers :73`.

### 3.6 First activity treated as wallet creation; truncated history treated as complete

- Oldest signature = "creation / genesis" and its biggest net loser = "funder": `col_20_wallets.funding_of :109-129`, `fn_trace.upstream_step :124-143`, `ed_trace.prior_trace :444-475` (`:483` `chain[-1]`), `a8.naissance :65-83`, `04.funding_events :95-119`, `03.incoming_sol :90`.
  The first signature of an address is its first observed activity, which can be a dust transfer, an incoming token airdrop, or a later re-funding after a close, not its creation or its first SOL funding. Nothing checks that the oldest transaction actually credited lamports to the address before accepting the funder (`funder` is `None` when no account lost SOL, `col_20_wallets.py:120`).
- Honest handling to keep: the `hub` status when more than N pages (`ed_trace.py:478-479`, `col_20_wallets.genesis :132-165`, `fn_trace.upstream_step :88-89`) rather than guessing a genesis.
- Truncated treated as complete: see 3.1 list. Also `05` strategy `sample` is correctly flagged incomplete.
- `a9` and `a6` trust the upstream label "virgin" (`vierge`) and `genesis` fields of `data/split/all_buyers_g2y.json`.

### 3.7 Intra-slot ordering

- `getSignaturesForAddress` returns newest first, and within a slot the list is in reverse execution order. Code that reverses a newest-first list (`ed_trace.py:413,533`, `fn_trace.py:179`, `fn_10_collect.py:151,186`) gets forward execution order, including inside a slot, as long as the page boundary does not split the slot.
- Code that sorts by time and leaves ties in API order keeps same-second or same-slot items in reverse order: `fparse.py:209` (`sort` by `(slot, bt)`), `04_early_buyers_funding.py:41,92` (sort by `blockTime` only, then `[:40]`), `rpc_client`-based walkers sorted by `blockTime or 0` (`lib_trace.all_signatures` sorts by `(blockTime, signature)`, an arbitrary tie-break), `09_bundle_snipe.oldest_sigs :89` (sort by `(blockTime, slot)`, ties still reversed), `05_trace_origin.py:73,76`.
- Real execution order is read only in `v04_slot_order.py` (`getBlock`, block order) and recorded as `idx = t.get("transactionIndex")` in `ed_trace.py:161`; whether any consumer of `idx` exists was not traced (not verified). `fparse.py:21-22` says the order is unknown.
- Slot fallbacks that drop same-slot items: `ed_trace.py:406`, `:512`.

## 4. Reuse as is, and do not reuse

### 4.1 What the new engine can reuse as is

| Function / piece | File:line | Why it is correct |
|---|---|---|
| `rpc`, `_http_rotating`, error rule | `code/rpc_client.py:82-164` | Raise-never-None, bounded retry, key cooldown on 429; tested (`tests/test_rpc_client.py`). Keep the semantics; change what is listed in 4.2. |
| `walk_sigs` page cap raising | `code/rpc_client.py:177-209` (cap `:190-194`) | A page budget exhausted before genesis raises instead of truncating. Keep, after adding the empty-page confirmation and a genesis flag. |
| `frpc.rpc` | `post_detection_forensics/code/frpc.py:54-101` | Per-key pacing, 429 separated with doubling wait, raises. Better for long runs. |
| `cached()` atomic write | `code/rpc_client.py:246-262` | Temp file then `os.replace`. Do not cache `None`. |
| Budgeted `Fetch` with offline mode | `exit_destination/code/ed_trace.py:60-139` | Hard call cap, failure-share stop, null is an error, offline raises `NotCollected`, same code path online and offline. |
| Coverage-carrying listing | `ed_trace.py:341-392`, `:395-441`, `:444-486`, `:489-536` | Returns `reached_first`, `older_end`, `newer_complete`, `truncated`, `status` strings and hub status, so incomplete histories stay visible in data. |
| `txflow` net-flow rule | `ed_trace.py:150-225` | Net lamport delta, fee add-back, token accounts excluded, Jito tips excluded, WSOL netted, WSOL-owner fallback, co-signer list. Fixes the "first System transfer" defect. Needs the fixes in 4.2. |
| Co-signing test | `funder_network/code/fn_40_posthoc.py:121-134` | Reads `accountKeys[*].signer` for the destination; the right field for "recipient co-signs". |
| Honest hub status | `col_20_wallets.genesis :132-165`, `ed_trace.prior_trace :478-479`, `fn_trace.upstream_step :88-89` | An address with more than N pages is recorded as `hub` and not walked, never guessed. |
| `col_10_windows.window` | `post_detection_forensics/code/col_10_windows.py` (window function) | Cursor block, page loop that raises after 50 pages, raises on null transaction and on an empty creation slot. |
| `buyers_of_tx` | `code/09_bundle_snipe.py:210-230` | Sums System transfers and `createAccount` funding into the curve over inner instructions, per payer; right for co-signed bundles. |
| `fparse.parse` trade logic | `post_detection_forensics/code/fparse.py:79-171` | Trades from owner-level token deltas and venue SOL, not from instruction names; WSOL pool; Jito tips; router detection. Fix ordering and `uiAmount`. |
| `v04_slot_order` block enumeration | `code/v04_slot_order.py` | The only intra-slot order taken from `getBlock` in block order. |
| `expl_ledger.wallet_view` | `code/expl_ledger.py:102-125` | Own-balance delta of one wallet, failed transaction skipped, raises on missing blockTime; tested (`tests/test_ledger.py`). Valuation per transfer at its own-day close. |
| `a6` temporal rules | `code/a6_gateway_chains.py:105-120` | Gateway before distributor before buyer; payment after token creation dropped and counted separately. |
| `groupe_montant_max` | `code/a9_g2y_prelaunch.py:72-94` | Exact nine-decimal equality, no tolerance, deterministic tie-break. |
| `find_splits` | `code/splitlib.py:27-67` | Pure, deterministic, fuzz-tested. Use as a candidate generator, not as proof (limits in 2.7). |
| `em_lib.hop` / `MissingCacheError` | `economic_mechanics/code/em_lib.py:101-134` | An absent cache cannot pass for an empty history. |
| Permutation nulls and cluster bootstraps | `em_lib.py:286-360`, `post_detection_edge/code/pde.py:217-268`, `alpha_patterns/code/ap_lib.py:199-243` | Standard, deterministic seeds, tested pieces for the statistics layer. |
| Freeze / registry discipline | `alpha_patterns/code/ap_lib.py:110-130`, `registre.py` | Hash-checked frozen blocks and a test registry. |

### 4.2 What must not be reused, with the concrete defect

| Piece | File:line | Defect |
|---|---|---|
| `walk_sigs` as the only genesis test | `code/rpc_client.py:197-198,205-206` | One empty or short page ends the walk as genesis; Helius can return `[]` mid-history (documented in `data/trace_temoins/14_corrige_pages_vides.py:1-30`). No `genesis_reached` flag in the return value. Fix: confirm an empty page 3 times, return an explicit flag. |
| `walk_sigs` `until_ts` semantics | `rpc_client.py:207-208` | Returns the whole last page, so entries older than `until_ts` are included while the docstring says exclusive. |
| `tx()` returning `None` | `rpc_client.py:212-214` | A null transaction is not an error; 5 callers skip it silently (see 2.1). |
| `cached()` storing `None` | `rpc_client.py:257-261`, `lib_verif.py:62-64` | A null `getTransaction` is cached permanently. |
| `incoming_sol` | `code/03_split_detector.py:79-90` | Reads the 60 oldest of at most 3000 newest signatures as "initial funding", no genesis flag. |
| `funding_events` | `code/04_early_buyers_funding.py:101-106` | Reads `sigs[:40]` even when genesis was not reached; also sorts by `blockTime` only. Produced `data/split/all_buyers_g2y.json`. |
| `early_buyers` signer | `04_early_buyers_funding.py:61` | First signer only; multi-signer bundles are attributed to one wallet. |
| `signatures_in_window` + `kept[:max_tx]` | `code/02_cn_outflows.py:67,162` | Page cap and tx cap truncate without raising. |
| `outflows_of_tx` attribution | `02_cn_outflows.py:113-118` | Every account gaining 1 to 20 SOL is an outflow of `addr`, even when `addr` did not pay it. |
| `inflows` | `code/05_trace_origin.py:129-137` | Any account losing 1 SOL or more (pool vaults, routers) is a "source"; only three program ids excluded. |
| `sampled_signatures` | `05_trace_origin.py:86-106` | Thinned sample, always incomplete. Not a basis for an origin claim. |
| `etudie` / `naissance` | `code/a8_wallet_horde.py:85-118,65-83` | 2500-transaction cap with status `"ok"`; "birth" = oldest blockTime; `nativeTransfers` only. |
| hub map | `code/06_hub_map.py:58-83` | 3000-transaction cap without completeness flag; `nativeTransfers` only. |
| `sigs_all` | `code/v07_exit.py:39-48` | 6-page cap, no flag. |
| `funding_of` | `post_detection_forensics/code/col_20_wallets.py:109-129` | Funder = largest net loser of the oldest transaction, no check that the oldest transaction credited lamports, no WSOL. |
| `funder_of` | `funder_network/code/fn_trace.py:96-109` | Same rule; fee added back at index 0 only. |
| `helius_parsed` | `data/trace_*/lib_trace.py:215-236` | Returns `[]` with no key, on 404 and when retries fail. A silent empty. |
| `all_signatures` ending | `data/trace_*/lib_trace.py:137`, `data/trace_h2w6/11_trace_h2w6.py:105` | `if not pg: genesis = True` (retry covers only `None`). |
| `rpc_batch`, `get_txs` | `data/trace_h2w6/11_trace_h2w6.py:59-89` | A per-element error object is `None`; one individual retry; then silently absent. |
| sort-by-time with API tie order | `fparse.py:209`, `04:41,92`, `09:89` | Same-slot items stay in reverse execution order. |
| `uiAmount` token math | `ed_trace.py:172`, `fparse.py:53`, `v03..v07` | Float token amounts; use the raw integer `amount` and `decimals`. |
| `a7` session test | `code/a7_cross_token_links.py:83-97` | 6 h gap chaining and no base rate despite the header (`:17-19`). |
| `a9` reconciliation text | `code/a9_g2y_prelaunch.py:181-184,333` | Hard-coded conclusion text and 7.6 independent of the computed counters. |
| `m5_roundtrip` "LECTURE" block | `code/m5_roundtrip.py:379-399` | Numbers printed as constants. Keep only the simulation. |
| Six copies of `lib_trace.py` | `data/trace_*/lib_trace.py` | Four distinct md5 hashes among six copies. Do not import any of them. |
| Slot fallbacks | `ed_trace.py:406,512` | Drop or misplace same-slot transactions when the anchor signature is not listed. |

## 5. Present, partial, missing (summary against the new engine's needs)

Present and sound: raising client; budgeted fetch with offline replay; net-flow transaction reader with WSOL; co-signer detection; hub status as a recorded state; creation-window collector; temporal-order chain rules (a6); exact-equality group (a9); statistics and freeze tooling.

Partial: genesis detection (empty page problem, no confirmation); coverage flags (carried in `ed_trace`/`fn_trace` data, absent in older modules); versioned transactions (cap 0 in legacy modules, 1 in new, no `loadedAddresses` test); intra-slot order (only `v04`).

Missing: integer-lamport money type and integer token amounts end to end; a token-account-level history walk for inflows into existing ATAs (only `v07_exit` has one); multi-recipient sweep decomposition (one recipient per transaction); ATA close and rent refund as first-class events; WSOL wrap and unwrap as events; a batch fetch that treats a per-element error as a failure; a durable "first activity vs creation" model (first credit of lamports, account closure and re-creation); verification that `len(accountKeys) == len(balances)`; tests for any of the above.

## 6. The FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump case (token label `h2w6gm6jz`)

Mint: `FNqJtYs7rsP1H9GXWTtc5VnDoL2GhXEUKhYN46EEpump`. Creation: `2024-12-13T14:50:36.376000Z` (`data/split/all_buyers_g2y.json`, key `h2w6gm6jz`).

Where the nine wallets, the amount and the interval are described:
- `README.md:122-129`: "identical amounts, down to nine decimal places", `**9 wallets**`, `**2.976815600 SOL**`, `**343 seconds**`.
- `docs/PATTERN.md:144-171` (section 2.1, table of the nine wallets with times 07:07:49 to 07:13:32, "a 343-second interval", "Approximately 7.5 hours earlier"), `:178-200` (SAFFRON wallet `wbzkg9ftnVEMzeCL6wW8bpNTPDQWhBBnKo3JWJe3wh5` with the same amount on 2024-11-12), `:541-546`, `:723-729`, `:817`.
- `code/p1_readme_check.py:405-413` (README claim checks), `docs/out/p1_readme_check.json`.
- `code/a9_g2y_prelaunch.py:5-16,37-41` and its output `docs/out/a9_g2y_prelaunch.json` (`cas_reference`: `"montant_sol":2.9768156`, `"etendue_s":343`, `"n_portefeuilles":9`, delay 7.7131 h from first and 7.6178 h from last credit; `"autres_tokens_au_meme_montant":["SAFFRON"]`).
- `code/a7_cross_token_links.py` output `data/adverse/a7_cross_token_links.json`, `data/adverse/a6_gateway_chains.json`, `data/adverse/a5_author_pattern.json`, `data/adverse/a2_recount.json`.
- `docs/EXPLOITATION.md:230` (the trade row for `h2w6gm6jz`), `tests/test_splitlib.py:8-17,80` (the figure used as a fixture), `code/10_select_temoins.py:25-26,98`, `code/f_act_iv_timeline.py`, `entry_zone/tables/E1_singles.md`.

The nine wallets, as stored in `data/split/all_buyers_g2y.json` (key `h2w6gm6jz`, `portefeuilles[w].g2y[].{sol,ts,utc,avant_token}`), checked with `jq`; each has one credit of `2.9768156`:

| wallet | ts | utc |
|---|---:|---|
| `Csye9QE8LomP9RHzQAWLVh8XFdyNXvaopzrAuo3a1PoW` | 1734073669 | 2024-12-13 07:07:49 |
| `BmkuX6DaZUp9UCeR3XqAD6NjSpiFySnBvXyLT9uo7ZEA` | 1734073682 | 2024-12-13 07:08:02 |
| `AwQqcqdQQ3zydrtWMVF1PPDaWMNK7Lmhm3sUyDNGnSSY` | 1734073744 | 2024-12-13 07:09:04 |
| `3bBaA1MpQZuQpHjWZBEig12JB1W1TTQikxYPjUgGG3kU` | 1734073812 | 2024-12-13 07:10:12 |
| `CDvfNWiamAR1B84GUgttvDCGtiQE5dvJ49toF4fzsV5g` | 1734073831 | 2024-12-13 07:10:31 |
| `92w4K8uLg78KHWHxRovTDksLmou7MekcenY5PntPR34R` | 1734073853 | 2024-12-13 07:10:53 |
| `6QMshP9zwFXKbpLPh7w8EwadjA6vVasKAC7zu5HfMA22` | 1734073880 | 2024-12-13 07:11:20 |
| `BXuznwXTXt4QbLtLTkQnKNaXwdJ4PDXHvDcXf9DMogxe` | 1734073913 | 2024-12-13 07:11:53 |
| `5ibajLyeBmJhDfyZJN9FQsJBi48h8QSYg7eHGGhFjog6` | 1734074012 | 2024-12-13 07:13:32 |

`1734074012 - 1734073669 = 343` seconds, consistent with the docs. The amount is stored as `2.9768156` (a float), which is the same value as `2.976815600`.

The two collections that do not share wallets:

| | Collection A | Collection B |
|---|---|---|
| File | `data/split/all_buyers_g2y.json`, key `h2w6gm6jz` (produced by `code/04_early_buyers_funding.py`) | `data/trace_h2w6/e2_funding_h2w6gm6jz.json` (read by `code/a5_author_pattern.py:39`; produced by `data/trace_h2w6/11_trace_h2w6.py`) |
| Wallets | 10 in `portefeuilles` (9 credited before the token, 1 after: `n_vierges_finances_G2Y_avant_token: 9`, `..._apres_token: 1`); file also reports `n_acheteurs_distincts: 223`, `n_vierges: 67`, `n_illisibles: 90`, `n_tx_courbe: 451` | 40 wallets (`n_wallets: 40`), the first 40 early buyers in `data/trace_h2w6/e1_buyers_h2w6gm6jz.json` (40 buyers, 451 curve signatures); 905 inflows, 61 tagged `financement`; `n_genesis_reached: 21`, `n_genesis_NOT_reached: 19`, `n_prebuy_NOT_reached: 6` |
| Credits at 2.9768156 | 9 before creation | 0 (`n_inflows_au_montant_de_reference: 0`); closest amount `2.981490868` |
| Overlap | `n_portefeuilles_communs_avec_source_a: 0` (`docs/out/a9_g2y_prelaunch.json`) | same |

Also holding some of the nine wallets: `data/split/horde.json` (2 matching lines for `Csye9QE8`/`BmkuX6Da`) and `data/trace_h2w6/e6_courbe_acheteurs.json` (2 matching lines). Neither file proves which collection is complete (`a9_g2y_prelaunch.py:13-16`, `:290-291`). Note also the wording difference: `docs/PATTERN.md:150` says "approximately 7.5 hours", `a9` computes 7.71 h and 7.62 h, README says 7.6 h.

## 7. `funder_network/results.md`: high-activity co-signers

Section in `funder_network/results.md`: executive summary `:22-52` (bullets "These are not exchange deposits" `:28-32` and "One network or a service?" `:48-51`), `D. Network components` `:108-126` (post hoc table `:117-125`), `WHAT THE BLOCKCHAIN PROVES` `:255`, `WHAT THE NETWORK STRUCTURE STRONGLY SUGGESTS` `:269-276`, `WHAT REMAINS UNRESOLVED` `:278-288`, `NEXT MOST INFORMATIVE TEST` `:290-303`. "Very active" = "more than 3,000 earlier transactions, the plan's 'hub'" (`:22-24`).

Exact figures quoted from the text:
- "In 408 of 408 outgoing transfers, the receiving wallet signs the transaction" (`:28`); README table: "outgoing transfers co-signed by the recipient | 408 of 408".
- "64 % of the SOL the 62 wallets send out goes straight to very active wallets"; "32 % goes to wallets never seen in the corpus" (`:22-25`).
- "Hubs joining only through a direct transfer they co-signed as recipient: 106 such hubs, 16 shared by two operators or more; components [14, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; leaving one of these hubs out keeps 13 to 14 operators in the largest" (`tables/K_posthoc.md:35`, `results.md:121,124-125`).
- "The co-signing very active wallets link 14 of the 24 operators" (`:308`). "Measure who else the 16 co-signing very active wallets shared by two operators sign for" (`:292`).
- "12 very active wallets both create funders and receive their proceeds. 6 of them serve a single operator (for example 2DEEdv8H for c:9FJv: 4 funders created, 7,032 SOL received)" (`:44-46`).
- "recipient co-signs every step (1,280 sweeps, 408 outflows)" (`:239`); "14 of 24 joined through co-signing very active wallets (post hoc)" (`:245`).
- Destination-signs counts in `derived/FN_posthoc.json` key `destination_signs`: `hub / destination signs` 130, `hub / destination signs (fee payer)` 23, `other / destination signs` 238, `other / destination signs (fee payer)` 17.

Exact wallets:
- The 16 co-signing wallets are not listed by name anywhere. Only `cos` (the set of `(primary, hub)` pairs) is built in memory at `funder_network/code/fn_40_posthoc.py:121-134` from cached transactions, and only its sizes are exported (`out["components_cosigned_hubs"] = [14, 1, ...]`, `:147`). The cache it reads (`funder_network/data/cache/`, plus `exit_destination/data/cache/`) is untracked and not present in this worktree (`ls funder_network/data` fails).
- The 26 hubs touched by two operators or more (superset, from `derived/FN_posthoc.json` key `hubs`, 131 hubs in total; operators count per hub, first hub on each path; this is the "touched by two operators or more: 26" of `tables/K_posthoc.md:5`):
  `2DEEdv8Hx5hRzWonDAZ6ZfqcWNuycHv8RvYgEhJW7qfU` (2 ops, 9 primaries, 7058 SOL), `BfWSJADbWPxH3qYrTdZmtcs3t3NuuAcFYvvNZXEExQEo` (2, 4, 4199), `FK13gGS8yrvc75BP6VBRWbqhpQxReeWQShnhCvLVRQaJ` (2, 5, 2372), `5A8rJUX82sqxbmW5oSQNgSpPDKpZ3THjHKWqsUZzDcxM` (2, 2, 109), `A3xp8M8swEM4BX1P71n6sDvAnVc42V18UUWZiUkkGiKu` (3, 4, 78), `EAHyDdCg9SuQgsy13AZTZueBjaCSzvJpKzSENbiXMJ5A` (2, 3, 59), `4QnqW79Q4SECGd4vZ77yWCbRKB81ACL8n89U7o4DMHF2` (2, 2, 41), `35Lopfe9H87AbhA3kPsTtnoaDPw4xiEF1RrbUcNJPqKB` (2, 2, 38), `iGdFcQoyR2MwbXMHQskhmNsqddZ6rinsipHc4TNSdwu` (5, 6, 28), `5zEo97KwHHQ8My5uHQ1Ljn4rJh1AQ7BVFJapC2MyxdAC` (2, 3, 25), `8G83ekgmB6XRqUdvC5s5a24ayk7viNFysrki7xQKu94b` (2, 2, 19), and fifteen more with 0 to 6 SOL: `2PAeZu3mDy2PipAEZJdoWwxGnMZ7JAiB4AVTsBpfDi9a`, `2xv5WhEiG7Ce8Vodk1w3Rx8XyCwBEASebSVpGGvFkLJH`, `3FfXZyAVsYzVRaZWuzJvAFkYz5kYRcvJ3bG5KWsBwRH1`, `5VH2sWdKYZr6ou4ez6tRmjuUdnE1H1jDa757x589iGE7`, `5q1pBfE3eZRJctKdorEwFL8dZHe2H4d9kNQYanMqgh4K`, `5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9`, `6vvMpwpBd2t17jMdPrcN87HjdBDQ27jUu3fu6uEpFDUg`, `7R6X6y1cf1XpNJ6b3ESTRfn7A4tDwFuyZdJMt8EfvCfT`, `DFZaXcTj6bNF9e3NwECa6HevrUFGNUWQvSaYqfAGheND`, `EitseL4jgWuAsqY7xQ7H9HYouUFfZUERcS5EKamdYjb`, `Ek2M9VCNtQf4gmnK8Fg9bd5ZPb278pbeBQwRzRC2Dz5u`, `FRT9fNC4RisVDHAwtEUR83vsgFdV4J1e2y28LQKLEV6d`, `Ffq77wXpuWc5vg9bkfgoWcF6Sf3tkkfCJ5reepHSbtZS`, `GGCU7sYGLdrhH7EQv5JrjyvaJy594AA1QV1zU9hUBZik`, `jqd63a5wxbGey2VodyodKXeDLKbsLiH4VBL3ioZAx87`. The 16 co-signing ones are a subset of the 106 co-signed hubs, not necessarily of these 26 (not verified).
  `5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9` is the address labelled "Binance hot wallet" in `data/trace_h2w6/lib_trace.py:KNOWN` and "echange (hot wallet)" in `code/05_trace_origin.py:52`.
- Bridge and treasury wallets named by prefix only in the text: `27NsskNe`, `AyBdrsDJ`, `DRUKt6L9`, `2DEEdv8H`, `8zHcWujH`, `D6HE3knc`, `H9tyeSef`, `7a2zhDAJ` (`results.md:100-101,108-125`, `tables/K_posthoc.md` section 3). Full addresses are in `derived/FN_posthoc.json` (`links[*].wallet`, 44 link records) and `derived/fn_table.json.gz`.

Derived data files that hold the transactions (all in `funder_network/derived/`):

| File | Rows / content |
|---|---|
| `fn_table.json.gz` | object with `downs` 409 rows (`direction, measured, origin, path, primary, side, terminal`), `ups` 55 rows (`direction, measured, path, primary, terminal`), `primary` 62 wallets (`kind, labels, operators, sample, upstream_start, wallet`), `reads` 62 keys holding 1058 read-transaction records in total (`anchor, bt, class, dsol, dtok, dws, err, idx, inn, origin, out, out_gain, post_tok, sig, signer, signers, slot, tok_to, trade_out, venue`), `calls` and `stopped` (`gzip -dc | jq`) |
| `inventory.json` | `population` 62 addresses, `calls {calls: 62, fails: 0}`, `test_start 1790680980` |
| `FN_posthoc.json` | 2453 lines; keys `components`, `components_cosigned_hubs`, `components_with_hubs`, `destination_signs`, `hub_leave_one_out` (26 entries), `hubs` (131), `links` (44), `sequences` (13), `two_way_hubs` (12) |
| `FN_results.json` | keys `B` to `H`, `coverage` |

The raw transactions behind these tables (`funder_network/data/cache/`, `exit_destination/data/cache/`) are untracked and not in this worktree; `fn_table.json.gz` `reads[*]` is the only tracked transaction-level record (1,058 flow records, not raw transactions).

## 8. Tables linking groups to sells and destinations

`economic_mechanics/derived/em_table.jsonl.gz` (1,657 rows, one per launch; `gzip -dc | wc -l`): top-level keys `actor, cluster, creator, ctl, deployer_recent, early, migrated_slot0, migration_slot, mint, slot0, slot0_sol, slot0_states, snipers, split, t, t_create, utc`. `cluster` is the group id (union-find over launches, `em_lib.clusters`), `snipers` the group members. Each `snipers[*]` has `between, bt, exits, exits_full, gen_bt, gen_funder, gen_funder_hub, gen_received, last_amount, last_bt, last_funder, last_funder_hub, last_sig, n_prior, role, sigs, slot, source, ticket, tok_bought, wallet`. `exits_full[*]` = `{bt, kind, post_sol, recipients, sig, slot, sol_in, tok_out}`: 13,233 records over the whole file (3,863 `sell`, 9,369 `transfer`, 1 `create`; counted with `jq`). This is the table that links a group (cluster -> snipers) to its sells and to the owners receiving transferred tokens (`recipients`).

`economic_mechanics/derived/em_price.jsonl.gz`: 1,657 rows, keys `mint, p0, series, t, t_create, window` (price series per launch).

`coordination_detection/derived/cd_table.jsonl.gz`: 1,657 rows, keys `actor, cluster, creator, ctl, early, migrated_slot0, mint, slot0, snipers, split, t, t_create, utc` (no exits).

`exit_destination/derived/ed_table.json.gz` (object, not JSONL): `wallets` 300 (each `events, listing, listing_error, wallet`; 1,457 events with `held_end, max_held, mint, n_window, n_window_ok, reads, receipt_listed, status, truncated, wallet`; 7,925 flow records in `reads`), `branches` 1,280 (keys `after_sale, measured, mint, path, pooled, reason, side, terminal, wallet`; `path[1]` has `bt, sig, slot, sol, wallet`), `prior` 300 (`genesis, reads, wallet`), `calls`, `stopped`. Branch terminals counted with `jq`: H1 631, H2 7, H5 300, H6 342. `derived/selection.json`: `events` 3,963, `population` 1,737, `selected` 300. The group-to-destination link is `ed_table.branches[*].path[-1]` classified H1..H6 by `ed_trace.Roles.classify` (`:307-320`) and `proceeds_cat` (`:322-334`).

`known_group_reentry/derived/kg_features.jsonl.gz` (1,657 rows; keys `G1, G2, G2_strict, G3, G4, depth, f, fine, has_series, history_latest_t, mint, n_snipers_em, one_funder_2plus, operator, p0, prior_group_launches, recency, since_group_s, sniper_prior_max, snipers_seen, split, stability, t`) and `kg_outcomes.jsonl.gz` (1,657 rows; keys `L0, L15, L30, L5, has_series, mint`) link groups to outcomes but not to destinations.

## 9. Not verified

- No code was run. No behaviour was confirmed against a live RPC response: version-1 transaction handling, whether jsonParsed `accountKeys` already includes lookup-table addresses (section 3.3), whether the Helius enhanced API returns failed transactions or lists inner transfers separately (2.6), whether `getTokenLargestAccounts` is capped at 20 (2.4).
- `idx = transactionIndex` (`ed_trace.py:161`): whether any downstream code uses it for ordering was not traced.
- The identity of the 16 co-signing wallets: not listed in any tracked file; not recomputed (needs the untracked cache).
- Whether the 26 hubs of section 7 contain the 16 co-signers: not verified.
- Files not read in full: `ed_20_build.py`, `ed_30_analysis.py`, `ed_40_posthoc.py`, `em_10_build.py`, `em_20_analysis.py`, `em_30_extra.py`, `cd_10_build.py`, `cd_20_analysis.py`, `fn_10_collect.py`, `fn_20_build.py`, `fn_30_analysis.py`, `kg_*`, `an_*`, the 33 `alpha_patterns` scripts beyond `feat_20_history.py` and `ap_lib.py` signatures, `01_ancrage.py`, `a1` to `a5`, `a8` beyond the pagination part, `scan_gateway_dispatch.py` beyond the transport. Statements about these rely on their README/docstrings and the function list.
- `data/trace_*` `lib_trace.py` contents were read for `trace_h2w6` only; the other five copies were only hashed.
- Forbidden files (`.env`, `.helius_keys`, `identity.txt`, `redact_salt.txt`, `docs/INVENTAIRE.md`, `docs/REVIEW.md`) were not opened.
- Row counts for `jsonl.gz` files come from `gzip -dc | wc -l`; JSON structures from `jq` on keys and lengths only.
