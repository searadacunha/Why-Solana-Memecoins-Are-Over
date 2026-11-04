# Cross-chain movements: what can be proved, and what was found

Code: `forensics_v2/crosschain.py`, tests on a real public transaction in `tests/test_crosschain.py`. Public endpoints, no key, no credit.

**A bridge leaves a proof that can be checked from both ends, and the code now does so. Across everything read for this project, bridges are almost absent: 6 transactions out of 162,342, none of them leaving through Wormhole. This does not show the capital stays on Solana: a custodial swap leaves no such link.**

## Levels of proof

| Level | Rests on |
|---|---|
| Bridge program in the transaction | The raw transaction. `ONCHAIN_VERIFIED` |
| Identity of the message | The sequence in the transaction's own logs, the emitter in its accounts, and both in the signed VAA, parsed from its bytes. `ONCHAIN_VERIFIED` |
| What the indexer says about recipient and amount | Wormholescan alone. `INDEXER_REPORTED` |
| Arrival | The destination chain's own node: the receipt, status success, and the contract called. `ONCHAIN_VERIFIED` |
| Guardian signatures | Counted, not recovered: that needs keccak and the guardian set. **Not done** |

## Validation on a real transaction

`3idaoHHC…`, 2024-12-13, through Wormhole's token bridge:

| Check | Result |
|---|---|
| Programs in the transaction | Wormhole core, token bridge, Mayan forwarder |
| Sequence 1079478 in its logs, emitter `ec737299…` in its accounts | Yes |
| VAA parsed from bytes gives the same chain, emitter and sequence | Yes, 13 signatures |
| Arrival on Ethereum, `0x17c585d0…` | Receipt status success, block 21397032, contract `0x8e687c6a…`, read from a public node |

Changing the sequence or the emitter in the test makes the first proof fall back to `INDEXER_REPORTED`. A second transaction, `jMxUewpJ…` (Mayan Swift), is proved at source and has no arrival known to the indexer, and it is reported as `NOT_FOUND`, not as a failure.

## What the scan found

| Corpus | Transactions | Bridge program seen |
|---|---:|---|
| Frozen 2024 cache, text search on raw files | 155,649 | 5 deBridge arrivals from one solver, 1 CCTP |
| 2026 exit wallets ([exits_2026](../exits_2026/README.md)) | 6,693 | None |

The 8 program ids searched are in `crosschain.py`, from each project's documentation. A bridge not on that list is not seen. The Relay protocol pays through solvers with no program of its own, and its API `requests/v2` is announced as retired on 2026-11-24 while `v3` needs a key, so it has no module here.

## Not provable from here

- **A custodial swap,** ChangeNOW for instance. Its books are off chain, so its input and output cannot be linked by this code.
- **An exchange.** A deposit and a later withdrawal on another chain have no common identifier.
- **Who controls either end** of a bridge transfer.
