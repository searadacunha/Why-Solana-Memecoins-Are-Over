# Forensique des opérateurs de bundle (écrit le 2026-10-07)

Exploratoire. Tests fixés avant calcul dans `tables/OPERATOR_FORENSICS_PREREG_2026-10-07.md` (sha256
au registre). Données : uniquement les 1 015 alertes antérieures au 2026-09-15 (DISCOVERY et
SELECTION) ; VALIDATION et OOS ne sont ni chargés ni lus, l'étude confirmatoire n'est pas ouverte,
aucun label Pump-Gold. SELECTION est lu ici pour la première fois par alpha_patterns, mais il n'est
pas vierge pour cette question : signal_search l'avait lu le 02/10 (VAL1) pour des historiques à
15 min. Aucune donnée nouvelle n'a été téléchargée : les wallets, financeurs, tickets et créateurs
déjà présents suffisent à identifier les groupes. Chiffres : `tables/operator_forensics.json`, code
`code/mech_45_operators.py`.

## 1. Population étudiée

- 1 015 lancements bundle-snipés du 2026-08-21 au 2026-09-14 ; issues observables (régime fin,
  entrée + 5 s, fenêtre 1 h) sur 612 : 363 DISCOVERY, 249 SELECTION.
- Taux de base : ×2 27,5 % (DISCOVERY 25,1 %, SELECTION 30,9 %), ×3 9,6 %, ×5 2,3 %.
- 2 189 wallets snipers distincts : 1 767 (81 %) ne servent qu'une fois, 422 reviennent, 194 sur
  ≥ 5 lancements, 6 sur ≥ 20, au plus 24.

## 2. Combien de groupes persistants ?

Groupes = composantes connexes des lancements reliés par un lien de chaque niveau :

| niveau | lien | groupes | isolés | plus grand | groupes à ≥ 5 / 10 / 20 / 30 / 50 lancements éligibles |
|---|---|---|---|---|---|
| L1 wallet | ≥ 1 sniper commun | 502 | 419 | 80 (8 %) | 26 / 11 / 3 / 1 / 1 |
| L2 wallet + financeur | même paire (sniper, dernier financeur) | 741 | 662 | 17 | 18 / 3 / 0 / 0 / 0 |
| L3 financeur | même financeur dominant non hub | 676 | 581 | 17 | 20 / 4 / 0 / 0 / 0 |
| L4 co-occurrence | ≥ 2 snipers communs | 543 | 441 | 23 | 31 / 9 / 1 / 0 / 0 |
| L5 signature | même configuration exacte de tickets | 418 | 273 | 38 | 34 / 11 / 1 / 0 / 0 |
| U union | L1 ∪ L3 ∪ L5 ∪ créateur | 188 | 82 | 224 (22 %) | 33 / 19 / 3 / 1 / 1 |
| L3b (diagnostic) | même source au 2e saut | 794 | 773 | 58 | 9 / 4 / 2 / 1 / 0 |
| L5b (diagnostic) | signature grossière | 39 | 16 | 400 (39 %) | 11 / 9 / 8 / 5 / 4 |

Quelles similarités sont défendables ? Part des paires de lancements liées par un niveau qui
partagent AUSSI un autre lien, contre la même part parmi les paires de la même semaine :

| paires liées par | partagent aussi un wallet | un financeur | la configuration |
|---|---|---|---|
| wallet (2 658 paires) | : | 30,0 % (base 0,17 %) | 36,5 % (0,71 %) |
| financeur (1 253) | 63,7 % (0,70 %) | : | 63,2 % (0,76 %) |
| co-occurrence (2 123) | 100 % | 37,0 % (0,17 %) | 45,4 % (0,71 %) |
| configuration (3 207) | 30,2 % (0,64 %) | 24,7 % (0,17 %) | : |
| source au 2e saut (3 502) | 0,6 % (1,0 %) | 0,3 % (0,5 %) | 27,5 % (0,7 %) |

Les wallets, les financeurs non hubs et les configurations exactes se confirment mutuellement 45 à
220 fois plus que le hasard : ce sont trois facettes de vraies identités. La source au 2e saut ne
recoupe ni les wallets ni les financeurs (en dessous du hasard) et ne suit que la configuration :
c'est un hub au service d'un outil commun (par exemple `4kwM…`). La signature grossière fond 39 %
des lancements dans un seul groupe (un outil, pas une équipe). Les deux sont rejetées. Le créateur ne sert à rien (wallets
jetables : 221 créateurs pour 224 lancements dans le plus grand groupe). L'accord entre niveaux
(ARI) va de 0,2 à 0,5 : ils voient des facettes différentes, l'union U est l'identité retenue.

Trois modes opératoires couvrent 764 des 1 015 lancements (groupes U à ≥ 5 lancements) :

| mode | groupes | lancements | durée d'activité médiane | ce qui les identifie | ×2 | ×3 |
|---|---|---|---|---|---|---|
| équipe fixe : les mêmes 4 wallets à chaque lancement (Jaccard consécutif 1,0) | 22 | 271 | 1 jour | L1 / L4 | 28 % | 7 % |
| script fixe, wallets neufs : 0 wallet récurrent, 1 à 2 configurations, moitié « groupés », prime médiane × 7,95 | 19 | 213 | 3 jours (jusqu'à 13) | L5 seul | 26 % | 11 % |
| population diffuse : 311 wallets, 60 financeurs, 112 configurations, Jaccard consécutif 0,11, 18 jours | 1 | 224 | 18 jours | chaînage L1 / L5 | 33 % | 13 % |
| mixte | 3 | 56 | 7 jours | | 10 % | 5 % |

Réponse : oui, des acteurs persistants existent et se reconnaissent sans ambiguïté, mais la plupart
des « équipes » vivent un à trois jours (des rafales de 12 à 23 lancements), et le plus gros
ensemble (22 % des lancements) n'est pas une équipe : c'est une population de wallets snipers
réutilisés par plusieurs mains, que l'union-find relie en chaîne.

## 3. Top groupes par activité (U)

| groupe | mode | lancements (éligibles) | période | jours | wallets (récurrents) | financeurs | configs | prime méd. | ×2 | ×3 | ×5 | chronologie (F, 2, 3, 5 ; . = non observé) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g31 | diffuse | 224 (115) | 08-22 → 09-14 | 18 | 311 (115) | 60 | 112 | 3,56 | 38/115 = 33 % [25, 42] | 15 | 1 | … 52FFF2F (115 observés) |
| g5 | équipe fixe | 46 (17) | 08-21 → 09-04 | 9 | 26 (26) | 33 | 29 | 3,74 | 2/17 = 12 % [3, 34] | 0 | 0 | 2FFFFFFF2FFFFFFFF |
| g169 | script, wallets neufs | 38 (25) | 08-25 → 09-09 | 13 | 152 (0) | 38 | 1 | 10,5 | 10/25 = 40 % [23, 59] | 6 | 3 | F3 5F5F5FFF3FFFFFFF F232F22 |
| g225 | mixte | 27 (17) | 08-26 → 09-14 | 7 | 56 (24) | 14 | 3 | 3,55 | 1/17 = 6 % | 1 | 0 | FFFFF3FFFFFFF FFFF |
| g570 | équipe fixe | 23 (20) | 09-05 → 09-07 | 3 | 4 (4) | 5 | 4 | 3,75 | 7/20 = 35 % | 2 | 0 | FFFFFF2FF3F2222FF3 FF |
| g578 | script, wallets neufs | 20 (15) | 09-05 → 09-14 | 9 | 80 (0) | 20 | 1 | 11,7 | 2/15 = 13 % | 1 | 1 | F25FFFF FFFFF F FF |
| g789 | script | 20 (17) | 09-09 → 09-10 | 2 | 80 (0) | 2 | 1 | 3,59 | 2/17 = 12 % | 1 | 0 | FFFFFFFFF 2FFFF3FF |
| g68 | mixte | 17 (12) | 08-23 → 09-10 | 11 | 12 (8) | 17 | 1 | aberrante | 0/12 | 0 | 0 | F FFFFFFFFFFF |
| g811 | équipe fixe | 17 (14) | 09-09 → 09-10 | 2 | 4 (4) | 1 | 3 | 3,55 | 7/14 = 50 % | 2 | 0 | F2FFFF2F3F2223 |
| g679 | équipe fixe | 16 (12) | 09-07 → 09-08 | 2 | 8 (8) | 9 | 2 | 3,70 | 4/12 = 33 % | 2 | 1 | F2 2FFF3F5FFF |
| g606 | équipe fixe | 14 (14) | 09-06 | 1 | 8 (8) | 1 | 2 | 3,80 | 4/14 = 29 % | 2 | 0 | FF22FFFFFF3FF3 |
| g850 | équipe fixe | 14 (11) | 09-10 | 1 | 4 (4) | 0 | 13 | 3,68 | 6/11 = 55 % | 1 | 0 | 2F2F2F22F3F |
| g855 | équipe fixe | 14 (12) | 09-10 | 1 | 8 (8) | 1 | 1 | 3,66 | 5/12 = 42 % | 1 | 0 | 2FFF22F3F2FF |
| g493 | équipe fixe | 13 (13) | 09-03 → 09-04 | 2 | 4 (4) | 1 | 3 | 3,56 | 0/13 | 0 | 0 | FFFFFFFFFFFFF |
| g745 | équipe fixe | 13 (12) | 09-08 → 09-14 | 4 | 4 (4) | 5 | 5 | 3,87 | 7/12 = 58 % [32, 81] | 2 | 0 | F2FF223 2FF32 |

## 4. Taux de réussite par groupe

| seuil d'observations (U) | groupes | lancements | taux ×2 des groupes |
|---|---|---|---|
| ≥ 5 | 33 | 456 | de 0 % à 58 % |
| ≥ 10 | 19 | 368 | 0, 0, 6, 10, 10, 12, 12, 13, 20, 25, 29, 33 (g31), 33, 35, 40, 42, 50, 55, 58 % |
| ≥ 20 | 3 | 160 | g31 33 %, g169 40 %, g570 35 % |
| ≥ 30 et ≥ 50 | 1 | 115 | g31 33 % [25, 42], ×3 13 %, ×5 0,9 % |

Taux du marché sur la même période : 27,5 %. Les grands groupes sont au niveau du marché ; les
écarts viennent des petites équipes éphémères.

## 5. Hétérogénéité inter-groupes

Statistique : χ² de Pearson groupes × ×2, comparé à 10 000 réattributions des issues (toutes
ensemble, à l'intérieur du jour, à l'intérieur du jour et du tercile de prime d'entrée).

| identité | seuil | groupes | χ² (ddl ; moyenne sous le nul) | p global | p dans le jour | p jour × prime | écart-type vrai entre groupes | groupes dont l'IC exclut la base (attendu) |
|---|---|---|---|---|---|---|---|---|
| U | ≥ 5 | 33 | 58,8 (32 ; 32,0) | 0,002 | 0,010 | 0,004 | 10,6 pts | 5 (1,2) |
| U | ≥ 10 | 19 | 41,4 (18 ; 18,1) | 0,0008 | 0,0017 | 0,0012 | 13,0 pts | 5 (0,8) |
| U | ≥ 20 | 3 | 0,4 (2) | 0,81 | 0,67 | 0,82 | 0 | 0 |
| L1 wallet | ≥ 10 | 11 | 21,4 (10) | 0,016 | 0,48 | 0,33 | 12,6 pts | 2 (0,5) |
| L4 co-occurrence | ≥ 5 | 31 | 53,2 (30) | 0,003 | 0,032 | 0,050 | 13,1 pts | 4 (0,9) |
| L5 configuration | ≥ 10 | 11 | 19,0 (10) | 0,039 | 0,057 | 0,011 | 10,0 pts | 2 (0,4) |
| U, cible ×3 | ≥ 5 / ≥ 10 | 33 / 19 | 24,8 / 15,7 | 0,82 / 0,62 | 0,78 / 0,44 | 0,64 / 0,53 | 0 | 1 (1,6) / 1 (0,7) |

Oui pour le ×2 : les équipes diffèrent plus que si toutes avaient la même probabilité, et l'écart
survit à la stratification par jour et par prix (écart-type d'environ 13 points autour de 27 %).
Non pour le ×3 : aucune hétérogénéité, à aucun seuil. Les groupes « wallet » seuls perdent leur
hétérogénéité dans le jour (une équipe fixe vit un jour : équipe et jour se confondent) ; l'union U
la garde.

## 6. Séquences FAIL / PUMP

Groupes U à ≥ 10 lancements éligibles (19 groupes, 349 transitions) :

| | ×2 | ×3 |
|---|---|---|
| P(succès après un succès du même groupe) | 32,0 % | 5,6 % |
| P(succès après un échec) | 25,8 % | 10,9 % |
| écart observé / attendu sous permutation dans le groupe | + 6,2 / + 6,7 pts (p 0,92) | − 5,3 / − 0,1 pt (p 0,34) |
| P(succès après deux échecs) / sinon | 21,3 % / 34,0 % (p 0,85) | 10,2 % / 12,1 % (p 0,70) |
| marché : P(S après S) / P(S après F), tous groupes | 28,7 % / 26,8 % | 5,1 % / 10,1 % |

L'écart S→S contre F→S est exactement celui que produit l'hétérogénéité entre groupes : aucune
dépendance séquentielle à l'intérieur d'un groupe. Les suites visibles (g493 : treize échecs en
quatre heures ; g850 : 2F2F2F22F3F) sont dans le bruit.

## 7. Test « ils font 1 pump sur 3 »

À l'échelle de toutes les équipes, ×2 tombe environ une fois sur 3,6 (équipes fixes 28 %, scripts à
wallets neufs 26 %, population diffuse 33 %), ×3 une fois sur 10, ×5 une fois sur 45 ; aucun ×10
en 1 h dans aucun groupe (multiple maximal 9,4). Mais ce n'est pas une stratégie programmée :
après deux échecs, le succès n'est pas plus probable (21 % contre 34 %), et le taux varie de 0 à
58 % d'une équipe à l'autre. Le « 1 sur 3 » est une moyenne de marché, pas un rythme d'équipe.

## 8. Historique du groupe → prochain lancement

Chronologique, identité causale (union-find incrémental, un lancement devient visible 60 s après
son alerte), issues antérieures utilisées seulement une fois résolues (3 810 s). Prédiction de
groupe = taux antérieur rétréci vers le taux du marché des 24 h précédentes (poids 10).

| identité U, cible ×2 | DISCOVERY | SELECTION | les deux |
|---|---|---|---|
| gain de log-loss sur le marché, ≥ 1 antécédent | − 0,009 [− 0,029, + 0,020] (n 219) | + 0,023 [0,000, + 0,049] (n 128) | + 0,003 [− 0,014, + 0,026] (n 347) |
| idem, ≥ 5 antécédents | − 0,016 [− 0,056, + 0,041] | + 0,038 [+ 0,007, + 0,078] | + 0,003 [− 0,022, + 0,046] |
| idem, ≥ 10 antécédents | − 0,037 [− 0,132, − 0,022] | + 0,046 [+ 0,003, + 0,115] | − 0,015 [− 0,043, + 0,050] |
| AUC du taux antérieur (≥ 5) | 0,43 | 0,66 | 0,56 |
| taux réel par tranche de taux antérieur (< 20 %, 20-30, 30-40, ≥ 40 %) | 32, 32, 24, 17 % | 10, 22, 59, 43 % | |
| cible ×3, ≥ 5 antécédents | − 0,030 [− 0,077, − 0,006] | − 0,032 [− 0,056, − 0,007] | − 0,030 [− 0,058, − 0,013] |

Règles HIGH-CONFIDENCE fixées d'avance (≥ 10 antécédents) :

| règle | DISCOVERY | SELECTION | les deux |
|---|---|---|---|
| HC1 : borne basse de Wilson à 90 % du taux antérieur > marché | 2/26 = 7,7 % (reste 44 %) | 1/3 (reste 44 %) | 3/29 = 10,3 % contre 44,1 %, EV − 55 % |
| HC2 : taux antérieur ≥ 45,8 % (rentabilité) | 0 cas | 1/1 | 1 cas |

Identités L1 et L5 : même inversion (DISCOVERY négatif ou nul, SELECTION positif, total nul).
Le passé d'un groupe ne contient pas d'information stable sur son prochain lancement : il aide sur
une semaine (09-07 → 09-14), nuit sur les deux précédentes, et nuit partout pour le ×3. C'est le
même motif que signal_search : ses historiques passaient sur cette même semaine puis échouaient en
OOS (09-15 → 09-29 ; meilleur p 0,022 contre un seuil de Holm de 0,0167).

## 9. Régimes de performance

Marché, ×2 par semaine : 33 %, 21 %, 32 %, 18 % (p 0,011). Groupes U à ≥ 20 lancements éligibles :

| groupe | ×2 par semaine (succès / lancements) | p (permutation dans le groupe) |
|---|---|---|
| g31 (diffuse) | 18/55, 15/47, 5/13 | 0,92 : stable, au niveau du marché |
| g169 (script, wallets neufs) | 5/11, 0/8, 5/6 | 0,006 : bon, mort, bon |
| g570 (équipe fixe) | 7/18, 0/2 | 0,53 |

Une équipe peut être bonne puis mauvaise : g169 l'a été, sur trois tests. Pour les 22 équipes
fixes, le « régime », c'est l'équipe elle-même : une rafale d'un jour, puis elle disparaît.

## 10. Analyse portefeuille (suiveur fictif, ×2 au relevé suivant, 500 $ ; descriptif)

| groupe | lancements | MFE 1 h médian / moyen / max | < 1,5× | 2-3× | 3-5× | 5-10× | ≥ 10× | net moyen par trade | cumul (en mises) | pire baisse | plus longue série de pertes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| g31 | 115 | 1,79 / 2,16 / 9,4 | 39 | 31 | 17 | 2 | 0 | − 23 % | − 26,3 | 31,2 | 7 |
| g169 | 25 | 1,51 / 2,39 / 8,0 | 11 | 4 | 4 | 3 | 0 | − 10 % | − 2,4 | 7,9 | 5 |
| g570 | 20 | 1,44 / 1,76 / 3,8 | 10 | 6 | 2 | 0 | 0 | − 26 % | − 5,1 | 7,1 | 6 |
| g493 | 13 | 1,36 / 1,39 / 1,8 | 9 | 0 | 0 | 0 | 0 | − 100 % | − 12,9 | 12,9 | 13 |
| g850 | 11 | 2,52 / 2,24 / 3,5 | 3 | 6 | 1 | 0 | 0 | + 20 % | + 2,3 | 1,3 | 1 |
| g745 | 12 | 2,33 / 2,39 / 4,0 | 4 | 5 | 3 | 0 | 0 | + 17 % | + 2,0 | 2,0 | 2 |

Pas de portefeuille de loterie : aucun ×10 en une heure, les multiples se tassent entre 1,4 et 2,5
en médiane, le meilleur à 9,4. Le modèle économique des opérateurs n'est pas « beaucoup de morts
pour quelques ×10 » : d'après les études antérieures (economic_mechanics, exit_destination ; non
remesuré ici), l'opérateur achète environ 78 % de l'offre dans le slot de création et revend à
l'essaim de bots dans les secondes qui suivent l'alerte. Il gagne sur la plupart des lancements, que
le token double ensuite ou non ; l'issue que nous cherchons à prédire n'est pas celle qu'il optimise.

## 11. Effet opérateur contre effet lancement

- L'hétérogénéité U sur ×2 survit à la réattribution dans le jour (p 0,0017) et dans le jour × prime
  (p 0,0012) : elle n'est ni le climat du jour ni le prix d'entrée.
- Modèle logistique mixte (tercile de prime en effet fixe) : écart-type de l'effet groupe 0,68 en
  logit, de l'effet jour 0,43. L'opérateur pèse plus que le jour, sur le ×2 seulement.
- Présence avant le mouvement : entre groupes, taux ×2 et essaim médian à − 10 s, Spearman 0,12 ;
  taux et âge à l'alerte, − 0,03. Les meilleures équipes n'attirent pas l'essaim plus tôt (les
  snipers du bundle sont, par construction, tous au slot de création).

## 12. Réponse à la question centrale

**C — Les mêmes équipes lancent à la fois les bons et les mauvais tokens, et leur historique ne
dit pas lesquels vont réussir.**

- Les acteurs se distinguent : trois modes (équipes fixes de 4 wallets, scripts à wallets neufs,
  population diffuse), reconnus par des liens qui se confirment 45 à 220 fois plus que le hasard.
  Ce n'est donc pas D, et pas E sauf pour le plus gros ensemble (22 % des lancements), qui est une
  population chevauchante et non une équipe.
- Leurs taux de ×2 diffèrent un peu plus que le hasard (écart-type ≈ 13 points, p ≈ 0,001 même à
  jour et prix égaux) : ce n'est pas B au sens strict. Mais aucune différence pour le ×3.
- Ce n'est pas A : aucune équipe n'a à la fois une identité stable, un taux anormal et un
  historique disponible avant le lancement qui le prédise. Toutes les équipes à ≥ 10 lancements
  mélangent échecs et ×2 ; aucune séquence ; l'historique aide une semaine, nuit les deux autres,
  nul au total ; les règles HIGH-CONFIDENCE font 10 % contre 44 % pour le reste.

Pourquoi l'historique échoue alors que les équipes diffèrent : la plupart des équipes vivent un à
trois jours, et l'issue d'un lancement n'est connue qu'une heure après ; quand une équipe a dix
antécédents résolus, sa rafale est souvent finie. Les identités longues (la population diffuse, les
scripts à wallets neufs) ont des taux de marché ou changent de régime (g169). L'opérateur est la
bonne unité pour DÉCRIRE ce marché, pas pour PRÉDIRE le prochain lancement.

Hypothèse à valider (section 15 de la consigne) : aucune. Aucun groupe ne réunit identité
persistante, taux anormal, stabilité temporelle et historique disponible avant chaque lancement.
Le plus proche, l'effet des historiques sur SELECTION, est contredit par DISCOVERY et, d'après
signal_search, par la période suivante. Rien n'est proposé pour VALIDATION ou OOS ; OOS reste vierge.

Limites : 612 issues, 19 groupes à ≥ 10 lancements ; SELECTION déjà lu par signal_search ; le
bénéfice des opérateurs n'est pas mesuré ici (sorties hors de la fenêtre de + 30 s).
