# Correctifs du 2026-10-06 après la revue à l'aveugle (32 constats)

Tous appliqués avant le gel et avant toute lecture de SELECTION, VALIDATION ou OOS. Référence :
`prefreeze_review_findings.md` (titres) et `prefreeze_review.json` (détail).

## Les 7 MAJOR

| constat | correctif |
|---|---|
| Bootstrap de grappes : tirages sans déclenchement écartés, règle portée par 1 à 4 grappes | `ap_mine.evaluate` : les tirages sans déclenchement comptent contre la règle (p = (tirages ≤ 0 + tirages sans déclenchement + 1) / (B + 1)) ; `val_pass` et `oos_decide` exigent ≥ 5 grappes et ≥ 3 jours de déclenchement ; B = 100 000, plancher signalé |
| Le p hors échantillon ignore le jour | p = max(Fisher, bootstrap de grappes, CMH stratifié par jour) ; `c_dow`, `lv_dow`, `reg_weekend` exclus par le plan ; nombre de jours de déclenchement rapporté ; mondes nuls avec effet de jour (0,4 et 0,8) dans les contrôles |
| Le JSON des contrôles enregistre le CFG du parent | les workers renvoient `cfg` et `bases`, vérifiés identiques, écrits tels quels ; surcharges appliquées avant `prepare_atoms` ; refus d'écraser un fichier existant ; exclusions obligatoires (plus de repli silencieux) |
| Seuils voisins : vérifications sautées en silence | `rob_80` : état par voisin (testé / trop petit / non testable), prochain quantile réellement distinct, `cutoffs = "not_testable"` sans variante ; `rep_90` distingue « non mesurable » d'« échec » |
| Un verdict négatif n'exclut que les gros effets | PLAN §8 et §10 : lifts de rentabilité (× 1,83 / × 2,9 / × 7,0) écrits à côté de la puissance ; scénarios plantés à × 1,83, × 2,2, × 2,9, × 3,0 et support 5 à 8 % ; formulation imposée du verdict négatif ; ×5 déclaré sans puissance |
| INTERESTING est ce que le bruit produit | `ctl_00` compte les INTERESTING sous le nul ; `rep_90` imprime ce taux nul en tête du TOP 20 ; PLAN §10 interdit toute suite sans échantillon prospectif |
| Le script de verdict est hors du gel et s'écarte de PLAN §10 | `rep_90_report.py`, `desc_45_families.py`, `derived/atoms.json`, `tables/FEATURE_INVENTORY.json`, `tables/discovery_summary.json`, `controles/ctl_00_controls.json`, `code/registre.py` ajoutés au gel ; `rep_90` appelle `check_freeze` ; la liste de décision ordonnée de PLAN §10 est implémentée dans `ap_mine.tier` (une seule fonction, utilisée par le rapport ET par les contrôles) ; les cas composite et « sans voisin » sont écrits |

## Les 25 MINOR

| constat | correctif |
|---|---|
| Triples : parent = paire-graine seule ; graines classées avant les filtres ; ex aequo | parent = max des trois sous-paires et des singles ; graines = les 300 meilleures paires AYANT PASSÉ jours, grappes et plafond, tri stable |
| Contrôles : atomes construits avant la surcharge, replis non tracés, faux survivants gonflés | surcharges avant `prepare_atoms` ; exclusions obligatoires ; `bases` du fichier DISCOVERY écrites ; survivants des mondes plantés classés par part de déclenchements dans l'ensemble planté et par lift vrai (probabilités synthétiques) |
| Égalité au facteur 1,10 décidée par float32 | comparaison en float64 avec tolérance 1e-9 |
| Dédup des atomes limitée aux lignes DISC | dédup sur toutes les lignes (features seules) ; jumeaux notés dans `atoms.json` |
| RANK inconnu retombe sur « min » | `ValueError` |
| Trades censurés retirés des moyennes ; IC du net dégénéré à une grappe | `net_censored` rapporté ; `net_ci` et borne 99 % absents sous 5 grappes ; critère net exige ≥ 5 grappes |
| Gel incomplet, registre dépendant de mine_40 | voir MAJOR 7 ; `mine_50` écrit `atoms.json` et enregistre ses propres comptes (`evaluated` compris) |
| Gardes d'étape de `desc_45` contournables | `selection` exige `SELECTION_FREEZE.json`, `oos` exige `OOS_READ.json` au statut `done`, `validation` refusé |
| 23 alertes du régime grossier dans DISC | éligibilité = régime fin (`fine`) dans `ap_data`, `feat_20_history` (issues des priors) et les contrôles ; PLAN §4 |
| Feature LEAK / AMBIGUOUS absente de la matrice ne lève pas | `inv_00` lève, sauf `miss__X` dont X est exclue |
| Statut SAFE par défaut pour 324 features non auditées | statuts `SAFE_PRIOR_AUDIT` (fA, ez, sc, kg), `REVIEWED` (h1 w / c / k / any / régime), `NOT_AUDITED` (lv, x, h1 clés funder et early) ; `rep_90` les imprime ; pas d'atome « manquante » pour NOT_AUDITED |
| Cotation SOL/USD horaire gardée dans trois colonnes | vérifié : clôture de l'heure PRÉCÉDENTE (écart 2e-7 contre `sol_usd_hourly.json`), causale, gardée ; écrit dans l'inventaire |
| Atomes « manquante » pour les features dont la réserve est la manquance | pas d'atome « manquante » pour `SAFE_WITH_CAVEAT` et `NOT_AUDITED` (155 features) ; PLAN §5 |
| Règle « familles différentes » contournée par les copies | paires et triples interdits entre features à \|Spearman\| ≥ 0,97 sur DISCOVERY (239 paires de features) |
| Le monde NUL n'exerce ni l'historique ni l'effet de jour | mondes `NULL_day04`, `NULL_day08`, `NULL_hist` (h1 reconstruites depuis les issues synthétiques via `feat_20_history.build`) ; le contrôle « porte retirée » n'a PAS été fait (écrit ici) |
| Bootstrap sans protection à 1 à 3 grappes, OOS SURVIVOR sans minimum | voir MAJOR 1 |
| B = 2 000 ne résout pas les seuils de Holm | B = 100 000 en VALIDATION et OOS, plancher signalé (`p_boot_floor`) |
| Net d'un survivant biaisé vers le haut | phrase imposée dans `rep_90` (biais 9 à 14 points), borne 99 % sous 35 trades, critère net sur cette borne |
| 12 graines ne certifient pas 5 % ; cfg du parent ; taux de base de repli ; détections partielles | 200 graines nulles ; cfg des workers ; taux de base du fichier DISCOVERY corrigé ; classement par lift vrai |
| Registre : format illisible par le compteur du skill, lectures non enregistrées | `code/registre.py` copié du skill, `ap_lib.registre` écrit par `enregistrer` (chaîne, `n_comparaisons`, `donnees`) ; chaque script enregistre sa lecture ; une ligne pour les ≥ 17,7 M d'évaluations antérieures à ajouter au gel |
| VAL + OOS groupés sans stratification | rapport de taux de Mantel-Haenszel par bloc, p CMH par jour, dans la robustesse, les voisins, la grappe dominante, les labels |
| Lecture unique contournable ; n du plan = alertes | marqueurs `*_READ.json` écrits AVANT tout résultat (statut `reading` puis `done`) ; `mine_50` vérifie la liste des fichiers avant de charger SEL ; PLAN §3 donne les lignes éligibles |
| Composite gardé sur conditions brutes seulement | conditions brutes et plafonnées |
| PLAN.md : 521 colonnes | 530 |
| « Issues mélangées » : aucun script dans code/ | script de l'essai à blanc dans le scratchpad de session, hors dossier d'étude (copie entière, issues permutées entre lignes éligibles) ; comptes des verdicts rapportés dans le bilan |

Non fait, assumé : le contrôle positif « porte de résolution retirée » (fuite volontaire dans
l'historique) ; les contrôles reconstruisent l'historique avec la porte en place seulement.
