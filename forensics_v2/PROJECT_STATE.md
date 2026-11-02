# State of the work

Checkpoint: 2026-11-02. Rewritten at each step; history is in `git log` and in the project journal.

## Done and checked

- **Engine:** decoder, client, tracer, DuckDB store, volume guard, with tests. The trip builder matches the frozen 2024 table to the lamport.
  Same convention and same data, separate code: this validates the implementation, it is not independent evidence about the trades.
- **Baseline** recorded before any change (`docs/baseline/`). **External repositories** read (`docs/EXTERNAL_REPOS_AUDIT.md`).
- **Published case** rebuilt from signatures, including its own day at the gateway: 15 wallets, not 9 (`reports/nine_wallets/`).
- **Gateway bursts** and **co-signers**: plans committed before results, reports written (`reports/gateway_bursts/`, `reports/cosigners/`).
- **The author's own trades:** private deliverables built, launch context read, comparison group read. Only in `private_trades/`, git-ignored.
- **Independent review** of the new code by a silent-failure agent; findings checked on the data, in `DECISIONS.md` 13d.

## Not done

See TODO.md. Not started: the cross-chain module, launch context of Raydium entries, tracing the fleet's other tokens and the common wallet further.

## Where the data is

- Work area: `~/.local/state/forensics_v2/hot` on the internal disk, under `internal_quota_bytes` and above the machine's 13.5 GB floor. Past either limit
  the cache continues on the external volume by itself, slower while other sessions use that disk.
- External volume: `/Volumes/PHI-Data/solana_forensics_v2`. It is a mechanical USB disk (image on `VERBATIM HD`), not an SSD.
- To copy the work area out, adding only: `python -m forensics_v2.investigations.sync_cold`.
- Private results: `forensics_v2/private_trades/`, git-ignored, mode 700. Start with `PATTERN_REPORT.md`, `PNL_RECONSTRUCTION.md`, `UNRESOLVED_TRADES.md`.

## Resume

```bash
cd ~/Documents/Crypto/WSMO-forensics-v2
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY -m pytest -q
$PY -m forensics_v2 trace <wallet> --direction both --hops 2 --credits 2000
$PY -m forensics_v2.investigations.trades_2024 build
$PY -m forensics_v2.investigations.trade_context analyse
$PY -m forensics_v2.investigations.trade_context analyse_control
$PY -m forensics_v2.investigations.card_scan 8000 <targets.json>     # resumes; symx and h2w6gm6jz stopped at 25,000 transactions
```

Everything resumes from `checkpoints/`. The core runs on the standard library with that Python. `store.py` needs DuckDB, from the venv in
`/Volumes/PHI-Data/solana_forensics_v2/tooling/venv`, slow to start while the disk is busy.
