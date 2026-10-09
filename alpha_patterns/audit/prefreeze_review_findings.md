# Revue à l'aveugle avant le gel (2026-10-05), constats à traiter

## review:silent-failures : PASS_WITH_FIXES

- [MAJOR] `ap_mine.py:347` Bootstrap de grappes : les tirages sans déclenchement sont écartés, aucune protection pour une règle portée par 1 à 4 grappes en VAL / OOS
  - Correctif proposé : Compter les tirages écartés contre la règle : `p_b = (np.sum(d <= 0) + (cfg["BOOT"] - good.sum()) + 1) / (cfg["BOOT"] + 1)`. Ajouter `ev["n_clusters_fire"] >= cfg["MIN_CLUSTERS"]` dans val_pass et oos_decide. Relancer les contrôles avant le gel.
- [MAJOR] `ctl_00_controls.py:171` Le JSON des contrôles enregistre le CFG par défaut du parent, pas celui utilisé par les workers
  - Correctif proposé : Faire remonter la vérité par les workers : `out["cfg"] = dict(M.CFG); out["bases"] = _G["bases"]` dans one(), écrire ces valeurs et lever si elles diffèrent entre runs. Ou appliquer les surcharges au niveau module. Refuser d'écraser un fichier de sortie existant.
- [MAJOR] `rob_80_robustness.py:112` Critère « seuils voisins » : vérifications sautées en silence, résultat binaire repris tel quel dans le verdict
  - Correctif proposé : Écrire par atome un état à trois valeurs (testé / non testable / voisin identique) et le nombre de voisins écartés pour n < 5. Dans rep_90, distinguer « non mesurable » de « échec ». Décider avant le gel si un voisin à n < 5 est un échec. Pour un voisin identique, passer au quantile suivant réellement distinct. Écrire `cutoffs: "not_testable"` quand aucune variante n'existe.
- [MINOR] `ap_mine.py:175` Triples : amélioration testée contre la paire-graine seule, pas contre « le meilleur parent » du plan ; graines classées avant les filtres ; ex aequo au seuil
  - Correctif proposé : Parent du triple = max des précisions des trois sous-paires (matrices C et H déjà en mémoire) et des singles. Classer les graines parmi les paires qui passent jours + grappes + plafond, avec `np.lexsort((jj, ii, -pair_lb))`. Sinon, corriger le texte du plan avant le gel (PLAN.md est haché dans le gel).
- [MINOR] `ctl_00_controls.py:52` Contrôles : atomes construits avant la surcharge AP_NMIN_DISC, replis non tracés (exclusions vides, taux de base par défaut), faux survivants gonflés dans les mondes plantés
  - Correctif proposé : Déplacer les surcharges avant prepare_atoms. Écrire dans la sortie `n_excluded`, `bases_source` (fichier ou repli) et le nombre d'atomes. Lever si les exclusions manquent, sauf option explicite. Rapporter à part les survivants sous-ensemble ou sur-ensemble de la règle plantée.
- [MINOR] `ap_mine.py:134` Égalité exacte au facteur 1,10 décidée par l'arrondi float32
  - Correctif proposé : Comparer en entiers exacts : `H * Cp * 10 >= 11 * Hp * C` en float64, ou calculer prec en float64 avec une tolérance de 1e-9.
- [MINOR] `ap_mine.py:59` Clé de déduplication des atomes limitée aux 386 lignes DISC éligibles : le survivant est choisi par ordre alphabétique alors que les jumeaux diffèrent ailleurs
  - Correctif proposé : Dédupliquer sur toutes les lignes (`vec.tobytes()`, features seules, sans issue), ou garder le choix actuel et écrire ces trois comptes dans atoms.json et dans le plan.
- [MINOR] `ap_mine.py:271` Une valeur RANK inconnue retombe en silence sur « min »
  - Correctif proposé : `elif cfg["RANK"] == "min": ... else: raise ValueError(cfg["RANK"])`.
- [MINOR] `ap_data.py:64` Trades « censored » sur lignes éligibles retirés des moyennes nettes ; IC du net dégénéré quand une seule grappe déclenche
  - Correctif proposé : Rapporter `net_censored` par règle à côté de net_n. Dans net_stats, rendre net_ci = None si K < 5, ou exiger net_clusters >= 5 dans crit["net"].
- [MINOR] `mine_50_selection.py:24` Gel incomplet et registre dépendant de mine_40 : atoms.json, rep_90 et desc_45 non hachés, comptes DISC non enregistrés par le run qui gèle
  - Correctif proposé : Dans mine_50 : écrire atoms.json soi-même, ajouter derived/atoms.json, code/rep_90_report.py et code/desc_45_families.py à FROZEN_FILES, enregistrer aussi les comptes evaluated. Faire appeler check_freeze par rep_90.
- [MINOR] `desc_45_families.py:28` Gardes d'étape contournables : desc_45 peut lire VAL ou OOS avant leur lecture unique, et SEL avant le gel
  - Correctif proposé : Dans desc_45 : refuser « validation », exiger OOS_DONE pour « oos », exiger SELECTION_FREEZE.json pour « selection » (le lancer après le gel).
- [MINOR] `ap_lib.py:62` 23 alertes éligibles du régime de relevé grossier dans DISC, toutes dans la première moitié temporelle
  - Correctif proposé : Décider avant le gel : exiger `r["fine"]` dans l'éligibilité (ap_data.py:46 et elig_all de ctl_00), ou garder ces 23 lignes et l'écrire dans le plan. Corriger le commentaire.
- [MINOR] `inv_00_inventory.py:32` Une feature signalée LEAK ou AMBIGUOUS mais absente de la matrice ne lève pas
  - Correctif proposé : Lever si un nom LEAK / AMBIGUOUS est absent de la matrice, sauf `miss__X` dont X est exclu.

## review:leakage : PASS_WITH_FIXES

- [MINOR] `ap_data.py:46` Mixed sampling regime: 23 eligible DISC rows are labelled from the 45 s series, not the 5 s one
  - Correctif proposé : Require fine (t >= T_FINE) in the eligibility at ap_data.py:46, feat_20_history.py:111 and ctl_00_controls.py:40, or state in PLAN.md section 4 that the 23 coarse rows are kept. This changes the population, so it must be written into the plan before the freeze (an amendment if done after).
- [MINOR] `desc_45_families.py:26` desc_45_families.py reads SEL before the freeze and VAL or OOS outside the one-read markers
  - Correctif proposé : Refuse 'selection' until SELECTION_FREEZE.json exists (the script is descriptive and loses nothing), refuse 'validation' and 'oos' unless VAL_DONE and OOS_DONE exist, and reject any other stage. No change of method.
- [MINOR] `mine_50_selection.py:24` Freeze list misses files that feed the post-OOS verdicts
  - Correctif proposé : Add code/rep_90_report.py, code/desc_45_families.py, derived/atoms.json and tables/FEATURE_INVENTORY.json to FROZEN_FILES, or recompute ref_rows in rob_80 from the frozen labels. Keep deviations in a separate file outside the hash. No change of method.
- [MINOR] `inv_00_inventory.py:38` Status SAFE is the default for 324 features that the causality audit did not cover
  - Correctif proposé : Give unaudited features a distinct status (NOT_AUDITED) and have rep_90 print it instead of FAIBLE; record this review's coverage for h1_ and x_. Wording only, no change of method unless a feature is later excluded.
- [MINOR] `feat_30_table.py:26` Hourly SOL/USD quote kept in three columns while the lv twins are dropped as look-ahead
  - Correctif proposé : Check the SOL/USD source in the builder of the analytic table. If it is the same-hour close, exclude the three columns like the lv twins (p_log_p0 and ez_log_price already carry the price). Excluding a feature before the freeze is a plan edit, an amendment after it.
- [MINOR] `ap_mine.py:91` 'Feature is missing' atoms are generated for features whose audit caveat is precisely their missingness
  - Correctif proposé : Let the inventory carry a 'no_missing_atom' flag for those caveats and skip line 91 for flagged features, or drop missing atoms for SAFE_WITH_CAVEAT features. This changes the rule space: decide before the freeze and write it in PLAN.md section 5.
- [MINOR] `ap_mine.py:153` The 'different families' rule is defeated by copies of one measure filed under two families
  - Correctif proposé : Before pairing, forbid pairs whose two features have |Spearman| >= 0.97 on DISC (feature-only), or give copies the family of their original. Report such rules as depth 1. Changes the rule space: plan edit before the freeze.
- [MINOR] `ctl_00_controls.py:72` The synthetic NULL world does not exercise the outcome-to-history-feature path nor a calendar-day effect
  - Correctif proposé : For (1), add one control run where h1_ features are rebuilt from the synthetic outcomes, including a positive control with the gate deliberately removed. For (2), add a day random effect to the NULL world or a day-block bootstrap as a third p-value. If the VAL or OOS test changes, that is a plan edit before the freeze.

## review:statistics : PASS_WITH_FIXES

- [MAJOR] `PLAN.md:100` A negative verdict only excludes large effects: detectable lift is far above break-even and the positive control hides it
  - Correctif proposé : Before the freeze, write the detectable effects in PLAN sections 8 and 10 next to the break-even lifts (x1.83, x2.9, x7.0), add planted scenarios at those lifts and a 5 to 8 % support band, and word the negative verdict as 'no rule with support >= 8 % and Y2 lift >= about 3 was found; x2.2 is seen about 1 time in 4'. Treat Y5 as descriptive or state that it has no power.
- [MAJOR] `ap_mine.py:316` The hold-out p-value ignores the day: day-driven atoms (c_dow, lv_dow, reg_weekend, regime rates) are tested on about 6 days as if on 232 or 295 alerts
  - Correctif proposé : p = max(Fisher, cluster bootstrap, within-day CMH or within-day permutation); drop c_dow, lv_dow and reg_weekend (5 weeks cannot identify a weekday effect); add a NULL world with a day random effect (sd 0.4 and 0.8) to ctl_00; print the number of distinct firing days for every candidate and report day-level n for any survivor with a regime atom.
- [MAJOR] `rep_90_report.py:70` INTERESTING is what pure noise produces: about 1 per run, at least one in about half the runs
  - Correctif proposé : Have ctl_00 count INTERESTING verdicts in the NULL world and print the null rate next to every INTERESTING line of TOP20.md ('expected about 1 per study under noise'); or rename the label to a neutral descriptive one. Do not let INTERESTING motivate a follow-up without a prospective sample.
- [MAJOR] `mine_50_selection.py:24` The script that assigns the verdict is outside the freeze, is never exercised on synthetic data, and differs from PLAN section 10 in several cases
  - Correctif proposé : Add rep_90_report.py, desc_45_families.py, atoms.json, FEATURE_INVENTORY.json and the final control report to FROZEN_FILES and call check_freeze in rep_90. Run rob_80 and rep_90 once on a synthetic world (synthetic nets drawn from DISC payoffs) inside ctl_00. Rewrite section 10 as an ordered decision list that matches the code, including the composite and no-neighbour cases.
- [MINOR] `ap_mine.py:347` The cluster bootstrap gives no protection when a rule fires in 1 to 3 clusters, and OOS SURVIVOR has no minimum number of clusters
  - Correctif proposé : p_boot = (draws <= 0 + draws without a fire + 1) / (BOOT + 1), and require n_clusters_fire >= 5 in VAL and in OOS for OOS SURVIVOR (the field is already computed by evaluate).
- [MINOR] `ap_mine.py:42` BOOT = 2000 does not resolve the Holm thresholds: pass or fail can depend on the seed
  - Correctif proposé : BOOT >= 100,000 for VAL and OOS (the code already works on per-cluster sufficient statistics, so it is cheap); flag any p_boot below 5e-4 as a bound.
- [MINOR] `ap_mine.py:360` Net return of a survivor is estimated on the blocks that selected it: point estimate biased up by 9 to 14 points per trade, lower bound mildly optimistic
  - Correctif proposé : Keep the criterion (it is a real filter) but state in the report that the net of a survivor is measured on its selection blocks, with the expected upward bias; use a 99 % one-sided bound or a studentised cluster bootstrap when fewer than 35 trades; never quote the point estimate without that note.
- [MINOR] `ctl_00_controls.py:169` Control report: 12 seeds cannot certify 5 %, the recorded cfg is the parent's not the workers', design runs used placeholder base rates, partial detections are counted as false
  - Correctif proposé : Final control after the constants are fixed, env unset, >= 200 NULL seeds (about 6 s each); return cfg and bases from a worker and assert they equal candidates.json cfg at the freeze; classify planted-world passes by true lift (known in the synthetic world) rather than Jaccard alone; hash the final report in the freeze.
- [MINOR] `ap_lib.py:245` Registry: format unreadable by the official counter, unregistered reads, undercounts
  - Correctif proposé : Write through the skill's enregistrer() (n_comparaisons, donnees reelles/synthetiques) or add those fields plus the chain; register discovery from mine_50 or assert atoms.json cfg equals M.CFG; add a line for every ad hoc DISC read; carry one line for the >= 17.7 M earlier evaluations.
- [MINOR] `rob_80_robustness.py:83` VAL + OOS statistics are pooled without stratifying by block
  - Correctif proposé : Use a block-stratified estimate (Mantel-Haenszel lift and CMH p with VAL and OOS as strata), or require the condition in each block separately.
- [MINOR] `desc_45_families.py:28` Read-once guards and reported n: OOS can be read descriptively before the confirmatory read; the plan's table gives alerts, not eligible rows
  - Correctif proposé : Require OOS_READ.json in desc_45 for the oos stage; write the *_READ marker before printing or writing any result; check FROZEN_FILES existence before loading SEL labels; put eligible counts and censored shares per block in PLAN section 3 and in the report.

