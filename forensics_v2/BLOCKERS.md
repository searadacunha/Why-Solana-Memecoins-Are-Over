# Blockers and decisions left to the author

None of these stops the work in progress. Each says what is needed.

1. **Helius accounts.** Eleven keys answer. Whether they sit on one account or several is not visible from a key, and neither
   is the plan or the credits left. Helius's terms on several free accounts were not found in its public documentation pages.
   Decision: look at the dashboard or the terms, and say whether the pool of five may be used as it is.
2. **Paid plan risk.** If one of these keys is on a paid plan with autoscaling, spending past its monthly credits could bill.
   The ceilings make that unlikely, not impossible. To check on the dashboard.
3. **Key rotation.** To review on the dashboard.
4. **The external disk is mechanical.** Several sessions at once saturate it (processes in disk wait, one `touch` over 90 s).
   Heavy collection here competes with PolySentinel's backups and restore tests. A real SSD would remove this limit.
5. **Publication of the unpushed 2024 study.** `historical-edge-2024` stays local, with corrections to the public README
   proposed in its `CORRECTIONS_PROPOSED.md`. Only the author decides, and only the author closes a frozen study.
6. **README claim.** The case is 15 wallets in 353 s, not 9 in 343 s (`reports/nine_wallets/README.md`). The published text is not
   edited on this branch. Decision: whether to correct it.
