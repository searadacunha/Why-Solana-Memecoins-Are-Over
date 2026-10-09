# Audit Pump-Gold : ce que `Solid-Sea/pump-gold-dataset` apporte à alpha_patterns (2026-10-06)

Étude exploratoire. Rien de l'étude confirmatoire n'a été ouvert, aucune donnée TEST lue, aucun
label VALIDATION ou OOS lu ici (DISCOVERY seul, 363 lancements du régime fin). Aucune installation,
aucun wallet, aucun bot. Dépôt lu par l'API GitHub (`gh api`, lecture seule) et **non cloné**.

## 1. Ce que le dépôt apporte réellement

Contenu exact (arborescence au 2026-08-19, dernier commit) : `README.md` (2,3 Ko), `export_dataset.py`
(1,2 Ko), `rf_classifier_eval.py` (1,8 Ko), `.zenodo.json`, `LICENSE` (CC BY 4.0) et
`pump_gold_dataset_core.csv.gz` (83 Mo, 1 306 082 tokens). Auteurs : deux lycéens de Dalian,
soumission « ICDM 2026 Teen Research Symposium » ; 0 étoile ; le papier compagnon n'est pas dans le
dépôt ; les scripts de reproduction « disponibles sur demande ». Source brute : un export Dune /
Kaggle de pump.fun daté 2025-02 (17 M de trades).

Schéma, une ligne par token, 10 colonnes publiées (12 dans le script d'export, `total_base` et
`n_price` en plus) :

| colonne | définition | fenêtre |
|---|---|---|
| `buy_count`, `sell_count` | nombre d'achats, de ventes | VIE ENTIÈRE du token |
| `unique_wallets` | wallets acheteurs + vendeurs distincts | vie entière |
| `total_quote_lamports` | volume cumulé en SOL | vie entière |
| `avg_swap_size` | total_quote / (buy + sell) | vie entière |
| `pmin`, `pmax` | min et max du chemin de prix | vie entière |
| `is_golden` | pmax ≥ 10 × pmin (0,25 % des tokens) | vie entière |
| `is_dead` | pmax < 2 × pmin (93,4 %) | vie entière |

Ce qu'il n'y a PAS, malgré le titre « wash-trading features » : aucune variable de wash trading, de
concentration, de flux, de temporalité ni de coordination ; aucune donnée par wallet, par trade, de
financement, de timing ou de bundle. Les cinq « features » sont des agrégats cumulés sur toute la vie
du token, calculés sur la même fenêtre que le label (pmax inclus) : un token qui monte attire plus
d'achats, donc `buy_count` « prédit » `is_golden` par construction. Le `rf_classifier_eval.py` entraîne
une forêt sur ces cinq totaux : c'est une fuite totale, pas une détection précoce. Les lignes
« Golden : 64,9 achats en moyenne contre 6,2 » du README décrivent la conséquence du mouvement, pas sa
cause.

Verdict : le dépôt vaut comme **liste de concepts** (intensité de wash trading, diversité économique
des wallets, pression vendeuse, taille moyenne des swaps, seuil « golden » ≥ 10×), pas comme source de
features ni comme dataset de comparaison : population différente (1,3 M de tokens de février 2025,
bundle ou non, 0,25 % de golden), agrégats vie entière inalignables sur un instant de décision,
labels de survie. Cloner les 83 Mo n'apporterait rien d'exploitable avant le mouvement.

## 2. Ce qui était déjà présent (étape 1, sans cloner)

Les cinq concepts du dépôt, ramenés à notre fenêtre de décision (création → alerte − 1 s, trades
externes au bundle), existaient déjà dans les 530 features :

| concept Pump-Gold | déjà dans alpha_patterns | statut |
|---|---|---|
| buy_count, sell_count | `m_buys`, `m_sells`, `ez_buys_5s`, `ez_buys_10s`, `m_buys_10s` | already_covered |
| unique_wallets | `m_buyers`, `m_sellers`, `ez_n_buyers`, `ez_n_early`, `ef_nb_buyers_log` | already_covered |
| total_quote | `m_buy_sol`, `m_sell_sol`, `ez_sol_early_total`, `ez_sol_outside` | already_covered |
| avg_swap_size | `m_buy_median`, `m_buy_max`, `ef_nb_median_buy_sol` | already_covered |
| pmin / pmax | labels `mfe_3600`, `mae_3600` (issue, jamais une feature) ; pré-alerte : `ef_px_*`, `p_price_max_ratio` | already_covered (côté pré-alerte) / label (côté post) |
| golden ≥ 10×, dead < 2× | nos cibles ×2 / ×3 / ×5 en 1 h depuis + 5 s ; ×10 en 1 h : 9 succès au plus sur DISCOVERY, non testable | partially_covered |
| ratio achats / ventes | `m_buy_sell_ratio`, `ef_px_down_share` | already_covered |
| concentration des acheteurs | `m_top_buyer_share`, `ez_sol_hhi`, `ez_top1_share`, `b_hhi` (bundle) | already_covered |
| wallets répétés sur plusieurs lancements | `e_prior_launches_*`, `ef_repeat_buyer_share`, `h1_e_*`, `kg_*` | already_covered |
| wash trading au sens strict (allers-retours, achats répétés d'un même wallet, tailles identiques) | rien par wallet avant l'alerte | genuinely_new |
| diversité économique (SOL par wallet, Gini par wallet, apparent / réel) | `m_top_buyer_share` seulement | partially_covered |
| coordination artificielle des externes (même slot, même taille, payeur ≠ trader, cosignatures) | `x_motif_*` (snipers seulement), `b_core_signers` (bundle seulement) | genuinely_new pour les acheteurs EXTERNES |
| transition activité initiale → organique | `m_accel`, `ef_nb_late_sol_share` | partially_covered |

Conclusion de l'étape 1 : les features publiées n'apportent rien ; les CONCEPTS « wash trading » et
« diversité économique », appliqués aux acheteurs externes de la fenêtre pré-alerte, n'étaient pas
mesurés par wallet. C'est ce qui a été construit, sans cloner.

## 3. Les features nouvelles (35 `pg_*`, `code/feat_27_pumpgold.py`)

Toutes calculées depuis les fenêtres brutes déjà sur disque (chaque transaction création → alerte,
parsées par `fparse.py` de l'étude forensique), trades EXTERNES = hors snipers du bundle et hors
créateur, achats du slot 0 exclus, enregistrements de temps de bloc > alerte − 1 s retirés AVANT tout
calcul. Dictionnaire : `derived/feat_pumpgold_dictionary.md`. Variante à alerte − 2 s pour le test
d'observabilité. Classement par redondance (|Spearman| max avec une feature existante, lignes
DISCOVERY, ≥ 30 lignes communes) :

| classe | n | features |
|---|---|---|
| copie d'une feature existante (ρ ≥ 0,90) : already_covered | 8 | `pg_ext_over_bundle` (1,00 `m_buy_sol`), `pg_sell_pressure` (1,00 `m_buy_sell_ratio`), `pg_core_sell_over_ext_buy` (1,00 `m_core_sell_sol`), `pg_buy_slot_gap_cv` (0,99 `x_burst_pre`), `pg_n_ext_trades` (0,98 `m_buys`), `pg_sell_buy_count_ratio` (0,95 `ef_px_down_share`), `pg_small_buy_share` (0,94 `m_buy_median`), `pg_big_buy_sol_share` (0,90 `m_buy_max`) |
| partiellement couverte (0,80 ≤ ρ < 0,90) | 9 | `pg_tx_per_wallet`, `pg_roundtrip_wallets`, `pg_roundtrip_share`, `pg_pingpong_10s` (toutes ≈ `m_sellers`), `pg_wallets_per_sol`, `pg_sol_per_buyer` (≈ `m_buy_sol`), `pg_top5_buyer_share` (≈ `m_top_buyer_share`), `pg_apparent_per_wallet`, `pg_fresh_ata_share` |
| réellement nouvelle (ρ < 0,80) | 18 | `pg_buys_per_buyer` (0,50), `pg_repeat_buyer_sol_share` (0,51), `pg_max_buys_one_wallet` (0,54), `pg_roundtrip_sol_share` (0,77), `pg_seller_buyer_overlap` (0,66), `pg_same_size_share` (0,33), `pg_modal_size_share` (0,61), `pg_size_cv` (0,73), `pg_buy_gini` (0,77), `pg_buy_run_max` (0,63), `pg_novelty_2nd_half` (0,64), `pg_size_shift` (0,29), `pg_sync_same_size_pairs` (0,69), `pg_same_slot_max_buyers` (0,71), `pg_payer_mismatch_share` (0,37), `pg_modal_prio_share` (0,79), `pg_multisig_share` (0,39), `pg_sell_first` (0,23 mais 99 % de zéros : inutilisable) |

**17 features réellement nouvelles et utilisables.** Aucune ne demande de nouvelle donnée (classe A :
calculées, fichier `derived/feat_pumpgold.jsonl.gz`, non intégrées à `X.npz`).

### Table d'extraction (étape 3)

Colonnes : FEATURE_ID | FAMILY | SOURCE | DESCRIPTION | OBSERVABLE_AT_ALERT | LOOKAHEAD_RISK |
ALREADY_IN_ALPHA_PATTERNS | POTENTIAL_NEW_SIGNAL | EXPECTED_DIRECTION | ECONOMIC_INTUITION.
OBSERVABLE : « − 1 s » = construit sur les blocs ≤ alerte − 1 s ; en direct il faut relire la fenêtre
après l'alerte (médiane 71 `getTransaction`), donc décision à + 5 s au plus tôt. LOOKAHEAD : part des
alertes dont la valeur change quand la coupure recule d'une seconde (la dernière seconde avant l'alerte
pèse lourd : une fenêtre de 12 s en médiane).

| FEATURE_ID | FAMILY | SOURCE | DESCRIPTION | OBS. | LOOKAHEAD (chg − 2 s) | DÉJÀ | NOUVEAU | DIRECTION | INTUITION |
|---|---|---|---|---|---|---|---|---|---|
| pg_buys_per_buyer | wash | concept buy_count / unique_wallets | achats externes par acheteur distinct | − 1 s | faible (24 %) | non (ρ 0,50) | oui | + si volume simulé attire, − si wash pur | un bot qui rachète en boucle gonfle le volume sans demande réelle |
| pg_repeat_buyer_sol_share | wash | idem | part du SOL externe venant de wallets à ≥ 2 achats | − 1 s | faible (24 %) | non | oui | ± | idem, pondéré en SOL |
| pg_max_buys_one_wallet | wash | idem | max d'achats d'un seul wallet externe | − 1 s | très faible (5 %) | non | oui | ± | un wallet « moteur » |
| pg_roundtrip_sol_share | wash | concept sell_count | SOL vendu par des wallets qui avaient acheté / SOL acheté | − 1 s | moyen (40 %) | partiel (`m_sellers` 0,77) | oui | − | allers-retours = wash ou scalp précoce, pas de détention |
| pg_seller_buyer_overlap | wash | idem | vendeurs qui avaient acheté / vendeurs | − 1 s | faible (15 %) | non (0,66) | oui | − | pur recyclage |
| pg_same_size_share | wash / coordination | concept avg_swap_size | part des achats dont la taille (1e-3 SOL) est répétée | − 1 s | fort (55 %) | non (0,33) | oui | ± | tailles identiques = un même script ; direction inconnue |
| pg_modal_size_share | wash | idem | part des achats à la taille modale | − 1 s | fort (56 %) | non (0,61) | oui | − | une seule taille = un seul opérateur |
| pg_size_cv | diversité | idem | CV des tailles d'achat | − 1 s | fort (56 %) | non (0,73) | oui | + | tailles variées = acheteurs variés |
| pg_buy_gini | diversité | concept unique_wallets | Gini du SOL par acheteur | − 1 s | fort (56 %) | non (0,77) | oui | − | demande concentrée = fragile |
| pg_buy_run_max | flux | ordre des trades | plus longue suite d'achats sans vente | − 1 s | faible (13 %) | non (0,63) | oui | + | demande qui ne rencontre pas d'offre |
| pg_novelty_2nd_half | transition | wallets par moitié | part des achats de 2e moitié par des wallets neufs | − 1 s | faible (14 %) | non (0,64) | oui | + | relais organique après l'amorce |
| pg_size_shift | transition | tailles par moitié | taille médiane 2e moitié / 1re | − 1 s | fort (65 %) | non (0,29) | oui | + | les tailles montent quand des humains suivent |
| pg_sync_same_size_pairs | coordination | même slot, même taille | paires d'achats même slot, wallets différents, taille à 5 % | − 1 s | faible (11 %) | non (0,69) | oui | − (ou + si « vrai » bundle de demande) | un script qui achète depuis N wallets |
| pg_same_slot_max_buyers | coordination | même slot | max d'acheteurs distincts dans un slot | − 1 s | très faible (2 %) | non (0,71) | oui | ± | rafale coordonnée |
| pg_payer_mismatch_share | coordination | signer ≠ trader | part des trades externes payés par un autre wallet | − 1 s | faible (16 %) | non (0,37) | oui | − | payeur unique derrière plusieurs « acheteurs » (78 % de zéros) |
| pg_modal_prio_share | coordination | frais de priorité | part des trades au frais de priorité modal | − 1 s | fort (63 %) | non (0,79) | oui | − | même configuration de bot |
| pg_multisig_share | coordination | n_sig ≥ 2 | part des trades externes cosignés | − 1 s | moyen (34 %) | non (0,39) | oui | + ? | relais ou payeur séparé ; 55 % de zéros |
| pg_tx_per_wallet, pg_roundtrip_wallets, pg_roundtrip_share, pg_pingpong_10s | wash | buy+sell / wallets | intensité d'allers-retours | − 1 s | 13 à 54 % | partiel (≈ `m_sellers`) | faible | − | idem roundtrip |
| pg_wallets_per_sol, pg_sol_per_buyer, pg_apparent_per_wallet | diversité | quote / wallets | SOL par wallet, apparent / réel | − 1 s | 56 à 64 % | partiel (≈ `m_buy_sol`) | faible | ± | volume apparent sans diversité |
| pg_top5_buyer_share, pg_fresh_ata_share | diversité | concentration, comptes neufs | top-5, comptes ouverts par acheteur | − 1 s | 56 % | partiel | faible | − | concentration |
| 8 copies (section 3) | | | | | | oui | non | | |

## 4. Tests de sanité (étape 7, DISCOVERY seul : `tables/pumpgold_sanity.json`)

- Observations : 1 656 alertes sur 1 657 pour 31 features (une alerte sans achat externe) ;
  `pg_seller_buyer_overlap` 1 315 (pas de vendeur), `pg_novelty_2nd_half` et `pg_size_shift` 1 473
  (fenêtre trop courte pour deux moitiés), `pg_buy_slot_gap_cv` 1 609.
- Manquants par bloc : identiques entre blocs (0 à 21 %), aucune dérive de couverture.
- Zéros : `pg_sell_first` 99 % (rejetée), `pg_core_sell_over_ext_buy` 88 %, `pg_payer_mismatch_share`
  78 %, `pg_repeat_buyer_sol_share` 65 %, `pg_multisig_share` 55 %, `pg_big_buy_sol_share` 50 %,
  `pg_roundtrip_*` 41 %.
- Stabilité temporelle (médianes par bloc, features seules) : stables pour la plupart ; dérives à
  noter : `pg_sell_pressure` 0,16 → 0,58 (plus de ventes pré-alerte en septembre), `pg_same_size_share`
  0,32 → 0,43, `pg_multisig_share` 0 → 0,02, `pg_buy_run_max` 17 → 12 (VAL). Un seuil appris sur
  DISCOVERY ne vaut donc pas la même chose plus tard pour ces quatre-là.
- Observabilité : toutes construites sur des blocs ≤ alerte − 1 s (vérifié dans le constructeur :
  les enregistrements après la coupure sont retirés avant tout calcul). Mais 50 à 65 % des valeurs
  changent quand la coupure recule d'une seconde : la dernière seconde contient en médiane 8 % des
  trades externes. En direct, la feature doit être recalculée à l'instant réel de décision.
- Corrélation triviale avec les labels (DISCOVERY, 363 lignes, 91 / 40 / 9 succès) : AUC entre 0,43
  et 0,61 sur ×2 et ×3 ; lift plafonné du quintile haut au plus 1,37 (×2, `pg_buy_run_max`) et 1,81
  (×3, `pg_same_size_share`). `pg_same_size_share` affiche 0,79 d'AUC sur ×5 : 9 succès, non
  interprétable. Rien de fort.

## 5. Criblage ciblé (étape 6, DISCOVERY seul : `tables/pumpgold_screen.json`)

Matrice étendue en mémoire (famille WASH), 257 atomes `pg_*` sur 3 357, paires et triples contenant
au moins un atome `pg_*`, mêmes filtres que le plan (support, Wilson, moitiés, parents, ≥ 5 jours,
≥ 5 grappes, plafond par grappe). Même criblage sur les labels DISCOVERY permutés au hasard :

| cible | évalué (paires + triples) | passent, labels réels | passent, labels mélangés | meilleur lift réel | meilleur lift mélangé |
|---|---|---|---|---|---|
| ×2 | 674 393 + 54 715 | 10 313 | 11 185 | × 2,87 (n 25) | × 2,78 (n 33) |
| ×3 | 674 393 + 45 378 | 10 798 | 5 685 | × 4,19 (n 26) | × 4,03 (n 27) |
| ×5 | 674 393 + 45 259 | 14 297 | 21 973 | × 11,3 (n 25) | × 9,7 (n 25) |

Les nouvelles features, seules ou combinées, ne se distinguent pas du bruit sur DISCOVERY : mêmes
comptes, mêmes lifts maximaux. C'est attendu (DISCOVERY génère) et ce n'est pas un verdict : seul un
passage VALIDATION → OOS d'une liste gelée peut trancher. Les atomes `pg_*` les plus utilisés par les
règles réelles : `pg_buy_run_max`, `pg_same_size_share`, `pg_buys_per_buyer`, `pg_buy_gini`,
`pg_big_buy_sol_share` ; partenaires : funding (4 958 règles ×2), temporel, bundle. Les mêmes atomes
dominent aussi les règles sur labels mélangés (ce sont les atomes à grand support).

## 6. Les 20 hypothèses prioritaires (étape 5)

Scores 1 à 5 par critère, à ma main : N nouveauté, O observabilité, É plausibilité économique,
F fréquence, I interaction forte possible, R robustesse au seuil, T signal simple tradable. Classe A
= calculable maintenant. Les « indices DISCOVERY » sont descriptifs et au niveau du bruit.

| # | hypothèse (règle candidate) | N | O | É | F | I | R | T | total | classe | indice DISCOVERY |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Demande externe RÉELLE : `pg_buys_per_buyer` bas ET `pg_buy_gini` bas ET `m_buy_sol` haut (volume sans wash ni concentration) | 4 | 4 | 5 | 3 | 5 | 3 | 4 | 28 | A | quintile haut buys_per_buyer : lift 1,34 (sens contraire !) |
| 2 | Relais organique : `pg_novelty_2nd_half` haut ET `pg_size_shift` > 1 ET `m_accel` > 1 | 4 | 4 | 5 | 3 | 5 | 2 | 4 | 27 | A | size_shift > 1,31 dans un triple à 69 % (n 26), bruit-compatible |
| 3 | Suite d'achats sans vente : `pg_buy_run_max` haut ET `m_buys_10s` haut | 3 | 5 | 4 | 4 | 4 | 3 | 4 | 27 | A | ×3 : 46 % (n 26, 9 grappes), le mélangé fait pareil |
| 4 | Wash + concentration : `pg_repeat_buyer_sol_share` haut ET `m_top_buyer_share` haut (demande d'un seul wallet qui rachète) → filtre négatif | 4 | 4 | 5 | 3 | 5 | 3 | 3 | 27 | A | lift 1,16 à 1,31 seul, direction + (contre-intuitif) |
| 5 | Script multi-wallets : `pg_sync_same_size_pairs` haut ET `pg_same_size_share` haut ET `g_early_funders_shared` > 0 (I : wallets « indépendants » même financeur) | 5 | 5 | 5 | 2 | 5 | 2 | 3 | 27 | A | same_size_share > 0,4 revient dans les tops ×3 / ×5 réels ET mélangés |
| 6 | Allers-retours précoces : `pg_roundtrip_sol_share` haut ET `pg_seller_buyer_overlap` haut → filtre négatif (C : wash + funding : ET `f_n_funders` bas) | 4 | 4 | 4 | 3 | 4 | 3 | 3 | 25 | A | ×3 lift plafonné 1,40 et 1,46 (sens +, contre-intuitif) |
| 7 | Cosignatures externes : `pg_multisig_share` > 0 ET `w_early_fresh` haut | 5 | 4 | 3 | 2 | 4 | 2 | 4 | 24 | A | AUC 0,58 / 0,59 / 0,61, lift 1,30 / 1,50 ; 55 % de zéros |
| 8 | Payeur caché : `pg_payer_mismatch_share` > 0 ET `pg_same_slot_max_buyers` haut (D : concentration + identité) | 5 | 4 | 4 | 1 | 4 | 2 | 3 | 23 | A | 78 % de zéros, AUC 0,52 |
| 9 | Volume apparent sans diversité (H) : `pg_apparent_per_wallet` haut ET `m_buyers` bas | 3 | 4 | 4 | 3 | 4 | 3 | 3 | 24 | A | AUC 0,55, lift 1,02 |
| 10 | Bot unique : `pg_modal_prio_share` haut ET `pg_modal_size_share` haut → filtre négatif | 4 | 3 | 4 | 3 | 4 | 2 | 3 | 23 | A | modal_size quintile haut : lift 0,67 (négatif, cohérent) |
| 11 | Wash + rapidité (B) : `pg_buys_per_buyer` haut ET `m_rate` haut | 3 | 4 | 4 | 3 | 4 | 3 | 3 | 24 | A | bruit |
| 12 | Diversité des tailles : `pg_size_cv` haut ET `ez_n_buyers` haut | 3 | 4 | 3 | 4 | 3 | 3 | 4 | 24 | A | AUC 0,57 ×2, 0,37 ×5 (instable) |
| 13 | Créateur + flux + qualité (J) : `h_creator_prior_creates` bas ET `pg_novelty_2nd_half` haut ET `w_early_log_prior_n` haut | 3 | 4 | 4 | 2 | 5 | 2 | 3 | 23 | A | non criblé en triple avec creator |
| 14 | Bundle + post-bundle (K) : `b_core_supply` haut ET `m_core_exit_share` bas ET `pg_buy_run_max` haut | 2 | 5 | 4 | 3 | 4 | 3 | 3 | 24 | A | partenaires bundle 2 183 règles ×2, bruit |
| 15 | Répétition des mêmes wallets (E) : `h1_e_known_share` haut ET `pg_same_size_share` haut | 3 | 4 | 3 | 3 | 4 | 2 | 3 | 22 | A | ×5 : 26 % (n 27) sur 9 succès, inexploitable |
| 16 | Wash + funding (C) : `pg_max_buys_one_wallet` haut ET `g_early_linked` > 0 | 4 | 3 | 4 | 2 | 4 | 2 | 2 | 21 | A | bruit |
| 17 | Rafale : `pg_same_slot_max_buyers` haut ET `x_burst_pre` haut (F synchronisation) | 2 | 5 | 3 | 3 | 3 | 3 | 3 | 22 | A | AUC 0,54 |
| 18 | Taille + diversité réelle (G) : `pg_sol_per_buyer` haut ET `pg_buy_gini` bas | 2 | 4 | 4 | 3 | 4 | 3 | 3 | 23 | A | partiel (≈ m_buy_sol) |
| 19 | Transition L inverse : `pg_novelty_2nd_half` bas ET `pg_modal_size_share` haut → filtre négatif « tout le flux est le même script » | 4 | 4 | 4 | 3 | 4 | 2 | 3 | 24 | A | novelty quintile bas : lift 1,07 (rien) |
| 20 | Golden ≥ 10× à 1 h (concept du dépôt) comme cible auxiliaire | 1 | 5 | 2 | 1 | 1 | 1 | 1 | 12 | D | ≤ 9 succès sur DISCOVERY : pas de puissance |

Classes : 19 hypothèses en A (calculables maintenant avec `derived/feat_pumpgold.jsonl.gz` et la
matrice), 0 en B, 0 en C, 1 en D (la cible ×10). Aucune donnée externe n'est nécessaire.

## 7. Les patterns composites à tester en premier (étape 5, recommandation)

À tester dans le cadre du plan (gel puis VALIDATION, OOS), jamais en lecture libre :

1. Demande réelle : wash bas + concentration basse + volume externe haut (#1).
2. Relais organique : nouveauté 2e moitié + hausse des tailles + accélération (#2).
3. Suite d'achats sans vente + rapidité (#3).
4. Script multi-wallets (mêmes tailles, même slot) + financeur partagé des acheteurs (#5), en filtre
   négatif ET en filtre positif (un « bundle de demande » peut précéder un pump organisé).
5. Allers-retours + peu de financeurs (#6), filtre négatif.
6. Cosignatures externes + wallets neufs (#7).
7. Bot unique (frais et tailles modaux) comme filtre négatif (#10).
8. Bundle + absence de sortie des snipers + suite d'achats (#14).
9. Créateur sans historique + relais organique + wallets expérimentés (#13).
10. Volume apparent sans diversité (#9), filtre négatif.

Honnêteté sur ce qu'on peut en attendre : les contrôles de la chaîne (bilan du 06/10) ne voient un
effet qu'à partir de × 2,9 le taux de base ; aucune de ces features n'a plus de 1,5 de lift plafonné
seule sur DISCOVERY, et leurs combinaisons font exactement ce que font des labels mélangés.

## 8. Ce qui ne vaut pas la peine d'être testé

- Les colonnes du dépôt elles-mêmes (agrégats vie entière) : fuite totale, inalignables sur l'alerte.
- Cloner le CSV comme jeu de comparaison : population et fenêtre incomparables, labels de survie.
- Les 8 copies (`pg_ext_over_bundle`, `pg_sell_pressure`, `pg_core_sell_over_ext_buy`,
  `pg_buy_slot_gap_cv`, `pg_n_ext_trades`, `pg_sell_buy_count_ratio`, `pg_small_buy_share`,
  `pg_big_buy_sol_share`) : déjà dans la matrice sous un autre nom.
- `pg_sell_first` (99 % de zéros), `pg_core_sell_over_ext_buy` (88 %).
- La cible ×10 en 1 h (≤ 9 succès).
- Les hypothèses 15 à 18 : partiellement couvertes ou sans indice, à garder seulement si les 17
  features entrent dans la matrice (elles y seront criblées mécaniquement de toute façon).

## 9. Tests effectués et fichiers

Tests : construction à deux coupures (− 1 s, − 2 s) sur 1 657 fenêtres ; sanité par feature
(observations, manquants par bloc, zéros, quantiles, médianes par bloc, moitiés DISCOVERY, redondance
Spearman ≥ 30 lignes, AUC et lifts plafonnés des quintiles sur DISCOVERY, part de changement à − 2 s) ;
criblage ciblé DISCOVERY réel contre mélangé (3 cibles, 2,2 M d'évaluations enregistrées au registre,
données réelles et synthétiques à part). Aucune lecture de SELECTION, VALIDATION ou OOS.

Fichiers créés : `code/feat_27_pumpgold.py`, `code/san_28_pumpgold.py`, `code/scr_29_pumpgold.py` ;
`derived/feat_pumpgold.jsonl.gz`, `derived/feat_pumpgold_cut2.jsonl.gz`,
`derived/feat_pumpgold_dictionary.md`, journaux `derived/feat_pumpgold*.log` ;
`tables/pumpgold_sanity.json`, `tables/pumpgold_screen.json`, ce rapport. `code/ap_mine.py` a reçu un
paramètre optionnel `allowed3` (masque du troisième atome d'un triple, défaut inchangé). La matrice
`X.npz`, le plan et les règles de sélection n'ont pas été modifiés.

## 10. Prochaine action recommandée

Décision à prendre avant le gel, pas après : ajouter ou non les 17 features nouvelles (famille WASH)
à la matrice. Pour : elles mesurent une chose que les 530 ne mesurent pas (wash trading et
coordination des acheteurs EXTERNES, par wallet) ; coût nul ; aucune lecture hors échantillon n'a eu
lieu, le plan peut être amendé proprement (§2, §5). Contre : elles ajoutent ~170 atomes à 3 100 et donc
du bruit à la sélection ; sur DISCOVERY elles ne montrent rien que le bruit ne montre. Si on les
ajoute, rejouer `mine_40`, les contrôles (cfg inchangée, nouveaux atomes), puis gel → VALIDATION → OOS
en une lecture chacun, comme prévu. Ne rien lire de VALIDATION ou OOS avant.
