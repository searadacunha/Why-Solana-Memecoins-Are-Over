# State of the work

Checkpoint: 2026-11-03, second session of the day. Rewritten at each step; history is in `git log` and in the project journal.

## Done and checked

- **Engine:** decoder, client, tracer, DuckDB store, volume guard, with tests. The trip builder matches the frozen 2024 table to the lamport.
  Same convention and same data, separate code: this validates the implementation, it is not independent evidence about the trades.
- **Branch history:** rewritten once on the author's written permission, `DECISIONS.md` 16. CI green on the rewritten tip.
- **Environment:** isolated Python 3.13 (see Resume). Existing and new tests run from it, in a fresh clone, with the artefacts unchanged byte for byte.
- **Published case:** nine against fifteen reconciled, each credit read from two sources: the nine are all inside the fifteen (`reports/nine_wallets/`). The README gains one sentence, none changed.
- **The author's own trades:** rebuilt as a ledger of every transaction, with a capital statement that closes to the lamport and a balance chain showing the ledger is complete for its wallets.
  Tips paid in their own transaction are attached to their trade. PnL cards are matched by token symbol, wallets get a level from a rule fixed in advance. Everything is in `private_trades/`, git-ignored.
- **Cross-chain module:** three levels of proof, tested on a real transaction from Solana to Ethereum (`crosschain.py`, `reports/cross_chain/`).
- **2026 exits through the new engine:** 427 of 427 transactions agree with the frozen tables after one stated convention, and the engine recovers what their cap hid (`reports/exits_2026/`).
- **Fleet of the published case:** deployers of its nine tokens read, none in the fleet, two funding chains among them (`reports/nine_wallets/`).
- **Co-signers, second test:** on paying wallets, plan fixed first, no credit spent (`reports/cosigners_v2/`).
- **Gateway bursts, first co-signer test, baseline, external repositories:** as reported on 2026-11-02.

## Not done

See `TODO.md`. Next, in this order: search local files for the 24 undetermined wallets and the last card, fix a matched control for the signal rate before reading it, then the fleet against ordinary gateway traffic, `AwzntLka…` and the 8 strict bursts, each only if it can separate one operator, a coordinated group and a shared service.

## Where the data is

- Work area of the last runs: `~/.local/state/forensics_v2/hot`, internal disk, 1.5 GB quota, reserved through the disk guard (`DECISIONS.md` 18).
- Everything else, and copies of the work area and private results: `/Volumes/PHI-Data/solana_forensics_v2`, a disk image on the mechanical USB disk `VERBATIM HD`.
- Private results: `forensics_v2/private_trades/`, git-ignored, mode 700, copied to `private_reports/` on that volume. Start with `RAPPORT_TRADES_2024_V2.md`.

## Resume

Run from the repository, never from the home folder, and not with the machine's default `python3`, which is 3.14 inside another tool's environment.

```bash
cd ~/Documents/Crypto/WSMO-forensics-v2                    # branch forensics-v2
uv venv --python 3.13 ~/.local/share/forensics_v2/venv     # once
uv pip install --python ~/.local/share/forensics_v2/venv/bin/python duckdb==2.0.0 pytest==9.2.0 mypy ruff   # once
PY=~/.local/share/forensics_v2/venv/bin/python
$PY -m pytest -q                                           # existing tests and V2
$PY code/run_all.py --strict                               # rewrites artefacts to compare them: run it in a fresh clone
$PY -m forensics_v2.investigations.trades_ledger extract   # private, no network
$PY -m forensics_v2.investigations.trades_report           # private, no network
$PY -m forensics_v2.crosschain prove <signature>           # public endpoints, no key
$PY -m forensics_v2 trace <wallet> --direction both --hops 2 --credits 2000
```

Everything that reads the network resumes from `checkpoints/`. `sync_cold` copies the work area to the volume, adding only.
