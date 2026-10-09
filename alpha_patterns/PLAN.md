# alpha_patterns : plan de la recherche exploratoire

Écrit le 2026-10-05, révisé le 2026-10-06 après la revue à l'aveugle du code (32 constats) et avant
toute lecture des blocs VALIDATION et OOS. Recherche EXPLORATOIRE, séparée de l'étude confirmatoire
gelée. Rien n'est lu ni écrit dans `WSMO-bundle-outcomes` (continuation_distribution,
pre_alert_transfers). Aucun `.env`, aucun appel réseau, aucun trading, pas de n8n. Aucun résultat
d'ici ne va vers une étude confirmatoire. Les écarts après le gel vont dans `ECARTS.md` (hors gel).

## 1. Question

Existe-t-il une règle observable à l'alerte (environ 12 s après la création du token), reproductible
sur plusieurs lancements et plusieurs opérateurs, assez fréquente, et dont l'espérance reste positive
après coûts, qui prédit un ×2, ×3 ou ×5 en 1 h depuis une entrée à alerte + 5 s ?

## 2. Données et limites connues d'avance

- Population : les 1 657 alertes du snapshot gelé du 2026-09-29 11:23 UTC (2026-08-21 au 2026-09-29).
  Ce sont toutes des bundle snipes (≥ 4 wallets ≥ 5 SOL dans le slot de création). Aucun lancement
  non bundle n'a de prix : la comparaison bundle / non bundle est impossible ici.
- Rien après le snapshot n'est lu : ces alertes appartiennent au TEST de l'étude confirmatoire.
- Le snapshot a déjà été lu par une dizaine d'études (≥ 17,7 M d'évaluations de règles, plus la
  recherche de signal du 02/10 dont aucun candidat n'a passé l'OOS). Aucun bloc n'est vierge. Le
  mieux qu'on puisse obtenir ici est « répliqué dans le temps à l'intérieur du snapshot » ; la seule
  confirmation propre est prospective.
- Features : 547 colonnes, dont 530 calculées par les études précédentes ou par `feat_20_history.py` et
  `feat_25_derived.py`, et 17 ajoutées le 2026-10-06 (`feat_27_pumpgold.py`, familles WASH et XFLOW :
  wash trading, diversité, flux et coordination des acheteurs EXTERNES de la fenêtre pré-alerte,
  concepts du dépôt Pump-Gold ; audit `tables/PUMP_GOLD_FEATURE_AUDIT_2026-10-06.md`), toutes coupées
  à l'alerte − 1 s (inventaire : `tables/FEATURE_INVENTORY.md`). Les 17 ont aussi une version à
  alerte − 2 s pour les coupures de robustesse. Ajout décidé par Benjamin avant tout gel et avant toute
  lecture de SELECTION, VALIDATION ou OOS.
  24 sont exclues avant toute lecture de label (`derived/feature_exclusions.json`) : 9 fuites et
  12 ambiguës (drapeau « hub » connu seulement a posteriori), plus `c_dow`, `lv_dow`, `reg_weekend`
  (cinq semaines ne peuvent pas identifier un effet de jour de semaine). Les features signalées avec
  réserve ou jamais auditées (`SAFE_WITH_CAVEAT`, `NOT_AUDITED`) n'ont pas d'atome « manquante ».
- Observabilité en direct : les features qui balaient la fenêtre jusqu'à l'alerte − 1 s demandent des
  lectures RPC après l'alerte (médiane 71 `getTransaction`), celles de financement 1 à 3 s de plus.
  L'entrée à + 5 s est donc une hypothèse ; la sensibilité à + 15 s est mesurée.

## 3. Blocs temporels (fixés sur le nombre d'alertes, sans regarder d'issue)

| bloc | période (UTC) | alertes | lignes éligibles (régime fin, entrée + 5 s, fenêtre 1 h observée) | rôle |
|---|---|---|---|---|
| DISCOVERY | < 2026-09-07 | 643 | 363 | génération mécanique des règles |
| SELECTION | 2026-09-07 → 09-15 | 372 | 249 | choix mécanique des candidats, puis gel |
| VALIDATION | 2026-09-15 → 09-22 | 292 | 232 | une lecture de la liste gelée |
| OOS | 2026-09-22 → 09-29 11:23 | 350 | 295 | test final, une lecture |

Les fenêtres non observées (309 lignes avec entrée) sont des trous de relevé de la machine, communs à
tous les tokens suivis au même moment : la censure ne dépend pas de l'issue (vérifié par la revue).
Le code refuse de charger les labels VALIDATION sans `SELECTION_FREEZE.json` intact, et les labels
OOS sans `VALIDATION_READ.json` (`ap_lib.allowed_blocks`) ; les lectures descriptives
(`desc_45_families.py`) viennent après les marqueurs de lecture unique.

## 4. Labels (fixés avant tout taux)

- Seules les alertes du régime de relevé fin (après 2026-08-25 21:47 UTC, un relevé toutes les 5 s
  pendant 180 s) sont éligibles : les 23 alertes du régime à 45 s qui avaient par hasard un relevé
  dans [5 s, 15 s] sont retirées (revue du 05/10 : leurs labels ne se mesurent pas pareil).
- Entrée : premier prix lu dans [5 s, 15 s] après l'alerte (prix spot, pas un fill).
- Y2, Y3, Y5 : deux relevés consécutifs ≥ k × le prix d'entrée dans l'heure qui suit l'entrée.
  Un seul relevé au-dessus ne compte pas (un pic isolé n'est pas vendable).
- Fenêtre non observée (trou de relevé > 135 s) : censurée, jamais comptée comme échec. La règle de
  couverture est décidée avant de regarder les prix.
- Variantes de robustesse seulement : relevé unique, 30 min, 2 h, entrée à + 15 s.
- Trade attaché à chaque label, déclaré d'avance : achat à + 5 s, prise de profit à k× vendue au
  relevé SUIVANT (un bot qui interroge puis vend), pas de stop, sortie au temps à 1 h. Modèle de coûts
  de `post_detection_edge/code/trade.py` inchangé (1 % par jambe, 0,005 SOL par transaction, impact
  de prix à produit constant, K = 1,39e10). Taille principale 500 $. Les trades censurés par la règle
  de couverture plus stricte de `trade.py` sont comptés à part (`net_censored`).
- Sur DISCOVERY (363 lignes) : taux de base et seuil de rentabilité de ce trade écrits dans
  `tables/discovery_summary.json`. Avec les taux du 05/10 (386 lignes), il fallait 45 % de réussite
  sur le ×2 (lift × 1,83), 33 % sur le ×3 (× 2,9), 20 % sur le ×5 (× 7,0).

## 5. Génération mécanique des règles (DISCOVERY)

- Atome : `feature <= seuil`, `feature > seuil` (seuils aux quantiles 20, 35, 50, 65, 80 % de la
  distribution DISCOVERY de la feature, sans issue) ou `feature manquante` (sauf features avec
  réserve ou non auditées). Support entre 25 lignes et 95 % du bloc. Atomes aux déclenchements
  identiques sur TOUTES les lignes dédupliqués (features seules) ; les jumeaux sont notés.
- Règle : conjonction de 1 à 3 atomes de FAMILLES DIFFÉRENTES (funding, coordination, bundle,
  acteurs, clusters, créateur, temporel, sortie, prix), jamais deux copies d'une même mesure
  (|Spearman| ≥ 0,97 sur DISCOVERY, features seules, ≥ 30 lignes communes). Paires : toutes.
  Triples : les 300 meilleures paires AYANT PASSÉ tous les filtres, étendues par un atome d'une
  troisième famille.
- Passe DISCOVERY si : ≥ 25 déclenchements ; borne basse de Wilson (95 % unilatéral) de la précision
  au-dessus du taux de base ; précision au-dessus du taux de base dans chaque moitié temporelle
  (≥ 8 déclenchements chacune) ; pour une paire ou un triple, précision ≥ 1,10 × le meilleur de
  TOUS ses parents (singles et sous-paires), comparaison en double précision ; déclenchements sur
  ≥ 5 jours et ≥ 5 grappes distincts.
- Plafond par grappe : dans le calcul de l'évidence, une grappe (un opérateur) compte au plus pour
  3 déclenchements, pondérés par son propre taux de réussite. La borne basse de Wilson de cette
  précision plafonnée doit aussi dépasser le taux de base plafonné (support plafonné ≥ 12). Un seul
  opérateur ne peut donc pas porter une règle.
- Toute règle qui passe est écrite dans `registre/disc_rules_<cible>.jsonl.gz` ; le nombre de règles
  évaluées est écrit dans le registre chaîné `registre/tests.jsonl` (format du skill etude-gelee,
  `code/registre.py`), avec la configuration.

## 6. Sélection mécanique (SELECTION) et gel

- Sur le bloc SELECTION seul : ≥ 12 déclenchements (support plafonné ≥ 8), précision au-dessus du
  taux de base du bloc, brute et plafonnée.
- Classement par le PIRE des deux blocs : min(DISCOVERY, SELECTION) de la borne basse de Wilson
  (90 % unilatéral) de la précision plafonnée divisée par le taux de base plafonné. Déduplication
  gloutonne (Jaccard des déclenchements ≥ 0,5). 10 règles par cible.
- Un composite par cible : arbres boostés de profondeur 3 ajustés sur DISCOVERY seul, règle « score ≥
  85e centile des scores SELECTION », gardé s'il satisfait les mêmes conditions (brutes et
  plafonnées). Un composite n'a pas de seuils voisins : il ne peut pas devenir CANDIDAT EXPLOITABLE.
- Le classement, le plafond et les supports minimaux ont été choisis sur contrôles synthétiques
  seulement (section 8), avant toute lecture d'un label SELECTION, VALIDATION ou OOS. Variantes
  essayées le 05/10 : classement sur SELECTION seul, groupé, pire bloc ; avec et sans plafond ;
  supports 25/12 et 35/20 ; avec et sans triples. Les triples sont gardés (demande d'interactions à
  trois), bien que les contrôles, dont la règle plantée est une paire, ne montrent aucun gain.
- Gel : `SELECTION_FREEZE.json` (sha256 de la liste, des vecteurs de déclenchement, des atomes, des
  données, de l'inventaire, du rapport de contrôles et du code qui lira VALIDATION et OOS, calculera
  la robustesse et attribuera les verdicts). `mine_50_selection.py` écrit les atomes lui-même et
  enregistre ses propres comptes.

## 7. Tests hors échantillon

- Test d'une règle sur un bloc : p = max(Fisher exact, bootstrap de grappes de la différence de
  précision règle moins reste avec les tirages sans déclenchement comptés CONTRE la règle,
  Cochran-Mantel-Haenszel stratifié par jour calendaire). 100 000 tirages de bootstrap (un p au
  plancher 1/100 001 est signalé).
- VALIDATION, une lecture : passe si ≥ 8 déclenchements dans ≥ 5 grappes sur ≥ 3 jours, précision
  au-dessus du taux de base et p ≤ 0,10. Pas de correction ici : c'est le crible de réplication.
- OOS, une lecture : seuls les survivants de VALIDATION sont testés, Holm sur eux à 0,05 unilatéral,
  mêmes minima de déclenchements, de grappes et de jours. Les autres candidats sont lus à titre
  descriptif seulement.
- Le marqueur de lecture (`VALIDATION_READ.json`, `OOS_READ.json`) est écrit AVANT tout résultat.
- Grappes = l'identifiant `cluster` du snapshot (union-find sur tout le snapshot, donc avec du futur) :
  utilisé pour l'inférence uniquement, jamais comme feature.

## 7b. Bibliothèque de patterns composites pré-spécifiés (ajoutée le 2026-10-06, DISCOVERY seul)

Avant toute sélection mécanique, une bibliothèque de patterns composites écrits d'avance (familles
A demande réelle, B relais organique, C suite d'achats, D coordination, E wash, F funding +
coordination, G créateur + acteurs précoces, H bundle + post-bundle, I bot / script ; conditions
« A haut ET B haut ET C bas » aux quantiles 20 / 35 / 50 / 65 / 80 % de DISCOVERY) est évaluée sur
DISCOVERY seulement (`code/pat_35_composites.py`, `tables/composite_patterns.json`) : précision, lift,
couverture, trades attendus, seuil de rentabilité, espérance nette, seuils plus stricts et plus
permissifs, coupure − 2 s, sous-périodes, part de l'information venant des features pg_*. Lecture
descriptive, enregistrée au registre comme exploratoire ; aucun de ces patterns n'est sélectionné ni
testé hors échantillon par cette étape. Les patterns retenus pour la suite entreront dans la liste
gelée de SELECTION comme candidats pré-déclarés, à côté des règles mécaniques, et seront comptés dans
Holm comme les autres.

## 8. Contrôles avant le gel (`ctl_00_controls.py`)

Issues synthétiques sur les vraies features, blocs, grappes, jours et éligibilité. Mondes : NUL
(effet aléatoire grappe × bloc, écart-type 1 en logit) ; NUL + effet de jour (0,4 et 0,8) ; NUL
« historique » (indépendant + jour 0,8, features d'historique h1 reconstruites à partir des issues
synthétiques) ; règle plantée (paire d'atomes réels, support 8 à 15 % ou 5 à 8 %) à × 1,83, × 2,2,
× 2,9, × 3,0 le taux de base. Toute la chaîne tourne, verdicts compris. Mesurés : faux survivants OOS
par passage, INTERESTING par passage sous le nul, sort de la règle plantée (gelée, VALIDATION, OOS),
survivants OOS portant une part du signal planté. La configuration est celle renvoyée par les
workers. 200 graines pour le monde NUL.

Puissance attendue (contrôles du 05/10, avant correctifs) : une règle à × 3 retrouvée environ
2 fois sur 3, × 2,2 environ 1 fois sur 3 ou 4, × 1,6 jamais. Un verdict négatif n'exclut donc que les
gros effets ; la cible ×5 (environ 11 succès sur DISCOVERY) n'a pas de puissance et reste descriptive.

## 9. Robustesse (`rob_80_robustness.py`, après l'OOS, descriptif)

Statistiques VALIDATION + OOS stratifiées par bloc (rapport de taux de Mantel-Haenszel, p CMH par
jour). Seuils voisins (prochain quantile réellement distinct ; état par voisin : testé, trop petit,
non testable), coupures − 2 s et − 5 s (ou « non testable »), ×2 / ×3 / ×5, relevé unique, 30 min /
2 h, semaines, sans la grappe dominante, sans les 2 meilleurs trades, sans les entrées peu liquides,
coûts (100 / 500 / 1 000 $, K ×0,5 et ×2, sortie au toucher, stop − 50 %, entrée + 15 s), temps et
creux avant la cible, fréquence, lift par tercile de prime d'entrée. Une vérification ratée ne peut
que déclasser. Le net d'un survivant est mesuré sur les blocs qui l'ont retenu : biais vers le haut
d'environ 9 à 14 points par trade (contrôles de la revue) ; borne basse à 99 % sous 35 trades.

## 10. Verdicts (liste de décision ordonnée, fixée maintenant ; `ap_mine.tier` + `rep_90_report.py`)

1. Une feature de la règle est LEAK, AMBIGUOUS ou exclue par le plan → REJECTED.
2. Passe VALIDATION puis l'OOS (Holm) → OOS SURVIVOR, puis CANDIDAT EXPLOITABLE si TOUT ceci :
   excès de lift OOS ≥ la moitié de l'excès DISCOVERY ; seuils : ≥ 1 voisin testé et tous les voisins
   testés gardent un lift MH > 1 (un composite, sans voisin, ne peut pas l'être) ; lift MH > 1 sans la
   grappe dominante et ≥ 5 grappes sur VALIDATION + OOS ; net moyen à 500 $ positif à la borne basse
   (99 % sous 35 trades, IC 95 % sinon) sur ≥ 5 grappes, net moyen > 0 à 100 $ et à K ×0,5 ;
   ≥ 2 signaux par jour d'activité ; aucune feature avec fuite.
3. Passe VALIDATION, pas l'OOS corrigé, précision OOS au-dessus du taux de base → INTERESTING.
4. Échoue VALIDATION, lift > 1 en VALIDATION et en OOS, p CMH par jour sur VALIDATION + OOS ≤ 0,05 →
   INTERESTING.
5. Sinon REJECTED.

INTERESTING est compatible avec le bruit : les contrôles donnent environ 1 par passage sous le nul
(revue du 05/10) ; le rapport imprime ce taux nul à côté de chaque INTERESTING et aucun INTERESTING
ne justifie une suite sans échantillon prospectif. Si aucun candidat n'atteint OOS SURVIVOR, le
rapport écrit NO EXPLOITABLE PATTERN FOUND, avec la puissance mesurée : « aucune règle de support
≥ 8 % et de lift ≥ 3 n'a été trouvée ; un lift de 2,2 n'est vu qu'une fois sur 3 ou 4 ».

Un candidat exploitable resterait « à confirmer en prospectif » : le snapshot est réutilisé.

## 11. Amendement du 2026-10-07 : un seul candidat pré-déclaré, la sélection mécanique abandonnée

Décision de Benjamin après l'autopsie de D1 (`tables/BREAK_THE_LOOP_2026-10-06.md`) : la liste gelée
de SELECTION contient UN candidat pré-déclaré, la règle SWARM + CHEAP ENTRY définie dans
`tables/CANDIDATE_SWARM_CHEAP_ENTRY.md` (hachée dans `tables/CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json`),
cible primaire Y2, trade et coûts de la section 4. Le gel (`code/frz_55_candidate.py`) n'écrit que ce
candidat ; `mine_50_selection.py` n'est pas lancé : les règles mécaniques de DISCOVERY et les
composites ne sont ni gelés ni testés, et ne pourront plus l'être après la lecture de VALIDATION et
OOS. Tests : section 7 inchangée (VALIDATION une lecture, p ≤ 0,10 ; OOS une lecture, Holm sur un
candidat = 0,05). Classement A / B / C tel qu'écrit dans le fichier du candidat. La section 7b
(bibliothèque de patterns composites) reste descriptive. Rien de VALIDATION ni d'OOS n'avait été lu
au moment de cet amendement.
