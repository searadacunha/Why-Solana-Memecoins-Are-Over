# Pré-enregistrement : rythme des équipes et GOOD / BAD à l'intérieur d'une même équipe (2026-10-07)

Écrit AVANT tout calcul d'issue de cette analyse. Exploratoire, séparé de l'étude confirmatoire.
Suite de `tables/BUNDLE_OPERATOR_FORENSICS_2026-10-06.md` (réponse C). Question : pourquoi la même
équipe fait-elle parfois un GOOD et parfois un BAD ?

## Ce qui a été regardé avant d'écrire ce fichier (structure seulement, aucune issue)

- Intervalles entre lancements consécutifs d'un même groupe U (827 intervalles) : 10e, 25e, 50e,
  75e, 90e centiles = 12,6 / 16,9 / 24,9 / 77,9 / 1 286 min ; presque aucun intervalle sous 10 min
  (40 sur 827) alors que 47 % des alertes du marché se suivent à moins de 10 min ; creux entre 100
  et 300 min. D'où le seuil de session ci-dessous.
- Couverture des colonnes de `X.npz` sur DISCOVERY + SELECTION (manquants, valeurs distinctes).
- 381 sessions à 90 min, 697 lancements sur 1 015 dans des sessions d'au moins 3.

## Données

- Les 1 015 alertes antérieures au 2026-09-15 00:00 UTC (DISCOVERY 643, SELECTION 372). Issues par
  `ap_lib.load_labels("selection")` seulement : VALIDATION et OOS ne sont ni chargés ni lus, leurs
  features non plus. OOS reste vierge. L'étude confirmatoire n'est pas ouverte.
- Issues sur les lignes éligibles (régime fin, entrée + 5 s, fenêtre 1 h observée) : 612.
- GOOD = Y2 (×2 confirmé en 1 h depuis l'entrée à + 5 s), BAD = éligible et pas Y2. ×3 descriptif.
- Équipe = groupe U de `mech_45_operators.py` (L1 ∪ L3 ∪ L5 ∪ créateur), sur toute la période
  (identité descriptive). Le test prédictif (section 6) utilise l'identité U causale (union-find
  incrémental, lancement visible 60 s après son alerte). Sensibilités : sans le plus grand groupe U
  (la « population diffuse »), et identité L1 (équipes à wallets fixes).
- Population intra-équipe : lancements éligibles des groupes U à ≥ 5 lancements éligibles. Les
  groupes sans GOOD ou sans BAD n'apportent rien aux comparaisons intra-équipe (ils restent
  comptés dans les dénominateurs descriptifs).
- Session : lancements consécutifs d'une équipe séparés de plus de 90 min = nouvelle session.
  Sensibilités 60 et 180 min.
- Aucune donnée nouvelle, aucun réseau, aucun `.env`.

## Variables fixées (une valeur par lancement, connue à l'alerte − 1 s sauf mention)

Familles : T0 = configuration choisie par l'équipe au slot de création ; RY = rythme de l'équipe ;
RE = réaction du marché entre la création et l'alerte ; CX = contexte.

| # | variable | famille | source |
|---|---|---|---|
| 1 | nombre de snipers | T0 | `lv_n_snipers` |
| 2 | SOL total du bundle | T0 | `lv_snipe_sol` |
| 3 | ticket médian | T0 | `lv_ticket_median` |
| 4 | dispersion des tickets (CV) | T0 | `lv_ticket_cv` |
| 5 | part de l'offre achetée | T0 | `lv_supply_part` |
| 6 | transactions du bundle | T0 | `lv_ntx` |
| 7 | achats groupés (≥ 2 wallets dans une transaction) | T0 | `lv_paquet_max` ≥ 2 |
| 8 | ordre des snipers dans le slot | T0 | `s0_core_order_rho` |
| 9 | achat du créateur | T0 | `b_creator_buy_sol` |
| 10 | âge des wallets snipers | T0 | `w_core_log_age_h` |
| 11 | part des wallets nouveaux pour l'équipe | T0 | calculée (lancements antérieurs de l'équipe) |
| 12 | recouvrement des wallets avec le lancement précédent de l'équipe (Jaccard) | T0 | calculée |
| 13 | nombre de derniers financeurs distincts des snipers (financement < t − 1 s) | T0 | calculée (`cd_table`) |
| 14 | au moins un dernier financeur commun avec le lancement précédent de l'équipe (snipers, financement < t − 1 s) | T0 | calculée |
| 15 | délai médian financement → achat | T0 | `cd_fund_to_buy_med_s` |
| 16 | dispersion des heures de financement | T0 | `cd_fund_spread_s` |
| 17 | même configuration exacte de tickets que le lancement précédent | T0 | calculée |
| 18 | intervalle depuis le lancement précédent de l'équipe (log) | RY | calculée |
| 19 | rang dans la session | RY | calculée |
| 20 | lancements de l'équipe dans les 60 min précédentes | RY | calculée |
| 21 | essaim externe à − 10 s | RE | `feat_swarm` |
| 22 | essaim externe à − 5 s | RE | `feat_swarm` |
| 23 | bots récurrents présents à − 10 s (acheteurs externes déjà vus acheteurs externes avant l'alerte sur ≥ 5 lancements antérieurs) | RE | calculée (fenêtres brutes) |
| 24 | snipers d'une AUTRE équipe parmi les acheteurs externes avant l'alerte | RE | calculée |
| 25 | acheteurs non snipers dans le slot de création | RE | `b_other_slot0_buyers` |
| 26 | part vendue par les snipers avant l'alerte | RE | `m_core_exit_share` |
| 27 | âge du token à l'alerte | RE | `lv_age_alert_s` |
| 28 | prime d'entrée sur le prix de l'opérateur | RE | `p_entry_over_operator` |
| 29 | taux ×2 du marché sur les 24 h résolues | CX | calculé comme `mech_45` (p_m) |
| 30 | alertes du marché sur 60 min | CX | `lv_n_alerts_prev_60m` |
| 31 | candidats du détecteur sur 60 min | CX | `lv_n_candidates_prev_60m` |
| 32 | lancements des AUTRES équipes dans les 30 min précédentes | CX | calculée |

« Lancement précédent de l'équipe » = le précédent dans l'ordre des alertes, éligible ou non.

## Tests (tous fixés ici ; nul = permutation des issues, B = 10 000 sauf mention)

1. Rythme, descriptif : distribution des intervalles (équipe contre marché), CV des intervalles à
   l'intérieur des sessions, tailles et durées de sessions, lancements par heure, heures UTC.
2. Rythme contre issue, intra-équipe (χ² sommé sur les équipes, nul = permutation dans l'équipe) :
   R1 heure (0-6, 6-12, 12-18, 18-24 UTC) ; R2 intervalle (premier de l'équipe, > 90 min, 30-90,
   15-30, < 15 min) ; R3 rang dans la session (1, 2-3, 4-6, ≥ 7) ; R4 tiers relatif de la session
   (début, milieu, fin ; sessions ≥ 3 ; NON causal) ; R5 taille de la session (1, 2-3, 4-9, ≥ 10 ;
   NON causal) ; R6 lancements de l'équipe dans les 60 min (0, 1-2, ≥ 3). R1 aussi sur le marché
   entier (nul global).
3. Séquences, intra-équipe : S1 P(G | précédent G) − P(G | précédent B), dans l'équipe, puis S2 dans
   la session seulement ; S3 P(G | deux B précédents) contre le reste ; S4 P(G | trois B précédents)
   contre le reste ; S5 causale : P(G | dernière issue RÉSOLUE de l'équipe G) − P(G | B) (résolue =
   t_j + 4 020 s ≤ t_i − 1) ; S6 causale : les 2 dernières résolues B contre le reste ; S7 hétérogénéité
   par rang modulo 3 dans la session (« un sur trois » programmé) ; S8 modulo 2 ; S9 nombre de
   séries (runs) dans les suites d'équipe ; S10 surdispersion entre sessions d'une même équipe
   (χ² sessions dans l'équipe, nul = permutation dans l'équipe : les GOOD se groupent-ils dans
   certaines sessions ?). Paires ou triplets comptés seulement si tous les lancements sont éligibles.
4. GOOD contre BAD dans la même équipe, variables 1 à 32 : AUC intra-équipe = P(x_GOOD > x_BAD) sur
   les paires (GOOD, BAD) de la même équipe (ex aequo = 1/2) ; nul = permutation des issues dans
   l'équipe ; p bilatéral ; Benjamini-Hochberg sur les 32 (q ≤ 0,10). Variable retenue seulement si
   q ≤ 0,10 ET même sens sur DISCOVERY et SELECTION séparément. Comparée à l'AUC poolée (toutes
   équipes mêlées) pour séparer l'effet équipe de l'effet lancement. Sensibilités : AUC intra-session
   (paires de la même session), sans le plus grand groupe, identité L1. ×3 descriptif.
5. Changement de configuration, intra-équipe : C1 P(G | changement) − P(G | même) pour : configuration
   exacte de tickets, wallets (Jaccard < 0,5 avec le précédent), financeur dominant, nombre de
   snipers, SOL total (écart > 5 %) ; nul = permutation dans l'équipe ; BH sur les 5. C2
   hétérogénéité du taux GOOD entre configurations exactes, entre ensembles exacts de wallets et
   entre financeurs dominants à l'intérieur d'une équipe (χ² sommé, nul = permutation dans l'équipe).
6. « Une configuration annonce-t-elle un GOOD avant le mouvement ? », prédictif et chronologique :
   lancements éligibles avec ≥ 3 lancements antérieurs dans l'identité U causale. Variables T0 en
   écart à la moyenne des lancements antérieurs de l'équipe, RY brutes, RE brutes, CX brutes.
   Régression logistique L2 (C = 0,1 sur variables standardisées sur le bloc d'apprentissage,
   manquants remplacés par la médiane d'apprentissage, rien d'autre de réglé). Modèles : M0 marché
   (p_m) ; M1 historique d'équipe rétréci (identique à `mech_45`) ; M2 T0 + RY (configuration et
   rythme de l'équipe) ; M3 RE (réaction) ; M4 tout. Apprentissage DISCOVERY → test SELECTION, puis
   l'inverse. Mesures : AUC, gain de log-loss sur M0 (IC bootstrap par équipe), AUC intra-équipe du
   test. « Annonce » = gain > 0 avec borne basse > 0 dans les DEUX sens.
7. Interaction entre équipes et environnement : I1 corrélation entre l'issue d'un lancement et le
   taux GOOD des lancements éligibles des AUTRES équipes à ± 60 min (NON causal : mesure si les
   issues se groupent dans le temps entre équipes) ; nul = permutation dans le jour calendaire ;
   sensibilité ± 30 min. I2 variables 24 et 32 (test 4). I3 paires d'équipes (A lance, des snipers
   de B sont parmi les acheteurs avant l'alerte) à ≥ 5 cooccurrences : tableau descriptif, au plus
   10 lignes, sans test. I4 les 10 bots récurrents les plus fréquents parmi les acheteurs externes
   à − 10 s (classés par fréquence, sans issue) : taux GOOD présent contre absent, intra-équipe
   (permutation dans l'équipe), BH sur les 10.
8. Décomposition : modèle logistique mixte (statsmodels, variationnel) avec effets aléatoires équipe,
   session (équipe × session), jour, et prime d'entrée en tercile en effet fixe ; variantes équipe
   seule, équipe + session, équipe + session + jour. Descriptif.
9. Contrôles synthétiques avant toute issue réelle, sur les vraies équipes, sessions et variables :
   (a) monde nul (issues permutées dans l'équipe), 200 graines : taux de faux positifs BH des tests
   4 et du test S1 ; (b) effet planté sur une variable réelle (logit + 0,8 par écart-type, intra-équipe)
   : puissance du test 4 ; (c) dépendance plantée (P(G) + 15 points après un B) : puissance de S1.
   B réduit à 2 000 dans les contrôles. Lignes de registre « synthetiques ».

## Classement fixé d'avance

- « Passe » partout = q ≤ 0,10 après BH à l'intérieur de sa section (section 4 : les 32 variables ;
  sections 2 et 3 : leurs tests ensemble ; section 5 : C1 et C2 ensemble ; I1 et I4 ensemble) ET
  même sens sur DISCOVERY et SELECTION pris séparément.
- A cadence / règle : un test CAUSAL des sections 2 ou 3 passe.
- B équipes distinctes, résultat dépendant du contexte : rien en T0 ni en RY, mais une variable CX
  (29 à 32) ou I1 passe.
- C mêmes équipes, GOOD / BAD essentiellement imprévisibles : rien ne passe en T0, RY, RE, CX, I1, I4,
  section 5 ni section 6.
- D interaction équipes / environnement : I1, I4 ou une variable RE passe (le GOOD dépend de ce que
  font les autres acteurs, pas de l'équipe).
- E autre mécanisme : un résultat qui passe et n'entre dans aucune case.
Plusieurs cases peuvent s'appliquer ; le rapport dit laquelle porte le plus de variance (section 8)
et si quelque chose est disponible AVANT le mouvement (section 6). Aucune règle de trading n'est
tirée d'ici ; au plus une hypothèse écrite pour un test prospectif.

## Amendement 1 (2026-10-07, avant tout calcul d'issue réelle ; résultats vus : non)

Après la revue à l'aveugle du code (`audit/TEAM_RHYTHM_PREAUDIT_2026-10-07.md` : 3 auditeurs, chaque constat
grave soumis à un agent chargé de le réfuter). Seuls les contrôles synthétiques v1 avaient tourné.

1. « χ² sommé sur les équipes » (R1 à R6, S7, S8, S10, C2) est bien la somme sur les cellules
   (équipe, catégorie) de (O − E)² / (n p (1 − p)). La v1 additionnait les écarts entre équipes avant
   le carré. C1 et I4 (contrastes binaires « changé / même », « présent / absent ») restent poolés et
   orientés, nul dans l'équipe.
2. « Même sens sur DISCOVERY et SELECTION » : chaque bloc est recalculé avec ses propres taux d'équipe.
   Pour les statistiques d'hétérogénéité (χ²), le sens est « au-dessus de la moyenne du nul » dans ALL,
   DISC et SEL. Pour S1 à S6 et I1, il porte sur l'écart à la moyenne du nul (biais de composition et
   de Miller-Sanjurjo), avec les mêmes permutations pour les blocs. Une condition vide (moins de 5
   tuples) donne une différence indéfinie.
3. S5 et S6 utilisent la porte écrite ici (4 020 s), pas les 3 810 s de `ap_lib`.
4. C1 « financeur » = financeur dominant non hub (clé L3), comme écrit. C2 : les lancements sans
   configuration ou sans financeur dominant sont écartés, plus regroupés en une catégorie commune.
5. Ajouts descriptifs, hors BH : témoin négatif « heure de l'alerte » en AUC intra-équipe (dérive du
   taux d'une équipe dans le temps) ; nul supplémentaire pour I1, permutation dans équipe × jour ;
   part des paires venant du plus grand groupe ; avertissements de convergence.
6. Contrôles : 200 mondes nuls (au lieu de 100) ; puissance mesurée avec la vraie règle de décision
   (BH sur les 17 tests des sections 2 et 3, plus le même sens) pour + 5, + 10, + 15 et + 20 points
   après un BAD.
7. Règle de lecture, sans changer les tests : 76 % des paires (GOOD, BAD) de l'AUC intra-équipe
   viennent du plus grand groupe U, la population diffuse, qui n'est pas une équipe (forensique du
   06/10). Une variable qui passe n'est attribuée à « l'équipe » que si elle garde le même sens, avec
   p ≤ 0,10, sans le plus grand groupe ET à l'intérieur des sessions. Sinon elle est attribuée à la
   population diffuse ou à une dérive dans le temps. La sensibilité « identité L1 » garde les
   variables calculées en U (nom de sortie `strata_L1_variables_U`).
8. Les tests R2, R3, R6, S5 à S8 sont causaux dans le temps, mais l'identité U est finale. Si l'un
   d'eux passe, il est recalculé avec l'identité causale avant tout classement en A.
