# Plan, written before any new on-chain or X data was read

Date: 2026-11-03. This file is committed before the first network call of this investigation. Changes after
that point go in `AMENDMENTS.md`, dated, with the reason. Earlier notes of the author (`ansem_enquete`, August 2026)
were read before this plan, so nothing here is blind to them; they are treated as claims to re-measure.

## Question

H1: Ansem (`@blknoiz06`) organised, directly or indirectly, several coordinated launches.

Competing explanations, each of which must be allowed to win:

- H0a: the launch of `9cRCn9rG...pump` was done by operators unrelated to him, who used his name, and he adopted the token later.
- H0b: a professional bundle-snipe operator runs many launches, ANSEM being one of them, with no link to him.
- H0c: several independent operators use the same tools and the same services, which creates links that mean nothing.

## Evidence ladder

Every conclusion is placed on one rung. A rung does not imply the rung above it.

| Rung | Name | What it takes |
|---|---|---|
| R1 | Same technical method | Same mechanics in the creation slot (share of supply, SOL amount, Jito use). Pump.fun's curve produces about 85 SOL and 79 % by itself, so this rung alone carries no weight. |
| R2 | Same infrastructure | A non-service address, program config or lookup table reused across launches. Shared bots are for sale: this does not show a shared owner. |
| R3 | Same financial network | Direct, non-service transfers of SOL or tokens that connect the wallets of two launches, each with a signature. |
| R4 | Probable same operator | R3 plus capital that returns to a common controller or is recycled from one launch into the next, with amounts and timing that match, in at least two launches, and a rarity test that rejects chance. |
| R5 | Personal attribution | A wallet he publicly claims, or a primary source that ties him to it (his own post, a filing, an exchange record), linked on chain to a launch wallet by R3 or better, before the token's public adoption. |

A token received after launch, an airdrop, a promotion, a shared exchange, or a shared funder at a service is not R5.

## What does not count as a link

An address stops being a link, and tracing ends there with the reason written, when it is any of these:

- a program, a pool, a bonding curve, a program-derived fee vault, a Jito tip account;
- an address named by a public source as an exchange, bridge or swap service;
- an address whose own history shows service behaviour: at least 500 distinct counterparties in a sample of 1,000 transactions, read before use;
- a transfer under 0.01 SOL, which is dust or a fee refund, unless the same pair repeats at least three times.

Funder = the account that loses the SOL, never the fee payer (`ansem_enquete/ELVENGARDEN.md`, section 1).
Destination = the largest net lamport gain in the transaction, tips excluded, not the first transfer.

## Rarity test

Seeds: wallets directly involved in the creation slot of ANSEM, and those that received tokens from them
within the first hour. Fixed after step 1, before step 2 reads other launches.

Population: every creation-slot buyer list available without new credits (`data/floor_capture_public.jsonl.gz`,
`data/v05_creation_block.json`, the detector's alerts, `ansem_enquete/data/snipers90.json`), plus launches found by
walking the seeds.

Statistic: for each pair of launches sharing a seed wallet, is the sharing more frequent than chance? Null: launches
keep their number of slots and each wallet keeps its number of launches, wallets are reassigned at random. Permutation
with 10,000 draws, p reported with its Monte Carlo error. Comparison group: all other wallets of the same corpus with
the same number of launches, plus or minus 20 %. The seed wallets are one group among those: if they look like the rest,
they carry no special signal.

Positive control before reading the seeds' result: the same test must flag a planted pair of wallets that always appear
together, and must stay quiet on shuffled data.

## Budget and storage

- Helius research pool only (`~/.config/forensics_v2/helius_sources.json`). Never the keys of `~/Downloads/.env`.
- Ceiling for this work: 150,000 credits, own counter. Reported in `RUN_MANIFEST.json`. Raised only by an amendment.
- Internal disk under `~/.local/state/ansem_network`, quota 1.5 GB, overflow to `/Volumes/VERBATIM HD/ansem_network`.
  The volume is a mechanical USB disk, so it takes one database file, never many small files.
- Every long computation runs in a stream with a memory watchdog.

## Publication

The branch `ansem-network` is public. Only verified, signature-backed findings go on it. No statement that a named
person did something unless it is on rung R5. No wallet of the author. Frozen results of the repository are never rewritten.
