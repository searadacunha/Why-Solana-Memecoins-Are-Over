# Pitfalls met in this study

Each one either changed a number or would have, had it not been caught. They are listed with the size
of their effect, measured on this corpus.

## 1. A trade that wins early escapes the outage that disqualifies a loser

The first version of the trade simulator stopped checking coverage at the exit. A trade that hit its
take-profit in the first minutes was scored even if the detector fell asleep afterwards, while a trade
still open was censored by the same outage. The scored sample leaned to winners. On VALIDATION, hold
to 2x for 1 h: take-profit share 40.4 %, against the complete-case 2x rate of 33.9 % for the same
population, and a net return of -25.4 %. Deciding eligibility on coverage of the whole holding window,
before looking at the exit, brought the take-profit share to 34.1 % and the net to -35.7 %. Fixed
before the lock, on VALIDATION only. The same rule governs the targets (§4 of the methodology).

## 2. An 80 % rule is the expected output of the search, not a finding

482,519 conjunctions evaluated on 250 TRAIN alerts produced 2 rules at 80 % or more for 2x within 1 h
and 8 for 2x within 15 min, every one of them with N between 20 and 28. They scored 13 to 41 % in
VALIDATION and 11 to 44 % in TEST, around base rates of 31 to 38 %. The 202 rules between 70 and 80 %
pool to 71.8 % in TRAIN, 30.5 % in VALIDATION and 40.4 % in TEST, against a base of 37.9 %. The number
of rules crossing a bar grows with the size of the search; their out-of-sample rate does not move.

## 3. Hit rate is not return

The one signal that survived raises P(2x within 15 min) to 45.7 %, and its hold-to-2x trade still
loses 9.8 % gross. A launch that has not doubled after 15 minutes has lost 98.9 % on average, so
holding for 2x needs a doubling rate of 49.7 % to break even before costs and 58.5 % after. With a
-20 % stop the bar falls to 18.7 %, but the stop also removes half the doublings. A probability of 2x
answers a classification question. Whether money is made is a separate measurement.

## 4. Censoring by the detector's own sleep

The machine that runs the detector slept for 489 hours of the 930. At 1 h, 351 of 1,648 windows are
censored; at 24 h, 1,601. The 47 alerts observed for a full day are all from late September and show a
24 h doubling rate (27.7 %) below the 1 h rate of the whole population (36.3 %). That is not a
decrease over time, it is a different set of launches. Scoring censored windows as misses would
understate every rate; scoring early hits in censored windows while dropping censored misses would
overstate it. Complete-case on coverage decided in advance avoids both, and the bounds are printed.

## 5. A threshold on a knife edge

The headline rule's last condition, entry price at most 3.55 times the operator's, selects 76 TEST
alerts. Moving the threshold by +5 % selects 133, and by -5 % selects 39, with rates of 37.6 % and
33.3 %. A rule whose N changes by a factor of three for a 5 % move was fitted to the TRAIN sample's
granularity. It lost 34 points between TRAIN and TEST.

## 6. The entry premium is most of the signal, and it is the operator's

Across every horizon, the family that separates best is the entry price relative to the operator's:
p0, the market cap at P0, and p0 over the operator's VWAP (median x3.7, q90 x11). Part of that
premium is set by the operator, who in some pools buys its own pool in the creation block. A
cheaper entry doubles sooner, which is arithmetic as much as information, and it does not change
whether the launch doubles within the hour (AUC 0.43 to 0.46).

## 7. Operators are not independent observations

One cluster, linked by reused sniper wallets, holds 320 of the 1,657 alerts and runs across all three
splits. Alert-level Fisher tests treat each of them as independent. Every conclusion here rests on
cluster-bootstrap intervals and leave-one-cluster-out checks instead. For the surviving signal they
agree: 43.9 % to 47.1 % whichever cluster is removed.

## 8. A pre-registered protocol that stopped being fed

The protocol of 2026-08-29 needed a daily collection (funding lineage, copied names, exit
destinations) that stopped on 2026-08-31. Evaluated as written, three of its six hypotheses are not
evaluable. The detector's own evaluation script would still print a verdict for the main one (C1),
because it treats a lineage that was never collected as "no dead hub". That reading is shown, and
labelled, but it is not the registered test.

## 9. The definition decides the population

The repository's definition (at least 60 SOL in the creation slot) and the detector's (at least 4
snipers of 5 SOL or more, 73 to 90 SOL, 75 to 81 % of supply) differ by a factor of 4.6 in the number
of launches. Only the detector's 1,657 have outcomes; the other 5,902, 5,127 of them with a single
large sniper, were rejected before any price was read. ANSEM belongs to that other family (two buyers)
and falls outside the window in any case. Results here are about the detector's population only.

## 10. Hypotheses carried in from earlier work

The grouped actor had shown a tail effect in August. Here it scored 37.9 % against 38.0 % in TRAIN,
23.7 % against 37.6 % in VALIDATION and 39.2 % against a 37.9 % base in TEST: the sign changed twice.
The market-cap bands (under $60k, $40k to $60k) had been found by looking at earlier data. They sit on
the base rate in TEST (+0.1 and -0.1 points). Hypotheses found by looking deserve a test on data that
was not looked at, which is all this study did with them.

## 11. Two sampling regimes in one corpus

Until 2026-08-25 21:47 UTC the detector read prices every 45 s; after that, every ~5 s for the first
three minutes. A maximum grows with the number of reads, so rates at short horizons are not comparable
across the two regimes. The 207 coarse alerts, all in TRAIN, are marked missing below 180 s rather
than mixed in.

## 12. Deterministic files, or the lock proves nothing

gzip writes a timestamp into its header, so regenerating identical rows changed the file's sha256,
and the hash recorded in the lock would have stopped matching after any rerun. The derived datasets
are now written with a zero timestamp; two rebuilds give the same hash, and the final test refuses to
run on data whose hash differs from the lock.
