# Analysis plan, written before the table is frozen and before any rate is computed

Question: is there an on-chain structure, measurable before the entry, that separates the bundle
snipes that double quickly from the others, beyond the two variables already known to carry
information (the actor label and the entry premium)?

The plan tries to destroy that hypothesis. It is fixed here, before the analytic table exists; any
later change is listed at the end of results.md as a deviation.

## Data

- One row per detector alert of the first snapshot (1 657 alerts, 2026-08-21 to 2026-09-29), with
  on-chain features from `code/feat_30_build.py` after the corrections of 2026-09-29
  (`temporal_leakage_audit.md`, `ticket_reconciliation_phase3.md`).
- The table (`derived/analytic_table.jsonl.gz`) is written once by `code/ana_00_freeze.py`; its
  sha256 is recorded in `derived/TABLE_FREEZE.json` and committed before any screening. It is not
  modified afterwards.
- Splits, by alert time: TRAIN before 2026-09-15 00:00 UTC (1 015 alerts), VALIDATION from then to
  the snapshot (642 alerts). TRAIN is for exploration; VALIDATION only re-measures what TRAIN chose.
  VALIDATION was the previous study's TEST and was read once there. The future TEST (alerts after
  2026-09-29 11:23 UTC) is a separate question and is not touched here.
- Nothing measured on TRAIN is called "robust".

## Labels

- Primary: `A_conf_2x_15m`, a 2x from P0 confirmed by two consecutive reads inside 15 minutes,
  complete-case (windows not observed are excluded, never scored as misses).
- Also reported, never used to choose: `A_conf_2x_5m`, `A_conf_2x_1h`, `A_conf_1.5x_15m`,
  `A_conf_3x_15m`, and every single-read twin.
- Robustness variants, fixed now: window 10 / 15 / 20 min; threshold 1.8 / 2.0 / 2.2x; one read vs
  two reads; feature cut-off alert - 1 s / - 2 s / - 5 s.

## Feature sets (families of feature_dictionary.md, PRE_ENTRY and SAFE only)

bundle, funding, wallets, history, micro, price (without the premium), premium
(`p_entry_over_operator`), actor (`c_actor_grouped`), context. Cut-off A (alert - 1 s) is the
primary one.

## Steps, in this order

1. Descriptive, winners vs losers (primary label), TRAIN, then the same statistics on VALIDATION:
   mean, median, q10 / q25 / q75 / q90, absolute and relative difference of medians, Mann-Whitney
   p, AUC as effect size, 95 % cluster-bootstrap CI of the difference of medians (operator
   clusters, 1 000 draws). Benjamini-Hochberg across all features in TRAIN.
2. Combined structures, systematic: every pair of SAFE features, both split at their TRAIN median;
   the best of the four cells against the rest in TRAIN (one-sided Fisher, x4 for the choice of
   cell), BH across all pairs; the same cell re-measured in VALIDATION. The pairs the owner listed
   (sniper count x SOL concentration, sniper count x funding hub, deployer funding x wallet age,
   common funding x buy timing, concentration x median ticket, independent wallets x ticket
   dispersion, wallet history x funding, pre-alert exits x bundle structure, premium x funding
   structure) are inside this grid and are reported whatever they give.
3. Actor vs premium: six ridge logistic models fitted on TRAIN, penalty chosen on VALIDATION:
   A actor; B premium; C actor + premium; D every on-chain feature without actor; E every
   feature + actor; F every feature + actor + premium. VALIDATION ROC-AUC, PR-AUC, precision in
   the top 10 / 20 %, with cluster-bootstrap CIs of the AUC differences (E - D, F - C, C - B, C - A).
   The overlap of actor and premium is reported as counts.
4. Funding flows: per-sniper descriptives and the funding features against the label, TRAIN then
   VALIDATION, inside the multiplicity count of step 1.
5. Profiles, defined now with TRAIN medians, never ranked: 1 concentrated bundle (b_top1 above
   median), 2 distributed bundle (b_indep: f_indep_share = 1 and b_ticket_cv below median),
   3 common funding (f_same_funder_multi = 1), 4 distributed funding (f_n_funders >= 3),
   5 experienced early wallets (w_early_log_prior_n above median), 6 fresh early wallets
   (w_early_fresh above median). For each: N, 2x within 5 min / 15 min / 1 h, median time to the
   confirmed 2x, MFE distribution, Wilson CIs, TRAIN and VALIDATION separately.
6. Simple rules: conjunctions of 1 to 3 conditions (TRAIN deciles), TRAIN support >= 40, TRAIN
   score = Wilson lower bound; the 50 best go to VALIDATION; the best VALIDATION lower bound with
   VALIDATION N >= 40 is kept. Every rule reaching 60 / 70 / 80 % in TRAIN is listed with its
   VALIDATION rate. The number of rules evaluated is written.
7. Machine learning: ridge logistic, tree (depth 2-3), forest (200 trees, depth 3-5), boosting
   (50-300 rounds) on each feature set (bundle, funding, wallets + history, micro, actor, actor +
   premium, price + micro, all, and "screened" = the step 1 features passing BH in TRAIN plus actor
   and premium), TRAIN fit, VALIDATION choice; ROC-AUC, PR-AUC, Brier, calibration, precision,
   recall, F1, precision at 5 / 10 / 20 / 30 %. Main metric: precision of the selected subgroup on
   the primary label.
8. Robustness of whatever steps 6 and 7 select (step 7 selects the "screened" model, its top
   20 % by the TRAIN score threshold): the pre-declared variants above, and VALIDATION
   cut by first / second half. August and September are reported with their split named.
9. Mechanics: for any selected signal, its correlation with P0, premium, pool reserve, curve
   progress, actor and funding; any pair of variables with |Spearman| >= 0.8 or a 2x2 overlap below
   20 alerts in a cell is reported as not separable. The signal's lift beyond a TRAIN model of P0,
   premium and actor (boosting, 150 rounds): on VALIDATION, observed minus expected inside the
   signal minus the same outside it, with a cluster-bootstrap CI.
10. Matched comparison: alerts stratified by week, premium band (TRAIN terciles), number of core
    wallets and bundle SOL (TRAIN medians); within strata, funding topology (common funder vs not) compared on the
    primary label; Mantel-Haenszel-type pooled difference with a stratified bootstrap CI.

## Verdict rules (fixed now)

- INCONCLUSIVE if fewer than 80 % of the alerts have on-chain features, or fewer than 300
  VALIDATION alerts have an observed 15-minute window.
- "Independent on-chain information" = the step 7 "screened" model beats the step 7 "actor +
  premium" model (same model grid) on VALIDATION ROC-AUC with a 95 % cluster-bootstrap CI of the
  difference above 0. Model F minus model C (step 3) and "all" minus "actor + premium" (step 7)
  are reported, not used.
- PROMISING HISTORICAL SIGNAL - NOT YET PROVEN OOS = independent on-chain information AND a rule
  or model subgroup with VALIDATION N >= 50 whose rate exceeds the VALIDATION base by at least
  15 points with a Wilson lower bound above the base, holding (rate still above the base with a
  Wilson lower bound above it) under at least 6 of the 7 pre-declared variants (window 10 min,
  window 20 min, threshold 1.8x, threshold 2.2x, single read, cut-off -2 s, cut-off -5 s), and not
  explained by P0 / premium / actor (step 9: |Spearman| below 0.8, no 2x2 cell below 20 against
  actor or premium band, and a lift beyond the P0 + premium + actor model whose CI stays above 0).
- WEAK ON-CHAIN SIGNAL = independent on-chain information exists but the subgroup criterion fails.
- NO ROBUST ON-CHAIN SEPARATION FOUND = no independent on-chain information.
- ROBUST ON-CHAIN SIGNAL is not reachable here: it needs the future TEST.
- Nothing is called exploitable without realistic costs and execution prices, which this historical
  analysis does not claim to settle.
- The verdict is computed by `code/ana_90_verdict.py` from the step outputs, not written by hand.

## Amendments of 2026-09-29, before the table was frozen

Made after a dry run of every step on a synthetic table (random features, a planted premium effect,
and in turn no, a moderate and a strong planted on-chain effect), and before any real rate was
computed. What the dry run showed, and what changed:

1. The step 3 gate (ridge logistic F on every feature, minus C) did not see a strong planted
   on-chain effect: +0.006 [-0.059, +0.067], while the funding models alone reached ROC-AUC 0.68.
   A ridge logistic on about 140 mostly empty features drowns a sparse effect. The gate moved to
   step 7, with the same model grid on both sides and the step 1 TRAIN screen deciding which
   on-chain features enter ("screened").
2. With no on-chain effect, the "screened" model reduces to actor + premium, and its top 20 %
   passed every subgroup check of step 9 as written (|Spearman| and 2x2 cells): those checks do
   not detect a signal that is the premium itself. A lift within premium and P0 terciles still
   passed (+14 points, CI above 0), because coarse strata leave premium confounding inside each
   tercile. The residual lift beyond a TRAIN model of P0, premium and actor was added; on the null
   control it gives +3.4 [-6.5, +12.9] and correctly calls the signal explained.
3. Step 6 could keep a rule with fewer than 40 VALIDATION alerts when no rule reached that N; it
   now keeps none in that case.
4. Step 10 stratified on the independent-actor count, which is built from shared funders, hence
   from the treatment (common funding) itself. It now stratifies on the owner's list: period,
   premium, bundle size (SOL) and number of wallets. Step 8 adds the weeks, and step 9 the token
   quantity (`b_core_supply`) and the reserve ratio, as the brief lists them.

What the pipeline can see (`tables/D0_power_dry_run.md`, synthetic tables, four seeds per size,
about 550 VALIDATION alerts): no false positive in four null runs; a planted on-chain effect with an
odds ratio of about 4.5 passes the gate 4 times out of 4 and reaches PROMISING 3 times out of 4; an
odds ratio of about 2.7 passes the gate 2 times out of 4 and never reaches PROMISING. A NO ROBUST
ON-CHAIN SEPARATION verdict therefore excludes large on-chain effects, not moderate ones.
