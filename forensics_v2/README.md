# forensics_v2

A wallet-level tracing engine for Solana, next to the published study and separate from it. The README at the root and
everything outside this folder stay as published.

Every movement is an exact integer and points to a signature. Every path says where and why it stops. Evidence levels are
explicit: `ONCHAIN_VERIFIED`, `STRONG_TECHNICAL_INFERENCE`, `STATISTICAL_ASSOCIATION`, `EXPLORATORY_HYPOTHESIS`,
`UNRESOLVED`, `REFUTED`. Nothing merges wallets into one owner.

## Use

```bash
python -m forensics_v2 trace <wallet> --direction both --hops 2 --credits 2000   # report.md and graph.json
python -m forensics_v2 tx <signature>                                            # one decoded transaction
python -m pytest forensics_v2/tests -q
```

Configuration lives outside the repository, in `~/.config/forensics_v2/`: `config.json` (`data_root`, `credit_ceiling`,
`read_caches`) and `helius_sources.json` (files to read keys from and allowed fingerprints, no key value). The core needs
only the standard library; `store.py` needs DuckDB (`requirements.txt`).

## Parts

| File | Does |
|---|---|
| `decode.py` | Raw transaction to transfers, owner nets, residuals and edges, in lamports and raw token units |
| `rpc.py`, `keys.py` | Bounded client: credit ceiling, resumable history, no key in any log |
| `trace.py` | Multi-hop graph, round trips, coverage of each wallet |
| `store.py` | DuckDB tables; a replay adds nothing; `reconcile` re-checks the books |
| `storage.py` | Refuses to write if the external volume is missing |
| `investigations/` | The studies below |
| `private_trades/` | The author's own wallets and trades. Git-ignored, mode 700 |

## Results and documents

| Document | Status |
|---|---|
| [docs/BASELINE_AUDIT.md](docs/BASELINE_AUDIT.md) | Existing code: what to reuse, defects with lines |
| [docs/EXTERNAL_REPOS_AUDIT.md](docs/EXTERNAL_REPOS_AUDIT.md) | 15 repositories read: integrate, adapt or reject |
| [docs/baseline/](docs/baseline/) | Test state before any change |
| [reports/nine_wallets/README.md](reports/nine_wallets/README.md) | The published case, rebuilt from signatures |
| [reports/gateway_bursts/README.md](reports/gateway_bursts/README.md) | Do same-amount bursts behave as groups? Plan: [docs/PLAN_gateway_bursts.md](docs/PLAN_gateway_bursts.md) |
| [reports/cosigners/README.md](reports/cosigners/README.md) | Very active co-signers: not settled. Plan: [docs/PLAN_cosigners.md](docs/PLAN_cosigners.md) |
| [docs/PLAN_trade_context.md](docs/PLAN_trade_context.md) | The author's own trades against his description. Results stay private |

State of the work: [PROJECT_STATE.md](PROJECT_STATE.md), [TODO.md](TODO.md), [DECISIONS.md](DECISIONS.md), [BLOCKERS.md](BLOCKERS.md).
