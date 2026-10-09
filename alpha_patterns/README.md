# alpha_patterns: the exploratory pattern search of October 2026

**Exploratory. Pre-registered test by test. Not validated out of sample.** This is the last study on the
live detector's alerts and the material of Act IV ([`docs/ACT_IV.md`](../docs/ACT_IV.md)). It is a
published copy of a study run outside this repository between 5 and 7 October 2026; what was copied,
what was left out and what was changed are listed at the end of this page. It is separate from the
frozen confirmatory study on the same detector, whose TEST block stays unread; nothing here uses it.

The reports, pre-registrations and audits are in French, as they were written. This page and
`docs/ACT_IV.md` carry the English account; every number in them is taken from the JSON files beside
the reports, and the JSON is the reference where the two differ.

## The question

> Is there a rule, observable at the alert (about 12 s after the token's creation), reproducible across
> launches and operators, frequent enough, with a positive expectation after costs, that predicts a
> ×2, ×3 or ×5 within one hour of an entry at alert + 5 s? (`PLAN.md`, §1)

## The answer

**NO EXPLOITABLE PATTERN FOUND**, with the power measured on synthetic outcomes: a rule at three times
the base rate on 8 to 15 % of the alerts would have been found about two times in three, a rule at 2.2
times about once in eight, a rule at the break-even lift of 1.83 once in 24, and nothing under 8 % of
support (`tables/BILAN_2026-10-06.md`, §4; `tables/CANDIDATE_SWARM_CHEAP_ENTRY_RESULT.md`).

Three mechanism studies then asked why, on the same 1,015 launches, with each study's tests fixed before
that study computed any outcome, on blocks whose outcomes the earlier search had already read:

| study | report | pre-registration | figures | verdict |
|---|---|---|---|---|
| the teams | `tables/BUNDLE_OPERATOR_FORENSICS_2026-10-06.md` | `tables/OPERATOR_FORENSICS_PREREG_2026-10-07.md` | `tables/operator_forensics.json` | **C**: the same teams launch the good and the bad tokens; their history does not say which will succeed |
| the rhythm, GOOD against BAD inside a team | `tables/BUNDLE_TEAM_RHYTHM_2026-10-07.md` | `tables/TEAM_RHYTHM_PREREG_2026-10-07.md` (amendment 1) | `tables/team_rhythm.json` | **C**: a clear rhythm, no link with the outcome; nothing measured before the alert separates a team's GOOD from its BAD |
| the absorption of the inventory by outside demand | `tables/TEAM_ABSORPTION_MECHANISM_2026-10-07.md` | `tables/TEAM_ABSORPTION_PREREG_2026-10-07.md` (amendment 1) | `tables/team_absorption.json` | **D**: no demand metric observable before the decision passes; the ×2 arrives a median 375 s after the entry |

## Population and blocks

The 1,657 alerts of the detector's snapshot of 2026-09-29 11:23 UTC (`../post_detection_edge/data/SNAPSHOT.json`),
every one a bundle snipe by construction (four wallets or more with 5 SOL or more in the creation
slot, 73 to 90 SOL in all, 75 to 81 % of the supply; `../post_detection_edge/results.md`). Blocks were cut on alert counts before any outcome was read (`PLAN.md`, §3):

| block | period (UTC) | alerts | observable 1 h outcomes | read by |
|---|---|---:|---:|---|
| DISCOVERY | 2026-08-21 → 09-07 | 643 | 363 | the mechanical search, the composites, the autopsy, the three mechanism studies |
| SELECTION | 09-07 → 09-15 | 372 | 249 | the three mechanism studies (first read on 6 October; an earlier search had read it on 2 October) |
| VALIDATION | 09-15 → 09-22 | 292 | 232 | once, for the single pre-declared rule (`VALIDATION_READ.json`) |
| OOS | 09-22 → 09-29 11:23 | 350 | 295 | never (`OOS_READ.json` does not exist) |

An outcome is observable when the 5 s sampling was active (after 2026-08-25 21:47 UTC), an entry price
was read in [5, 15] s after the alert, and the hour after it was recorded. GOOD = two consecutive reads
at or above 2 × the entry price within that hour. Base rate on DISCOVERY + SELECTION: 168 of 612,
27.5 % (×3 9.6 %, ×5 2.3 %). The trade attached to every test: buy at alert + 5 s, take profit at ×2 on
the next read, exit at 1 h, $500, the cost model of `../post_detection_edge/code/trade.py`; its
break-even precision is 45.8 % (`tables/BILAN_2026-10-06.md`, §2).

## Chronology

| date (2026) | step | record |
|---|---|---|
| 5 Oct | plan written; feature matrix (547 columns from the nine earlier studies, cut at alert − 1 s); blind code review (32 findings) | `PLAN.md`, `audit/prefreeze_review_findings.md`, `audit/CORRECTIFS_2026-10-06.md` |
| 6 Oct | DISCOVERY search: 3,100 atoms, 3.24 to 3.27 M rules per target (9.76 M in all); synthetic controls of the whole chain | `tables/discovery_summary.json`, `tables/BILAN_2026-10-06.md`, `controles/ctl_00_controls.log` |
| 6 Oct | 17 features from the Pump-Gold concepts (wash trading, external flows) built and screened on DISCOVERY | `tables/PUMP_GOLD_FEATURE_AUDIT_2026-10-06.md`, `tables/pumpgold_sanity.json`, `tables/pumpgold_screen.json` |
| 6 Oct | 32 pre-specified composite patterns scored on DISCOVERY; autopsy of the best one (D1) | `tables/composite_patterns_owner.json`, `tables/composite_patterns_results.json`, `tables/BREAK_THE_LOOP_2026-10-06.md` |
| 6 Oct 17:53 UTC | one pre-declared candidate frozen (SWARM + CHEAP ENTRY); mechanical selection abandoned (`PLAN.md`, §11, whose heading is dated 7 October while the freeze files are stamped 6 October 17:53 UTC; the files are followed here) | `tables/CANDIDATE_SWARM_CHEAP_ENTRY.md`, `tables/CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json`, `SELECTION_FREEZE.json` |
| 6 Oct 17:53 UTC | VALIDATION read once: 13 fires, 5 hits, 38.5 % against 30.6 %, p 0.39, fail | `VALIDATION_READ.json`, `tables/validation.json`, `tables/CANDIDATE_SWARM_CHEAP_ENTRY_RESULT.md` |
| 6 to 7 Oct | operator forensics (computed 6 October, report written 7 October; first read of SELECTION by this study, the 2 October search had read it before) | `tables/OPERATOR_FORENSICS_PREREG_2026-10-07.md`, `tables/BUNDLE_OPERATOR_FORENSICS_2026-10-06.md` |
| 7 Oct | team rhythm: blind review of the code before any outcome, synthetic controls, then the tests; two independent reviews of the conclusions | `audit/TEAM_RHYTHM_PREAUDIT_2026-10-07.md`, `controles/team_rhythm_controls.json`, `tables/BUNDLE_TEAM_RHYTHM_2026-10-07.md`, `audit/TEAM_RHYTHM_CLAIMS_AUDIT_2026-10-07.md` |
| 7 Oct | absorption: blind review, measures, tests, a declared post-hoc check; two independent reviews of the conclusions | `audit/TEAM_ABSORPTION_PREAUDIT_2026-10-07.md`, `tables/TEAM_ABSORPTION_MECHANISM_2026-10-07.md`, `tables/team_absorption_posthoc_nobig.json`, `audit/TEAM_ABSORPTION_CLAIMS_AUDIT_2026-10-07.md` |
| 7 Oct | this copy: the time-to-×2 summary (`code/desc_46_x2_timing.py`) and the integrity check (`code/chk_00_integrity.py`) added | `tables/x2_timing_summary.json` |

The two independent reviews of the rhythm and absorption conclusions returned FAIL on first reading
(rounding, denominators, one sentence about the timing of the teams' liquidation that the cited studies
contradicted); every correction was applied before the version published here, without a change of
method. The forensics report had no such review. The audits are published so that the corrections can
be read.

## Where each figure of Act IV comes from

| figure quoted in `README.md` / `docs/ACT_IV.md` | file | field |
|---|---|---|
| 1,657 alerts | `../post_detection_edge/data/SNAPSHOT.json` | `n_alerts` |
| 1,015 launches, 612 observable, 168 GOOD, 27.5 % | `tables/team_absorption.json` | `population.alerts`, `population.Y2.eligible`, `.good`, `.rate` |
| ×3 9.6 %, ×5 2.3 % | `tables/operator_forensics.json` | `population.base` |
| 3,237,943 rules evaluated for the ×2 on DISCOVERY; 37,296 passed | `tables/discovery_summary.json` | `Y2.evaluated`, `Y2.passed` |
| 26,655 passed with shuffled outcomes; break-even 45.8 % | `tables/BILAN_2026-10-06.md` | §1, §2 |
| planted ×3 survives 16 of 24, ×2.2 3 of 24, ×1.83 1 of 24 | `tables/BILAN_2026-10-06.md`, `controles/ctl_00_controls.log` | §4; `PLANTED_*` |
| 32 composites, best D1 16 of 40 at −12 % | `tables/composite_patterns_results.json`, `tables/BREAK_THE_LOOP_2026-10-06.md` | `patterns[*]` with `id = D1_sync_sizes_shared_funder`, `main.Y2.{n, successes, ev_500}`; §2 |
| 31,656,419 comparisons on real data | `registre/tests.jsonl` | sum of `n_comparaisons` where `donnees = reelles` |
| 2,189 sniper wallets, 81 % used once; three modes | `tables/BUNDLE_OPERATOR_FORENSICS_2026-10-06.md` | §1, §2 |
| links confirm each other 47 to 212 × chance (45 to 220 in the report's rounding) | `tables/operator_forensics.json` | `groupings.corroboration`: for the wallet, funder, co-occurrence and configuration links, `also_X` / `sameweek_baseline_X`; zero baselines and co-occurrence → wallet (1.0 by construction) left out |
| 188 groups; 33 ≥ 5, 19 ≥ 10, 3 ≥ 20; largest 224 (22 %) | `tables/operator_forensics.json` | `groupings.stats.U` |
| rates 0 % to 58 %; χ² 41.4, p 0.0008 / 0.0017 / 0.0012; ×3 p 0.62 | `tables/operator_forensics.json` | `heterogeneity.U.Y2.10`, `heterogeneity.U.Y3.10`, `groups.U[*].rate_x2` |
| group 0.68 against day 0.43 (logit) | `tables/operator_forensics.json` | `mixed_model.group+day.sd_mean` |
| P(S after S) 32.0 %, P(S after F) 25.8 %, p 0.92; after two F 21.3 % against 34.0 % | `tables/operator_forensics.json` | `sequences.U.Y2` |
| history gain −0.016 / +0.038 / +0.003 [−0.021, +0.046]; AUC 0.43 / 0.66 / 0.56 | `tables/operator_forensics.json` | `history_prediction.U.{DISC,SEL,ALL}.Y2_nprev5`, `.Y2_auc_nprev5.rate_prev` |
| high-confidence rule 3 of 29 (10.3 %) against 44.1 %, EV −55 % | `tables/operator_forensics.json` | `history_prediction.U.ALL.Y2_HC1` |
| g169: 5/11, 0/8, 5/6, p 0.006 | `tables/operator_forensics.json` | `regimes.U.per_group` |
| gap in session median 20.6 min (15.1, 29.5); 4.7 % under 10 min against 47.2 % | `tables/team_rhythm.json` | `rhythm_descriptive.gap_in_session_quantiles_min`, `.gap_team_share_lt10`, `.gap_market_share_lt10` |
| 17 rhythm and sequence tests, best q 0.26; after two BAD 21.6 % (40 of 185) | `tables/team_rhythm.json` | `rhythm_vs_outcome.*`, `sequences.*` (`q_bh_sections_2_3`), `sequences.S3_after_two_bad` |
| rank ≥ 7: 41 of 103 (40 %) against 84 of 310 (27 %), q 0.34 | `tables/team_rhythm.json` | `rhythm_vs_outcome.R3_rank_in_session` |
| 28 of 33 teams have both; 32 within-team variables, best q 0.13 (swarm at −5 s, 0.67 / 0.46) | `tables/team_rhythm.json` | `population.within_teams_mixed`, `within_team.*` |
| changes of configuration (C1), every q ≥ 0.998; heterogeneity across a team's configurations (C2), q 0.47 to 1.0; other teams ±60 min, correlation 0.001 | `tables/team_rhythm.json` | `configuration_changes.C1_*`, `.C2_*`, `interaction.I1_contemporaneous_other_teams_60min` |
| four prediction models announce nothing | `tables/team_rhythm.json` | `prediction.*_announces` |
| power: AUC 0.68 in 47 of 50, +20 points in 46 of 50, +15 in 31 of 50, +10 in 5 of 50 | `tables/BUNDLE_TEAM_RHYTHM_2026-10-07.md`, `controles/team_rhythm_controls.json` | §1 |
| 308,520 transactions reconstructed | `tables/team_absorption_checks.json` | `K1.records` |
| the GOOD / BAD medians table (inventory 77.7 / 77.8 %, 294 / 297 SOL, delays, sold shares) | `tables/team_absorption.json` | `mechanism.descriptive.*` |
| external buyers 37 / 42 / 86 against 35 / 40 / 84; demand over inventory 3.0 % and 11.0 / 9.9 %; recurrent bots ~80 % | `tables/team_absorption.json` | `mechanism.timeline_medians.{-1,2,29}.M1_ext_buyers`, `.{2,27}.M7_demand_over_inventory`, `.{-1,2}.M9_recurrent_share` |
| price ×1.09 / 1.16 / 1.27 / 1.55 against ×1.01 / 1.00 / 0.96 / 0.64 | `tables/team_absorption.json` | `mechanism.price_after_entry.at_{30,60,120,300}` |
| ×2 confirmed: p10 118 s, median 375 s, p90 1,503 s; 1.2 % within 30 s, 10.7 % within 2 min, 42.3 % within 5 min | `tables/x2_timing_summary.json` | `t_hit_2x_s`, `share_of_good_confirmed_within_s` |
| 19 pre-entry metrics, best AUC 0.60, p 0.027, q 0.41, inverts (0.64 / 0.45) | `tables/team_absorption.json` | `explanatory.M1_ext_buyers\|-1` |
| 40 tradable tests, best q 0.91 | `tables/team_absorption.json` | `tradable.*` |
| 12 teams of 13, sign test p 0.003; equal-price AUC 0.58, p 0.14 | `tables/team_absorption.json` | `per_team.*.M7`, `equal_price.M7_demand_over_inventory` |
| post hoc without the diffuse population, demand velocity at +20 / +30 s: AUC 0.61 to 0.65, SELECTION p 0.18 / 0.14 | `tables/team_absorption_posthoc_nobig.json` | `hits.M3_ext_buy_sol_last10\|20`, `\|30` (`auc`, `p_SEL`) |
| five rules, none meets the bar; R2 at +10 s 6 of 12 | `tables/team_absorption.json` | `rules.*.*.meets_A`, `rules.10.R2_demand_inventory_ge0.25` |
| SWARM + CHEAP ENTRY on VALIDATION: 13 fires, 5 hits, 38.5 % against 30.6 %, lift 1.26, p 0.394, EV −11.6 % | `tables/validation.json` | `[0].val` |
| exit wallets sell a median 81 s after receipt (p25 35, p90 330) | `../exit_destination/results.md` | section on delays |

## What is published here, and what is not

| published | not published (size as measured on the author's machine, frozen sha256 in `SELECTION_FREEZE.json`) |
|---|---|
| the plan, its deviations, the two freeze and read markers | the feature matrix `derived/X.npz` (4 MB) and its column list |
| every report, pre-registration, bilan and audit named above | the labels `derived/labels.jsonl.gz` (1 MB; its hash is checked by `code/desc_46_x2_timing.py` before the summary is computed) |
| every result JSON of the tables above | the atoms, the candidate firing vectors, the swarm features |
| the chained test registry `registre/tests.jsonl` | the synthetic controls `controles/ctl_00_controls.json` (7 MB; the log and the summary tables are published) |
| the synthetic controls of the rhythm study | the feature inventory (`tables/FEATURE_INVENTORY.*`, which quotes local paths) |
| all 30 scripts of the study, 29 byte for byte and one with the single-line change listed below, plus the two added for this copy | the raw per-alert windows and wallet caches (read from the earlier studies' worktrees) |
| the small coverage and exclusion files of `derived/` | `REPRISE.md`, the session hand-over notes |

## Integrity, offline

```bash
python3 alpha_patterns/code/chk_00_integrity.py
```

checks that the 17 published files listed in `SELECTION_FREEZE.json` still carry their frozen sha256,
that each result JSON names the sha256 of the pre-registration it was computed under and that the
published pre-registration matches it, that `tables/x2_timing_summary.json` was computed on the frozen
labels file, and compares every script and output hash recorded in `registre/tests.jsonl` with the
published file (25 match; 11 refer to earlier versions of scripts or outputs that were re-run later,
the registry keeps every run; 6 point to files not published here and are not compared).

## Reproduction

Nothing in CI executes these scripts: they read the unpublished derived files and the frozen tables of
the nine earlier studies through the paths in `code/ap_lib.py`. They are published so the method can be
read line by line, not re-run from a clone. What runs from a clone:

```bash
python3 alpha_patterns/code/chk_00_integrity.py      # the three checks above
python3 code/f_act_iv_timeline.py                     # figure F5 from the committed JSON (matplotlib)
python3 code/p1_readme_check.py                       # the Act IV figures of README.md against these files
```

## Deviations of this copy from the original study folder

- `code/mech_48b_posthoc_nobig.py`: one line changed, an absolute `sys.path` entry replaced by the
  script's own directory (the publication gate refuses local paths). The registry records the
  original under its out-of-study path and hash (`<hors etude>/posthoc_nobig.py`, run with the code not
  frozen); `chk_00_integrity.py` counts that line among the files not published here and does not
  compare it.
- `code/col_49_long_windows.py`, `code/col_49b_priority.py`, `code/feat_49_long.py`, `code/net/`,
  `derived/long/` and `tables/TEMPORAL_DIVERGENCE_PREREG_2026-10-07.md`: a collection beyond
  alert + 30 s that was being started when this copy was made, with no result. Not published here; it is
  not part of Act IV.
- `tables/FEATURE_INVENTORY.json` and `.md`: not published (local paths); the inventory's counts are in
  `tables/discovery_summary.json`, `atoms`.
- `code/desc_46_x2_timing.py`, `code/chk_00_integrity.py`, `tables/x2_timing_summary.json`: added for
  this copy, standard library only.
