# Plan: co-signers, second test, on those who actually pay

Written before this reading. The first test ([PLAN_cosigners.md](PLAN_cosigners.md)) counted distinct other signers and turned out to count disposable keys: 16 of 25 controls got the
same label. This test uses the same 131 wallets and the same eight windows, already read, so it costs no credit. Only their transactions are read again, with no price or outcome file.

## Measures, per wallet

A **payer** sends SOL to the wallet. A **persistent payer** does so on at least two of the eight days.

- **M1:** number of persistent payers.
- **M2:** share of the SOL received that comes from persistent payers.
- **M3:** share of its persistent payers that also pay another wallet of the set.
- **M4:** share of the SOL received from known operator wallets of the frozen tables.
- **M5:** share of the SOL received from its five largest payers.

## Verdicts, fixed here

- **Looks like a service for many clients:** M1 at least 20, and M4 under 10 %, and M5 under 60 %.
- **Looks private to a few parties:** M5 at least 80 %, or M4 at least 50 %.
- **Not separated:** anything else. **No payer:** nothing received in the windows.

Co-signers against controls: permutation of labels on M1 to M5, 10,000 draws, seed 20261103, Bonferroni over 5. The verdicts count only if controls do not get the same label at the same
rate: Fisher on "service" share, co-signers against controls, p under 0.05. Otherwise this test does not discriminate either, and the report says so.

## Limits, written before

Eight days of first transactions per wallet. A persistent payer may be one operator's wallet, an unknown one, or a client: payment alone cannot tell them apart. No label here identifies anyone.
