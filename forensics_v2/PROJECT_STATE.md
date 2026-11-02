# State of the work

Checkpoint: 2026-11-02, session running. Rewritten at each step; history is in `git log` and in the project journal.

## Done and checked

- Engine: decoder, client, tracer, store, volume guard, with tests. 95 repository tests plus the new ones pass. The trip builder
  matches the frozen 2024 table to the lamport. Same convention and data,
  separate code: this validates the implementation, it is not independent evidence about the trades.
- Baseline recorded before any change (`docs/baseline/`). External repositories read (`docs/EXTERNAL_REPOS_AUDIT.md`).
- Published case rebuilt from signatures: 15 wallets, not 9 (`reports/nine_wallets/`, report to finish).
- Plans committed before results: `docs/PLAN_gateway_bursts.md`, `docs/PLAN_cosigners.md`.

## In progress

See TODO.md. Long jobs are logged in the session scratchpad, and they resume from `checkpoints/` when run again.

## Where the data is

- Work area: `~/.local/state/forensics_v2/hot` on the internal disk, capped at 1.5 GB by `internal_quota_bytes`, with a floor at
  the machine's 13.5 GB. Past either limit the cache continues on the external volume by itself.
- External volume: `/Volumes/PHI-Data/solana_forensics_v2` (folders `rpc_raw`, `checkpoints`, `intermediate`, `tooling`, ...).
- To copy the work area out, once the external disk is free enough: `python -m forensics_v2.investigations.sync_cold`.
- Private results: `forensics_v2/private_trades/`, git-ignored, mode 700.

## Resume

```bash
cd ~/Documents/Crypto/WSMO-forensics-v2
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY -m pytest forensics_v2/tests -q
$PY -m forensics_v2.investigations.gateway_bursts analyse
$PY -m forensics_v2.investigations.cosigners collect 10600   # resumes from its checkpoints
$PY -m forensics_v2.investigations.cosigners analyse
$PY -m forensics_v2.investigations.card_scan 8000 <targets.json>
```

The core runs on the standard library with that Python. `store.py` needs DuckDB, from the venv in
`/Volumes/PHI-Data/solana_forensics_v2/tooling/venv` (slow to start while the disk is busy).
