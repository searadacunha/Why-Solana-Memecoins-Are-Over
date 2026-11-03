# investigations/ansem_network

An on-chain and public-source investigation of the ANSEM token: was the launch organised by Ansem or by a network tied to him?

**Short answer: not supported by the evidence, and not disproved, because chain data cannot see a private agreement.** The launch comes from a serial deployer that gave his newly published wallet most of the supply, repeated this on many launches, and has no traced money going back. Start with [REPORT.md](REPORT.md). The report names no one as responsible for anything beyond what the chain and their own posts show.

Nothing outside this folder was changed. The root README and the frozen studies are as published. Proposed corrections are in [PROVENANCE.md](PROVENANCE.md).

## Check it

Offline, from the repository root:

```bash
python investigations/ansem_network/code/check_ledger.py          # 71 checks against saved raw data
python -m pytest investigations/ansem_network/tests -q
```

Rebuilding from the chain needs a Helius key pool (`forensics_v2/keys.py`). Scripts run in this order, all resuming from checkpoints: `col_01`, `col_02`, `col_03`, `col_04`, `col_05`, `col_06`, `col_07`, `col_08`, `col_10`, `col_11`, then `ana_10`, `ana_11`, `ana_12`, `ana_20`, `ana_30`, `ana_31`, `ana_40`, `ana_50`, `ana_60`, `build_ledger`. Working data stays outside the repository. `evidence/raw/` holds the transactions the ledger cites.
