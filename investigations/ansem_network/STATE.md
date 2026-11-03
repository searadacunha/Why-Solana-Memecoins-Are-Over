# State of the investigation (resume here)

Checkpoint: 2026-11-03. Branch `ansem-network`, worktree `~/Documents/Crypto/WSMO-ansem-network`. Python: `~/.local/share/forensics_v2/venv/bin/python`.
Work area `~/.local/state/ansem_network` (rows, checkpoints, tx.sqlite). All collectors resume from their checkpoints.
Credits: read `~/.local/state/ansem_network/checkpoints/credits`, ceiling 150,000 (`code/lib.py`).

## Measured so far, each with its evidence file

- Creation slot rebuilt from the raw block: `evidence/creation_slot.json`, `evidence/raw/creation_slot_txs.json.gz`.
- Deployer table: `evidence/deployer_tokens.csv`, `evidence/deployer_recipients.csv` (`code/ana_10_deployer.py`).
- X posts by ID with hash: `evidence/x_posts.jsonl` (`code/col_10_x_posts.py`).

## Still to do

See the task order in `PLAN.md` and the open items at the end of `REPORT.md` once written.
