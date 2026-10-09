# Revue des conclusions : TEAM_ABSORPTION_MECHANISM_2026-10-07.md (2026-10-07)

Deux claims-auditor indépendants (workflow `absorption-claims-audit`, run wf_4d3dc592-70b), un passage. Verdict : FAIL pour les
deux (critères 1, 4, 5, 7, 10 ; le premier aussi 9). Classement D confirmé par les deux ; table des règles exacte cellule par
cellule ; aucune lecture de VALIDATION / OOS ; aucune analyse d'issue hors registre. Toutes les corrections (arrondis, dénominateurs,
formulations trop affirmatives, 81 s = première vente des wallets de sortie, garde K4 tautologique, écart du post hoc au
pré-enregistrement) ont été reprises dans le rapport, sans changement de méthode. Pas de second passage.

## Auditeur 1

| critère | verdict |
|---|---|
| 1 | FAIL |
| 2 | PASS |
| 3 | PASS |
| 4 | FAIL |
| 5 | FAIL |
| 6 | PASS |
| 7 | FAIL |
| 8 | PASS |
| 9 | FAIL |
| 10 | FAIL |

Corrections demandées (26) :

- « La meilleure valeur d'avant l'entrée (M1 à l'alerte, 0,61) s'inverse sur SELECTION » : [formulation] explanatory["M1_ext_buyers|-1"].auc = 0,6047, soit 0,60 à deux décimales ; même erreur dans la cellule du tableau (l.109 : « 0,61 (p 0,027 ; q 0,41) »).
- « | M3 SOL sur 10 s | 0,56 | 0,53 | 0,50 | 0,50 | 0,57 | 0,57 | » : [formulation] explanatory["M3_ext_buy_sol_last10|2"].auc = 0,5246, soit 0,52.
- « à 5 min, × 1,55 contre × 0,65 » : [formulation] price_after_entry.at_300.bad_median = 0,6447, soit 0,64 ; même erreur l.61 (« × 1,01 / 1,00 / 0,96 / 0,65 »).
- « (T = 5, 10, 20, 30 s ; 613 éligibles ; 27,5 %, 27,1 %, 24,8 %, 24,5 % de ×2) » : [formulation] population.Y2_5.eligible = 612 ; seuls T = 10, 20 et 30 ont 613 éligibles.
- « R1 24 à 32 % » : [formulation] S_R1_with_buyburn sur SELECTION à T 30 : 37/157... non, 43/188 = 22,9 %, sous la borne écrite.
- « mêlées, les équipes donnent une AUC de 0,50 à 0,55 » : [formulation] pooled_auc_nobig vaut 0,474 (M5) et 0,475 (M7) : la fourchette réelle va de 0,47 à 0,55.
- « sur les deux blocs pour M3, M4, M5 et M6, mais SELECTION seul n'est jamais significatif » : [formulation] Les 7 pistes sont de même sens sur les deux blocs (M2 et M7 aussi, SEL 0,53 et 0,54). Surtout, elles ont été choisies sur DISCOVERY et SELECTION réunis (posthoc_nobig.py:18) : le même sens sur SELECTION n'est pas une réplication indépendante, et les p par bloc sont 
- « AUC intra-équipe contre Y2 (explicatif ; familles BH d'avant l'entrée : 19 tests) : » : [formulation] Le dénominateur et le n effectif manquent : les AUC portent sur 413 lancements de 28 équipes ayant au moins un GOOD et un BAD, soit 3 642 paires dont 80 % dans g31, et non sur les 456 lancements de 33 équipes annoncés l.19. Les tests tradables portent sur 427, 401 e
- « | part de l'inventaire vendue à création + 30 s / + 40 s | | 2,0 % / 4,6 % | 1,8 % / 4,5 % | » : [formulation] À + 40 s, le calcul ne porte que sur les alertes faites moins de 11 s après la création (team_sold_share_c40 : 78/125 GOOD, 213/331 BAD). Ce dénominateur n'est pas indiqué.
- « | R3 vitesse ≥ 80e centile | 5 / 10 / 20 / 30 | 24,0 % ; 26,8 % ; 30,0 % ; 21,3 % (n 75 à 82) | 29,3 % ; 20,0 % ; 25,0 % ; 24,0 % | non | » : [formulation] Les taux SELECTION n'ont pas de dénominateur (rules.*.R3_velocity_ge_disc_p80.SEL.n = 58, 65, 64, 50).
- « des effets intra-équipe d'AUC inférieure à environ 0,65 » : [formulation] Le chiffre 0,65 ne vient d'aucune source. La seule mesure de puissance (étude précédente, autre famille de tests) retrouve 0,68 dans 47 mondes sur 50 et dit qu'elle n'exclut pas les AUC entre 0,5 et 0,68 (BUNDLE_TEAM_RHYTHM_2026-10-07.md:58-63). Écrire 0,65 laisse c
- « elle est petite, et cette étude n'a pas la puissance de la voir » : [formulation] La puissance de ce test n'a pas été mesurée, et le résultat (AUC 0,58, p 0,14, 342 lancements) ne dit pas que l'effet est petit : il dit seulement qu'il n'est pas détecté.
- « **À + 29 s, oui, de façon régulière mais modeste** : le rapport demande / inventaire est plus haut sur les GOOD que sur les BAD dans 12 équipes sur 13 (test du signe pré-enregistré » : [formulation] Ce « oui » repose sur un p nominal, à une coupure (+ 29 s) que l'amendement 1, point 2, déclare en partie contenue dans le label (M7 fixe les réserves, donc le prix). Le test à prix égal, conçu pour lever ce doute, ne passe pas.
- « la vitesse de la demande à + 17 et + 27 s sépare un peu les GOOD des BAD, y compris pour une entrée à + 20 ou + 30 s (AUC 0,61 à 0,65 ; sensibilité puis contrôle post hoc, section  » : [formulation] La formule « sépare un peu » présente comme un constat une piste post hoc, non significative sur SELECTION seul et choisie sur les deux blocs réunis.
- « avec une AUC intra-équipe d'environ 0,60. » : [formulation] À + 29 s, la mesure est descriptive et en partie contenue dans le label (amendement 1, point 2). La section 4 le dit, mais pas le résumé.
- « quand toutes les équipes sont mêlées (AUC 0,52) » : [formulation] Le 0,52 est l'AUC intra-équipe de M7 à + 27 s (tradable, g31 incluse). Or « mêlées » désigne l'AUC poolée à la section 7, et l'AUC poolée de M7 vaut 0,49.
- « D, l'hypothèse d'absorption OBSERVABLE avant la décision » : [formulation] « Rejetée » reprend le nom de la classe D du préenregistrement. Sans puissance mesurée, il faut dire que cela signifie « non détectée », pour que l'absence de séparation ne se lise pas comme une absence d'effet.
- « ce qui ressemblerait à B si cela se confirmait » : [formulation] Les mêmes lettres B, C, D servent au classement (l.33-39) et aux scénarios de la consigne (section 8). Ici, B désigne la classe du classement ; à la l.225, « est B » désigne le scénario. Un lecteur peut croire que « D » et « B » se contredisent.
- « | liquidation par les wallets de sortie | une médiane de 81 s après le transfert (exit_destination, contexte cité, non remesuré ici) | | | » : [formulation] Dans la source, 81 s est le délai jusqu'à la PREMIÈRE vente du wallet de sortie (exit_destination/results.md:62 ; p25 35 s, p75 143 s, p90 330 s), pas toute la liquidation. Même erreur l.253 (« il se joue quand les wallets de sortie liquident, une médiane de 81 s ap
- « liquidation, 1 à 25 minutes après l'entrée, selon que de nouveaux acheteurs arrivent ou non » : [formulation] C'est une interprétation présentée comme un fait. Elle met dans la liquidation une fenêtre (25 min) qui est en réalité le 90e centile du ×2. Elle contredit aussi « 1 à 5 minutes après la création » (l.41, l.268).
- « wallets de sortie, le même rythme de transfert et de première vente. Le résultat se joue ensuite, quand » : [formulation] Seul le NOMBRE de wallets de sortie a été mesuré (médiane 4 et 4), pas leur identité ; même chose l.290 (« les mêmes pour GOOD et BAD »). La suite (« quand les wallets de sortie liquident et que les acheteurs suivants arrivent ») n'est pas observée.
- « c'est donc uniquement par la demande à venir » : [formulation] L'offre après + 30 s n'est pas observée : elle pourrait aussi différer. Le post hoc du rapport montre d'ailleurs que, sans g31, l'équipe vend un peu plus sur les GOOD à + 27 s (M5 et M6, AUC 0,60). Même tension dans la ligne du scénario D (l.223 : « la vitesse de li
- « sont des bots récurrents qui viennent sur presque tous les lancements » : [formulation] M9 compte les acheteurs déjà vus sur au moins 5 lancements antérieurs, pas sur presque tous. Et la médiane des BAD à + 2 s vaut 0,79, ce qui contredit « plus de 80 % » (l.258).
- « Même la seule règle au-dessus du seuil (R2 à + 10 s, 6 sur 12) » : [formulation] Le tableau de la section 9 montre aussi R4 à + 10 s au-dessus de 45,8 % sur DISCOVERY (46,2 %, n 13). R2 à + 10 s est la seule au-dessus du seuil sur les deux blocs.
- « le code lève une erreur sur toute transaction postérieure à la coupure » : [bug de code] À feat_48_absorption.py:137-141, le garde K4 teste vs, vb et vbb, des listes déjà filtrées sur bt <= cutabs juste au-dessus : il ne peut jamais se déclencher. Ce qui protège réellement, c'est le filtre, et le rapport présente le garde comme un contrôle.
- « et inscrit au registre (`tables/team_absorption_posthoc_nobig.json`), bloc par bloc » : [formulation] Le script du post hoc n'est pas cité. Le registre pointe vers « <hors etude>/posthoc_nobig.py » (dossier temporaire), dont une copie identique (sha a4ff1bbc) existe dans l'étude.

## Auditeur 2

| critère | verdict |
|---|---|
| 1 | FAIL |
| 2 | PASS |
| 3 | PASS |
| 4 | FAIL |
| 5 | FAIL |
| 6 | PASS |
| 7 | FAIL |
| 8 | PASS |
| 9 | PASS |
| 10 | FAIL |

Corrections demandées (24) :

- « | M1 acheteurs | 0,61 (p 0,027 ; q 0,41) | » : [formulation] explanatory['M1_ext_buyers|-1'].auc = 0,6048, recalculé à part : 0,60475. Le 0,61 vient d'un double arrondi. Même erreur l.117 : 'M1 à l'alerte, 0,61'.
- « | M3 SOL sur 10 s | 0,56 | 0,53 | » : [formulation] explanatory['M3_ext_buy_sol_last10|2'].auc = 0,5246.
- « × 1,55 contre × 0,65 » : [formulation] price_after_entry.at_300.bad_median = 0,6447. Même erreur l.61 : '0,96 / 0,65'.
- « AUC de 0,50 à 0,55 » : [formulation] Dans team_absorption_posthoc_nobig.json, pooled_auc_nobig va de 0,474 (M5) à 0,552 (M4). Le tableau juste au-dessus affiche d'ailleurs 0,47 et 0,48.
- « R1 24 à 32 % » : [formulation] S_R1_with_buyburn va de 22,9 % (SEL, T = 30) à 31,8 %.
- « composé à plus de 80 % » : [formulation] Médiane M9 à + 2 s : 0,81 pour les GOOD, 0,788 pour les BAD.
- « qui viennent sur presque tous les lancements » : [formulation] M9 mesure seulement la part d'acheteurs déjà vus sur au moins 5 lancements antérieurs. 'Presque tous les lancements' n'est mesuré nulle part.
- « 2,0 % / 4,6 % | 1,8 % / 4,5 % » : [formulation] La valeur à + 40 s porte sur 78 GOOD sur 125 et 213 BAD sur 331 (descriptive.team_sold_share_c40), et le dénominateur n'est pas écrit.
- « familles BH d'avant l'entrée : 19 tests » : [formulation] Les AUC portent sur n = 413 lancements, 28 équipes ayant au moins un GOOD et un BAD, et 3 642 paires, pas sur les 456 / 33 annoncés l.19. En section 7 (l.179), n = 413, 427, 401 et 398 lancements, pour 28, 30, 26 et 26 équipes.
- « 29,3 % ; 20,0 % ; 25,0 % ; 24,0 % » : [formulation] Les n de R3 sur SELECTION manquent.
- « 613 éligibles » : [formulation] À T = 5 s, population.Y2_5.eligible vaut 612.
- « quand toutes les équipes sont mêlées (AUC 0,52) » : [formulation] 0,52 est l'AUC intra-équipe de M7, g31 comprise. En section 7, 'mêlées' veut dire AUC poolée, et celle de M7 vaut 0,49.
- « oui, de façon régulière mais modeste » : [formulation] Le 'oui' repose sur un test du signe à p nominal 0,003, non corrigé, à c = 29, coupure où le chemin du prix après l'entrée fait partie du label (amendement 1.2). La même cellule écrit 'sépare un peu les GOOD des BAD' pour une sensibilité post hoc à p nominaux (meill
- « l'absorption explique un peu le résultat après coup » : [formulation] D'après l'amendement 1.3, seul un test « à prix égal » pouvait soutenir C, et aucun ne passe. Les AUC à c = 29 contiennent en partie le label. Même problème en Q5 : 'Après coup, faiblement ; avant, non.'
- « Elle se dessine entre + 10 et + 30 s » : [formulation] Aux coupures 9 à 29, les mesures comparées à Y2 (entrée à + 5 s) contiennent le chemin de prix qui fait le label (amendement 1.2). Le rapport le dit en section 4, mais pas dans la réponse courte.
- « liquidation par les wallets de sortie | une médiane de 81 s » : [formulation] exit_destination/results.md:18 et 62 : 81 s est le délai jusqu'à la PREMIÈRE vente du wallet de sortie (p25 35, p90 330 s), sur un autre échantillon (148 lancements WSMO). Ce n'est pas la durée de la liquidation. Même problème l.253 : 'il se joue quand les wallets d
- « se jouent entre 1 et 25 minutes après l'entrée » : [formulation] Cette fenêtre mêle la liquidation (citée, premières ventes à 81 s en médiane, liquidation placée à '1 à 5 minutes après la création' l.41 et 268) et le ×2 (10e et 90e centiles : 118 et 1 503 s). Les fenêtres se contredisent d'une section à l'autre.
- « liquidation, 1 à 25 minutes après l'entrée, selon que de nouveaux acheteurs arrivent ou non. » : [formulation] Une interprétation non testée est écrite comme un fait. Elle contredit aussi l'intitulé de B ('demande APRÈS la liquidation') et la fenêtre de liquidation donnée ailleurs.
- « Le résultat se joue ensuite » : [formulation] C'est le scénario B, non testé, écrit comme un fait. La phrase dit aussi 'les mêmes wallets de sortie' (l.65-66), alors que seul leur nombre a été comparé (médiane 4).
- « les mêmes pour GOOD et BAD » : [formulation] Seul le nombre de wallets de sortie a été comparé, pas leur identité.
- « c'est donc uniquement par la demande à venir » : [formulation] Ne rien détecter ne prouve pas l'égalité. Le post hoc de la section 7 donne d'ailleurs M5 à 0,60 (DISC 0,58, SEL 0,61) et M6 à 0,60 sans g31, et la section 7 écrit 'l'équipe vend davantage'. Même problème l.85 ('Côté offre, rien ne distingue') et l.223 ('la vitesse 
- « AUC inférieure à environ 0,65 » : [formulation] Le seuil de 0,65 ne se trouve dans aucune source. L'étude citée n'a mesuré que 0,68, sur d'autres familles, et écrit qu'elle n'exclut pas les AUC entre 0,5 et 0,68 (BUNDLE_TEAM_RHYTHM_2026-10-07.md:62-63).
- « la seule règle au-dessus du seuil » : [formulation] R4 à + 10 s fait aussi 46,2 % sur DISCOVERY seul (6 sur 13). R2 à + 10 s n'est la seule au-dessus de 45,8 % que sur les deux blocs réunis.
- « déclaré après lecture, inscrit au registre (22 comparaisons), hors classement. » : [formulation] L'écart au pré-enregistrement n'est pas signalé : le prereg (l.124) prévoit 'pas d'autre recherche après le rapport', et le post hoc a été lancé (07:24:27 UTC) après un premier jet du rapport (07:23:16) qui concluait 'rien de nouveau' pour les sensibilités.

