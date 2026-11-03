# investigations/ansem_network

An on-chain and public-source investigation of the ANSEM token: was the launch organised by Ansem or by a network tied to him?

**Short answer: no on-chain or public evidence found here ties Ansem to organising it. This does not clear him: chain data cannot see a private agreement, and some facts stay unexplained.** The launch comes from a serial deployer that gave his newly published wallet most of the supply and went on sending him tokens, and no SOL moves directly between that deployer's group and the wallets tied to him. Start with [REPORT.md](REPORT.md).

Nothing outside this folder was changed. The root README and the frozen studies are as published. Proposed corrections are in [PROVENANCE.md](PROVENANCE.md).

## Check it

Offline, from the repository root:

```bash
python investigations/ansem_network/code/check_ledger.py          # checks against saved raw data
python -m pytest investigations/ansem_network/tests -q
```

Rebuilding from the chain needs a Helius key pool (`forensics_v2/keys.py`). Scripts run in this order, all resuming from checkpoints: `col_01`, `col_02`, `col_03`, `col_04`, `col_05`, `col_06`, `col_07`, `col_08`, `col_10`, `col_11`, then `ana_10`, `ana_11`, `ana_12`, `ana_20`, `ana_30`, `ana_31`, `ana_32`, `ana_33`, `ana_40`, `ana_50`, `ana_60`, `build_ledger`. Working data stays outside the repository. `evidence/raw/` holds the transactions the ledger cites.
