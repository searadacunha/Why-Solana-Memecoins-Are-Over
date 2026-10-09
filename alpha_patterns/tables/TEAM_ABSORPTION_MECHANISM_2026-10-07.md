# La demande externe absorbe-t-elle l'inventaire de l'équipe ? (2026-10-07)

Exploratoire. Tests fixés avant tout calcul d'issue dans `tables/TEAM_ABSORPTION_PREREG_2026-10-07.md`
(amendement 1, écrit avant les issues réelles, après une revue à l'aveugle du code :
`audit/TEAM_ABSORPTION_PREAUDIT_2026-10-07.md`). Données : les 1 015 alertes antérieures au 2026-09-15
(DISCOVERY 643, SELECTION 372), déjà lues par les deux études précédentes. Aucune issue de VALIDATION ni
d'OOS n'est chargée ; les séries de prix sont lues en entier puis filtrées tout de suite sur ces 1 015
lancements. L'étude confirmatoire n'est pas ouverte, OOS reste vierge. Aucune donnée nouvelle, aucun
réseau. Chiffres : `tables/team_absorption.json` et `tables/team_absorption_checks.json` ; code :
`code/feat_48_absorption.py` (mesures, sans issue) et `code/mech_48_absorption.py` (tests) ; registre :
452 comparaisons sur données réelles pour ce calcul et 22 pour un contrôle post hoc ; le registre
d'alpha_patterns en compte 31 656 419 au total (Bonferroni 1,6e-9). Les q de ce rapport sont des BH à l'intérieur des familles pré-enregistrées ;
aucun p ici n'approche le seuil du registre.

Labels. **Explicatif** : Y2, ×2 confirmé en 1 h depuis une entrée à + 5 s (612 lancements éligibles, 168
GOOD, 27,5 %) ; il sert à décrire. **Tradable** : Y2_T, même définition avec l'entrée au moment T de la
décision (T = 5, 10, 20, 30 s ; 612 éligibles à + 5 s, 613 aux autres moments ; 27,5 %, 27,1 %, 24,8 %, 24,5 % de ×2) ; les mesures
d'une décision à T s'arrêtent à T − 3 s (marge pour le retard de 1 à 2 s du détecteur, section 9).
Intra-équipe : 456 lancements de 33 équipes U à ≥ 5 lancements éligibles (125 GOOD, 331 BAD).

## 1. Réponses courtes

| question | réponse |
|---|---|
| 1. Les GOOD ont-ils plus de demande externe que les BAD ? | **Un peu, et tard.** Avant l'entrée (alerte et + 2 s), la différence est minime et ne tient pas : 42 contre 40 acheteurs externes à + 2 s, 8,8 contre 8,4 SOL. À + 29 s, l'écart grandit (37,8 contre 32,4 SOL achetés, 15,4 contre 12,9 SOL sur les 10 dernières secondes), avec une AUC intra-équipe d'environ 0,60 (descriptif : à + 29 s, la mesure contient déjà une partie du mouvement de prix qui définit le label). |
| 2. Cette différence existe-t-elle à l'intérieur des mêmes équipes ? | **À + 29 s, en descriptif seulement, et en partie mécanique** : le rapport demande / inventaire est plus haut sur les GOOD que sur les BAD dans 12 équipes sur 13 (test du signe pré-enregistré, p nominal 0,003, non corrigé) ; mais à + 29 s le prix après l'entrée fait partie du label, et le test « à prix égal » ne passe pas. À + 2 s, c'est l'inverse dans 9 équipes sur 13. Chez les vraies équipes (sans la population diffuse g31), la vitesse de la demande à + 17 et + 27 s donne une AUC intra-équipe de 0,61 à 0,65 pour une entrée à + 20 ou + 30 s (piste post hoc née d'une sensibilité, p nominaux, non significative sur SELECTION seul, hors classement ; section 7). |
| 3. À quel moment devient-elle observable ? | Elle se dessine entre + 10 et + 30 s, en descriptif seulement (après l'entrée à + 5 s, ces mesures contiennent une partie du chemin de prix qui fait le label) (AUC intra-équipe du volume externe : 0,55 à + 4 s, 0,58 à + 19 s, 0,59 à + 29 s). Mais la vraie séparation du prix vient bien plus tard : 30 s après l'entrée, les GOOD sont à × 1,09 et les BAD à × 1,01 en médiane ; à 2 min, × 1,27 contre × 0,96 ; à 5 min, × 1,55 contre × 0,64. Le ×2 confirmé arrive une médiane de 375 s après l'entrée. |
| 4. Peut-on détecter un GOOD avant que le mouvement soit réalisé ? | **Non, pas de façon démontrée.** Dans la famille tradable (10 métriques × 4 moments), rien ne passe (meilleur q 0,91), et dans la famille pré-enregistrée, toutes équipes comprises, la demande vue à + 27 s ne prédit plus le ×2 depuis + 30 s (M7 : AUC intra-équipe 0,52, AUC poolée 0,49). Seule piste : chez les vraies équipes, la vitesse de la demande par rapport à l'équipe elle-même (AUC 0,61 à 0,65, même sens sur les deux blocs, non significative sur SELECTION seul, post hoc). |
| 5. Le ratio demande / inventaire explique-t-il le ×2 ? | **Non démontré.** Après coup, association faible (12 équipes sur 13 à + 29 s), que le test « à prix égal » ne distingue pas du mouvement de prix (AUC 0,58, p 0,14) ; avant, non. Aux moments de décision, la demande externe ne couvre que 3 % (+ 2 s) à 11 % (+ 27 s) de la valeur de l'inventaire. |
| 6. Existe-t-il une règle économiquement exploitable ? | **Non.** Aucune des 5 règles à seuils fixés n'atteint 45,8 % avec assez d'observations sur DISCOVERY et sur SELECTION ; le net moyen à 500 $ est négatif partout sauf sur 12 cas. |
| 7. Pourquoi l'hypothèse échoue-t-elle ? | Parce que la phase d'absorption n'a pas encore commencé quand on peut décider. À + 30 s, l'équipe n'a vendu que ~4 % de son inventaire ; les wallets de sortie commencent à vendre une médiane de 81 s après le transfert (exit_destination, autre échantillon) et le ×2 confirmé tombe entre 2 et 25 minutes après l'entrée (10e et 90e centiles), hors de ce que l'on voit. Ce qui est visible tôt est surtout l'essaim de bots récurrents, autant sur les GOOD que sur les BAD, et une demande trop petite face à l'inventaire. Détail en section 10. |

**Classement selon la règle fixée d'avance : D** (« hypothèse rejetée » au sens de la règle : aucune
métrique de demande ne passe), c'est-à-dire que l'absorption OBSERVABLE avant la décision n'est pas
détectée, sans être démontrée absente (puissance non mesurée). Aucune métrique de demande ne passe, ni dans la famille d'avant l'entrée, ni dans la
famille tradable, ni dans les tests « à prix égal ». Nuances : à + 29 s, la demande est un peu plus forte sur
les GOOD (12 équipes sur 13, AUC 0,60), mais à cette coupure le prix après l'entrée fait partie du label,
et le seul test retenu pour la classe C (« à prix égal ») ne passe pas ; et, hors classement,
chez les vraies équipes, la vitesse de la demande à + 17 / + 27 s donne une AUC intra-équipe de 0,61
à 0,65 même pour une entrée tardive, ce qui ressemblerait à la classe B du classement si cela se confirmait (post hoc,
non significatif sur SELECTION seul). Et l'absorption au sens
propre (pendant la liquidation, qui commence une à quelques minutes après la création) n'est pas
mesurable avec ces données :
elle n'est ni démontrée ni réfutée.

## 2. Le mécanisme reconstruit, lancement par lancement

Fenêtre observée pour chaque lancement : toutes les transactions réussies du token, de la création à
l'alerte + 30 s (308 520 transactions ; les 195 669 signatures sans détail sont des transactions
échouées, non détaillées par le collecteur). Au-delà de + 30 s : seulement les relevés de prix.

Chronologie médiane (lancements intra-équipe, GOOD / BAD) :

| étape | quand | GOOD | BAD |
|---|---|---|---|
| bundle : les snipers achètent dans le slot de création | 0 s | 77,7 % de l'offre | 77,8 % |
| premier transfert d'un sniper vers un wallet de sortie (≥ 0,1 % de l'offre) | depuis la création | 8 s (98 / 125) | 7 s (239 / 331) |
| alerte du détecteur | depuis la création | 12,6 s | 12,3 s |
| première vente de l'équipe (snipers, créateur ou wallets de sortie) | depuis l'alerte | + 8,8 s (107 / 125) | + 8,4 s (282 / 331) |
| part de l'inventaire vendue à création + 30 s / + 40 s | | 2,0 % / 4,6 % (+ 40 s : 78 sur 125 mesurables) | 1,8 % / 4,5 % (+ 40 s : 213 sur 331) |
| acheteurs externes à l'alerte / + 2 s / + 29 s | | 37 / 42 / 86 | 35 / 40 / 84 |
| première vente des wallets de sortie | une médiane de 81 s après le transfert (p25 35 s, p90 330 s ; exit_destination, autre échantillon, contexte cité, non remesuré ici) | | |
| prix 30 s / 60 s / 2 min / 5 min après l'entrée (médiane) | | × 1,09 / 1,16 / 1,27 / 1,55 | × 1,01 / 1,00 / 0,96 / 0,64 |
| part ayant touché × 2 dans les 60 s / 2 min / 5 min après l'entrée | | 5,6 % / 19,2 % / 56,8 % | 0 % / 0,9 % / 7,3 % |
| ×2 confirmé (deux relevés) depuis l'entrée | GOOD seulement, n 168 | 10e, 25e, 50e, 75e, 90e centiles : 118 / 162 / 375 / 815 / 1 503 s ; 1,2 % en 30 s, 2,4 % en 60 s, 10,7 % en 2 min, 42,3 % en 5 min | |

Ce qui ressort : jusqu'à + 30 s, les GOOD et les BAD d'une même équipe ont en médiane le même inventaire,
le même nombre de wallets de sortie (4) et des délais de transfert et de première vente proches. La
séparation du prix apparaît ensuite ; ce qui la produit (liquidation, nouveaux acheteurs) n'est pas
observé ici.

## 3. L'inventaire à absorber (GOOD contre BAD dans la même équipe, médianes)

| mesure | GOOD | BAD |
|---|---|---|
| tokens contrôlés par les snipers (part de l'offre) | 77,7 % | 77,8 % |
| valeur de l'inventaire au prix d'alerte | 294 SOL | 297 SOL |
| concentration (HHI entre snipers) | 0,379 | 0,378 |
| wallets de sortie à + 29 s | 4 | 4 |
| délai création → premier transfert | 8 s | 7 s |
| délai alerte → première vente de l'équipe | 8,8 s | 8,4 s |
| part vendue par l'équipe à + 2 s / + 17 s / + 27 s depuis l'alerte | 0 / 1,8 % / 3,7 % | 0 / 1,6 % / 4,3 % |
| SOL sortis par l'équipe à + 27 s | 18,4 | 20,2 |

L'inventaire reconstruit égale la part d'offre mesurée en direct par le détecteur sur les 1 015
lancements (écart maximal 0,012). La part vendue n'est mesurable que jusqu'à + 30 s après l'alerte,
soit environ + 42 s après la création : les horizons de 60 et 90 s demandés ne sont pas observables
sans nouvelle collecte. Côté offre, aucune différence détectée dans les familles pré-enregistrées
(vitesse de vente M5 : AUC intra-équipe 0,51 à 0,55 à tous les moments, rien ne passe) ; post hoc,
sans g31, l'équipe vend un peu plus sur ses GOOD à + 27 s (section 7).

## 4. La demande externe

Acheteurs externes = wallets hors équipe (snipers, créateur, wallets de sortie) qui achètent après le
slot de création ; les achats « buy-and-burn » d'un service unique (978 lancements, environ 1,9 SOL
médian par lancement à + 27 s) sont mis à part. Médianes GOOD / BAD :

| moment | acheteurs (M1) | SOL achetés (M2) | SOL sur 10 s (M3) | accélération (M4) | part de bots récurrents (M9) |
|---|---|---|---|---|---|
| alerte − 1 s | 37 / 35 | 7,2 / 7,1 | 4,7 / 4,3 | 13 / 13 | 0,84 / 0,82 |
| + 2 s | 42 / 40 | 8,8 / 8,4 | 3,8 / 3,8 | − 4 / − 2 | 0,81 / 0,79 |
| + 7 s | 51 / 48 | 11,7 / 10,9 | 3,7 / 3,5 | − 9 / − 9 | 0,74 / 0,72 |
| + 17 s | 70 / 64 | 18,9 / 18,0 | 7,4 / 5,3 | 0 / − 1 | 0,64 / 0,60 |
| + 27 s | 85 / 80 | 34,1 / 30,2 | 15,4 / 11,5 | 1 / 1 | 0,54 / 0,51 |

Avant l'entrée, environ 80 % des acheteurs externes (médianes 0,79 à 0,84) sont des bots déjà vus comme
acheteurs externes sur au moins 5 lancements antérieurs, autant sur les GOOD que sur les BAD. La demande « nouvelle » monte après + 10 s, un peu plus vite sur les GOOD.

AUC intra-équipe contre Y2 (explicatif ; familles BH d'avant l'entrée : 19 tests ; 413 lancements de 28 équipes
ayant au moins un GOOD et un BAD, 125 GOOD, 3 642 paires GOOD-BAD dont 80 % dans g31) :

| métrique | alerte − 1 s | + 2 s | + 4 s | + 9 s | + 19 s | + 29 s |
|---|---|---|---|---|---|---|
| M1 acheteurs | 0,60 (p 0,027 ; q 0,41) | 0,57 | 0,54 | 0,55 | 0,54 | 0,53 |
| M2 SOL achetés | 0,59 (p 0,057) | 0,57 | 0,55 | 0,55 | 0,58 | 0,59 |
| M3 SOL sur 10 s | 0,56 | 0,52 | 0,50 | 0,50 | 0,57 | 0,57 |
| M7 demande / inventaire | 0,56 | 0,55 | 0,54 | 0,54 | 0,58 | 0,60 |
| M8 absorption | 0,55 | 0,54 | 0,52 | 0,52 | 0,56 | 0,56 |
| M5 part vendue par l'équipe | 0,51 | 0,51 | 0,52 | 0,51 | 0,51 | 0,51 |

Colonnes + 4 à + 29 s : descriptives, sans q (le chemin du prix après l'entrée fait partie du label).
La meilleure valeur d'avant l'entrée (M1 à l'alerte, 0,60) s'inverse sur SELECTION (DISC 0,64, SEL 0,45)
et disparaît sans la population diffuse g31 (0,48), qui porte 80 % des paires : c'est l'essaim déjà vu
dans les études précédentes, pas un effet d'équipe.

## 5. Le rapport demande / inventaire

| moment | M7 = SOL externes / valeur de l'inventaire (GOOD / BAD) | M8 = achats externes / (ventes + 1 SOL) (GOOD / BAD) |
|---|---|---|
| alerte − 1 s | 0,025 / 0,025 | 1,51 / 1,41 |
| + 2 s | 0,030 / 0,030 | 1,39 / 1,41 |
| + 17 s | 0,057 / 0,062 | 1,25 / 1,18 |
| + 27 s | 0,110 / 0,099 | 1,17 / 1,10 |

Aux moments où l'on peut décider, la demande externe n'a payé que 3 à 11 % de ce que vaut l'inventaire :
l'essentiel reste à vendre. Les acheteurs paient plus que ce qui est vendu (M8 > 1) simplement parce
que l'équipe n'a presque rien vendu.

Test « la demande explique-t-elle au-delà du prix ? » (à + 29 s, AUC intra-équipe à l'intérieur des
strates équipe × tercile du mouvement de prix ; 342 lancements, 47 strates) :

| métrique | AUC | DISC / SEL | p | q |
|---|---|---|---|---|
| M2 SOL achetés | 0,565 | 0,557 / 0,582 | 0,21 | 0,21 |
| M7 demande / inventaire | 0,576 | 0,566 / 0,582 | 0,14 | 0,21 |
| M8 absorption | 0,566 | 0,573 / 0,492 | 0,19 | 0,21 |

Même sens sur les deux blocs pour M2 et M7, mais pas significatif : une information de la demande
au-delà du prix déjà monté n'est pas détectée ici (342 lancements, 47 strates ; puissance non mesurée
pour ce test).

## 6. GOOD contre BAD, équipe par équipe

13 équipes ont au moins 3 GOOD et 3 BAD (médianes GOOD / BAD ; à + 29 s sauf mention) :

| équipe | GOOD / BAD | inventaire (SOL) | part vendue M5 | acheteurs M1 | SOL externes M2 | M7 | M8 | M7 à + 2 s |
|---|---|---|---|---|---|---|---|---|
| g31 (population diffuse) | 38 / 77 | 279 / 282 | 0,058 / 0,058 | 86 / 80 | 42,7 / 32,6 | 0,158 / 0,117 | 1,18 / 1,11 | 0,035 / 0,035 |
| g169 (script) | 10 / 15 | 883 / 868 | 0,020 / 0,017 | 147 / 113 | 20,1 / 10,9 | 0,021 / 0,015 | 0,96 / 0,90 | 0,001 / 0,001 |
| g570 | 7 / 13 | 281 / 282 | 0,096 / 0,098 | 96 / 85 | 77,3 / 36,3 | 0,275 / 0,121 | 1,27 / 1,02 | 0,058 / 0,034 |
| g606 | 4 / 10 | 296 / 298 | 0,062 / 0,066 | 80 / 98 | 53,3 / 41,8 | 0,180 / 0,142 | 1,31 / 1,04 | 0,047 / 0,047 |
| g811 | 7 / 7 | 296 / 304 | 0,062 / 0,071 | 89 / 87 | 33,4 / 35,9 | 0,124 / 0,112 | 1,22 / 1,20 | 0,019 / 0,026 |
| g368 | 3 / 9 | 318 / 299 | 0,025 / 0,033 | 55 / 92 | 30,5 / 30,1 | 0,106 / 0,103 | 1,64 / 1,56 | 0,036 / 0,036 |
| g679 | 4 / 8 | 273 / 288 | 0,117 / 0,109 | 96 / 121 | 65,3 / 64,8 | 0,236 / 0,232 | 1,13 / 1,07 | 0,057 / 0,046 |
| g745 | 7 / 5 | 314 / 314 | 0,023 / 0,000 | 49 / 58 | 13,8 / 12,1 | 0,042 / 0,041 | 0,71 / 1,59 | 0,029 / 0,035 |
| g855 | 5 / 7 | 283 / 290 | 0,028 / 0,056 | 81 / 103 | 26,8 / 38,8 | 0,101 / 0,134 | 1,23 / 1,23 | 0,033 / 0,056 |
| g850 | 6 / 5 | 274 / 282 | 0,017 / 0,030 | 94 / 98 | 19,3 / 14,7 | 0,071 / 0,054 | 1,19 / 1,49 | 0,044 / 0,021 |
| g344 | 4 / 4 | 998 / 932 | 0,009 / 0,015 | 54 / 92 | 39,7 / 44,0 | 0,048 / 0,045 | 0,99 / 0,82 | 0,006 / 0,000 |
| g246 | 4 / 3 | 298 / 292 | 0,099 / 0,065 | 112 / 70 | 84,9 / 48,3 | 0,285 / 0,165 | 1,19 / 1,50 | 0,030 / 0,042 |
| g931 | 4 / 3 | 314 / 295 | 0,052 / 0,030 | 117 / 106 | 52,7 / 31,7 | 0,165 / 0,107 | 1,50 / 1,38 | 0,026 / 0,026 |

Tests du signe pré-enregistrés (à + 29 s, 13 équipes, 6 tests) : M7 plus haut sur les GOOD dans 12
équipes (p 0,003) ; M2 dans 10 (p 0,09) ; M8 dans 9 (p 0,27) ; M1 dans 6 (p 1,0) ; part vendue M5 dans 6
(p 1,0) ; inventaire dans 5 (p 0,58).

Une règle du type « cette équipe fait un GOOD quand X acheteurs externes arrivent avant que son
inventaire soit libéré » n'est pas présente : à + 2 s, M7 est plus haut sur les GOOD dans 4 équipes
seulement et plus bas dans 9 (les égalités apparentes du tableau viennent de l'arrondi). Le phénomène commun aux équipes n'apparaît qu'à + 29 s, et en SOL achetés
plutôt qu'en nombre d'acheteurs (M1 : 6 sur 13). À + 29 s, une partie de ce volume est le mouvement de
prix lui-même (les GOOD sont à × 1,06 contre × 1,03 depuis l'alerte, M10), et le test « à prix égal »
ne confirme pas d'effet propre.

## 7. Moment de la décision

Famille tradable : 10 métriques × 4 moments contre Y2_T, mesures à T − 3 s, 40 tests :

| moment de décision (lancements intra-équipe testés) | ×2 depuis l'entrée à T (DISC / SEL) | meilleure métrique (AUC intra-équipe, p, q) | M7 demande / inventaire | rien ne passe |
|---|---|---|---|---|
| + 5 s (413) | 25,1 % / 30,9 % | M4 accélération 0,42 (p 0,088, q 0,91) | 0,55 (p 0,28) | oui |
| + 10 s (427) | 25,5 % / 29,3 % | M1 acheteurs 0,56 (p 0,19) | 0,52 (p 0,65) | oui |
| + 20 s (401) | 24,2 % / 25,7 % | M10 prix déjà monté 0,39 (p 0,024, q 0,91) | 0,53 (p 0,60) | oui |
| + 30 s (398) | 24,5 % / 24,5 % | M10 prix déjà monté 0,43 (p 0,15) | 0,52 (p 0,62) | oui |

Le taux de ×2 baisse quand on entre plus tard (27,5 % à + 5 s, 24,5 % à + 30 s), et aucune information
accumulée entre-temps ne compense. Une piste nominale, non robuste, va dans le sens contraire d'un
signal d'achat : à + 20 s, un prix déjà monté annonce MOINS de ×2 depuis + 20 s (AUC 0,39, même sens sur
les deux blocs, q 0,91, disparaît sans la population diffuse : 0,47).

Sensibilités (B = 2 000, hors classement). Mesures à T − 1 s : 1 p ≤ 0,05 sur 40. Sans les lancements à
plus de 10 wallets de sortie : 0 sur 40. **Sans la population diffuse g31 : 7 p ≤ 0,05 sur 40 (2
attendus)**, toutes aux décisions tardives. Contrôle post hoc, déclaré après lecture de la sensibilité
et inscrit au registre (script `code/mech_48b_posthoc_nobig.py`, sortie
`tables/team_absorption_posthoc_nobig.json`), bloc par bloc :

| métrique, décision | AUC intra-équipe (282 à 285 lancements, 25 équipes) | DISCOVERY | SELECTION | AUC poolée (équipes mêlées) |
|---|---|---|---|---|
| M3 vitesse de la demande, + 20 s | 0,61 | 0,65 (p 0,012 ; 15 équipes) | 0,59 (p 0,18 ; 12 équipes) | 0,52 |
| M3 vitesse de la demande, + 30 s | 0,65 | 0,65 (p 0,026) | 0,61 (p 0,14) | 0,53 |
| M4 accélération des acheteurs, + 20 s | 0,62 | 0,71 (p 0,001) | 0,59 (p 0,18) | 0,55 |
| M2 SOL achetés, + 30 s | 0,61 | 0,64 (p 0,033) | 0,53 (p 0,70) | 0,50 |
| M7 demande / inventaire, + 30 s | 0,61 | 0,63 (p 0,044) | 0,54 (p 0,58) | 0,48 |
| M5 part vendue par l'équipe, + 30 s | 0,60 | 0,58 (p 0,22) | 0,61 (p 0,13) | 0,47 |
| M6 SOL sortis par l'équipe, + 30 s | 0,60 | 0,57 (p 0,27) | 0,60 (p 0,18) | 0,50 |

Lecture : chez les vraies équipes, quand la demande externe s'accélère entre + 10 et + 30 s (et que
l'équipe vend davantage dedans), le ×2 depuis une entrée tardive est un peu plus fréquent. Le sens tient
sur les deux blocs pour les 7 pistes (nettement pour M3, M4, M5 et M6, SELECTION de 0,59 à 0,61 ; à peine
pour M2 et M7, 0,53 et 0,54), mais SELECTION seul n'est jamais significatif ; comme ces pistes ont été
choisies sur les deux blocs réunis, ce même sens n'est pas une réplication indépendante (p nominaux,
sans correction pour les 40 sensibilités d'où elles sortent ; meilleur q BH sur ces 40 : 0,10). L'effet
n'existe que relativement à l'équipe : mêlées, les équipes donnent une AUC poolée de 0,47 à 0,55. Un seuil
absolu ne marche donc pas : la règle R3 (vitesse ≥ 80e centile) fait, chez ces équipes, 31 % de ×2
contre 22 % de base sur DISCOVERY à + 20 s (n 61), mais 26 % contre 26 % sur SELECTION (n 57), net
négatif. Rien de cela n'entre dans le classement : c'est une piste née des données.

## 8. Les scénarios

| scénario de la consigne | ce que disent les données | verdict |
|---|---|---|
| A. GOOD = forte demande externe AVANT la liquidation | avant l'entrée, différence minime (42 contre 40 acheteurs), non robuste (inversée sur SELECTION, absente sans g31) ; à + 2 s, aucun motif commun aux équipes | non soutenu |
| B. GOOD = demande qui arrive APRÈS la liquidation | la liquidation et le ×2 tombent après + 30 s (×2 médian à 375 s) ; on ne voit que le début : la demande des GOOD accélère un peu plus entre + 10 et + 30 s (M3 à + 27 s : 15,4 contre 11,5 SOL), 12 équipes sur 13 à + 29 s, et chez les vraies équipes cette accélération sépare encore un peu pour une entrée tardive (post hoc) | compatible, le plus cohérent, non testable au-delà de + 30 s |
| C. GOOD / BAD déterminé avant que les ventes commencent | avant la première vente de l'équipe (+ 8,7 s en médiane), rien ne sépare dans l'équipe : ni inventaire, ni configuration (étude précédente), ni demande | non soutenu |
| D. autre mécanisme | aucun mécanisme côté offre détecté jusqu'à + 30 s dans les familles pré-enregistrées (M5) ; post hoc sans g31, l'équipe vend un peu plus sur ses GOOD à + 27 s (AUC 0,60, non significatif sur SELECTION) ; un prix déjà monté à + 20 s annonce moins de ×2 ensuite (non robuste) | rien d'établi |

Le scénario B de la consigne (demande après la liquidation) est le plus cohérent avec l'ensemble des
faits. Interprétation, non testée ici : le résultat se jouerait après + 30 s, pendant puis après la
liquidation, le ×2 confirmé tombant entre 2 et 25 minutes après l'entrée (10e et 90e centiles), selon
que de nouveaux acheteurs arrivent ou non. Cette étude ne voit pas cette phase, et ce qu'elle voit
avant ne suffit pas à l'annoncer.

## 9. Rentabilité

Règles à seuils fixés d'avance, évaluées à T − 3 s contre le ×2 depuis l'entrée à T, sur tous les
lancements éligibles ; trade déclaré (prise de profit à ×2 au relevé suivant, sortie à 1 h, 500 $, coûts
inchangés). Seuil de rentabilité de référence : 45,8 %.

| règle | T | DISC : n, ×2, net moyen | SEL : n, ×2, net moyen | exploitable ? |
|---|---|---|---|---|
| R1 absorption ≥ 1 | 5 / 10 / 20 / 30 | 232, 27,2 % ; 250, 25,6 % ; 242, 23,6 % ; 223, 22,9 % (net − 32 à − 44 %) | 162, 29,6 % ; 161, 30,4 % ; 165, 25,5 % ; 157, 23,6 % | non (taux de base) |
| R2 demande / inventaire ≥ 0,25 | 5 | 10, 40,0 %, − 10 % | 2, 1 sur 2 | non (n trop petit) |
| R2 | 10 | 10, 50,0 %, + 18 % | 2, 1 sur 2, − 13 % | non : 12 cas en tout, 2 sur SELECTION |
| R2 | 20 / 30 | 14, 35,7 % ; 34, 23,5 % | 4, 25 % ; 25, 16,0 % | non |
| R3 vitesse ≥ 80e centile | 5 / 10 / 20 / 30 | 24,0 % ; 26,8 % ; 30,0 % ; 21,3 % (n 75 à 82) | 29,3 % (58) ; 20,0 % (65) ; 25,0 % (64) ; 24,0 % (50) | non |
| R4 l'équipe vend et le prix tient | 5 / 10 / 20 / 30 | 31,6 % (19) ; 46,2 % (13) ; 35,5 % (31) ; 23,3 % (86) | 25 % (4) ; 12,5 % (8) ; 6,5 % (31) ; 19,1 % (68) | non (s'effondre sur SELECTION) |
| R5 l'équipe n'a rien vendu et demande forte | 5 / 10 / 20 / 30 | 29,3 % (140) ; 26,4 % (110) ; 25,0 % (52) ; 31,2 % (16) | 32,0 % (125) ; 32,6 % (86) ; 30,2 % (43) ; 33,3 % (21) | non (≈ taux de base, net négatif) |

Aucune règle n'atteint A (≥ 45,8 % sur les deux blocs, ≥ 15 cas par bloc, net positif). Les
sensibilités avec les achats « buy-and-burn » ajoutés à la demande ne changent rien (R1 23 à 32 % ; R2
identique à + 5 et + 10 s). Le net moyen des lancements de base va de − 22 % à − 42 % par trade.

## 10. Pourquoi l'hypothèse d'absorption échoue ici

1. **Trop tôt.** Au moment où l'on peut décider (jusqu'à + 30 s), l'équipe n'a vendu qu'environ 4 % de
   son inventaire et la demande externe n'en a payé que 3 à 11 %. Le test d'absorption n'a pas encore
   eu lieu : il commencerait quand les wallets de sortie se mettent à vendre, une médiane de 81 s après
   le transfert (première vente, exit_destination), et le ×2 confirmé arrive une médiane de 6 minutes
   après l'entrée.
2. **L'offre ne varie pas de façon détectable.** Inventaire (78 % de l'offre, ~295 SOL), concentration,
   nombre de wallets de sortie, délais et vitesse de vente ont des médianes proches pour les GOOD et les
   BAD d'une équipe, et aucun test pré-enregistré ne passe (post hoc sans g31, M5 et M6 à + 27 s donnent
   0,60, non significatif par bloc). Cette étude ne dit pas si l'absorption, si elle décide, passe par
   l'offre ou par la demande à venir : ce qui se passe après + 30 s n'est pas observé.
3. **La demande visible tôt n'est pas la bonne.** Avant l'entrée, environ 80 % des acheteurs externes
   (médianes 0,79 à 0,84) sont des bots déjà vus sur au moins 5 lancements antérieurs. La demande qui distingue les
   GOOD (achats plus gros et plus rapides, en SOL plutôt qu'en nombre de wallets) n'apparaît qu'après
   + 10 à + 20 s. À ce moment, une partie est déjà dans le prix : entrer à + 30 s fait perdre ce qui
   séparait (AUC 0,60 vu depuis + 5 s, 0,52 depuis + 30 s).
4. **Trop peu pour une règle.** Même la seule règle au-dessus du seuil sur les deux blocs réunis (R2 à
   + 10 s, 6 sur 12) repose sur 12 cas, dont 2 sur SELECTION ; R4 à + 10 s fait 46,2 % sur DISCOVERY
   seul (6 sur 13) mais 1 sur 8 sur SELECTION.

Ce qui n'est pas exclu : la piste post hoc de la section 7 (accélération de la demande relative à
l'équipe, + 17 à + 27 s), à tester seulement en prospectif avec une définition fixée d'avance et
l'identité d'équipe causale ; une vraie dépendance à l'absorption pendant la liquidation (qui commence une à quelques minutes après
la création),
qui demanderait des fenêtres de transactions jusqu'à plusieurs minutes après l'alerte (nouvelle
collecte, non faite ici) ; des effets intra-équipe d'AUC jusqu'à 0,68 au moins (puissance non mesurée
ici ; seul ordre de grandeur, l'étude précédente, sur une autre famille de tests et avec la même
statistique, retrouvait un effet d'AUC 0,68 dans 47 mondes sur 50 et n'excluait pas les AUC entre 0,5
et 0,68).

## 11. Contrôles

| contrôle | résultat |
|---|---|
| K1 horodatages | 308 520 transactions ; aucune avant la création, aucune après la fenêtre, aucune inversion slot / heure de plus d'une seconde |
| retard du détecteur (audit) | le prix d'alerte égale l'état du pool à t_alerte − 2 s pour 58,5 % des lancements : mesures arrêtées à T − 3 s ; T − 1 s en sensibilité |
| K2 ventes de l'équipe après l'entrée | 58 % du SOL sorti par l'équipe (équipe finale, jusqu'à + 29 s) l'est après + 4 s ; 848 lancements sur 1 015 ont une vente de l'équipe avant + 29 s |
| K3 acheteurs externes vraiment externes | part du volume externe venant de snipers de la même équipe 0,15 à 0,35 %, de snipers d'autres équipes 0,8 à 1,8 %, de wallets qui rejoignent l'équipe plus tard ≤ 0,04 %, de financeurs des snipers 0 |
| K4 fuite | les enregistrements sont filtrés sur bt ≤ t_alerte + c avant tout calcul (le garde ajouté dans le code relit des listes déjà filtrées et ne contrôle rien de plus) ; l'entrée tradable est refusée avant T ; Y2 à + 5 s reproduit exactement le label de l'étude |
| inventaire | égal à la part mesurée en direct par le détecteur sur 1 015 lancements (écart ≤ 0,012) après deux corrections faites avant toute issue |
| poussière | des transferts de 1 token vers des centaines d'adresses sont ignorés (seuil 0,1 % de l'offre) |
| K5 DISCOVERY / SELECTION | séparés partout ; l'effet d'avant l'entrée s'inverse sur SELECTION, il est donc non robuste |

## 12. Outils

Graphify : non utilisé. Un graphe équipe → inventaire → wallets de sortie → acheteurs externes n'aurait
rien montré de plus : 4 wallets de sortie par lancement en médiane, pour les GOOD comme pour les BAD,
et des acheteurs externes dominés par des bots récurrents. OmniRoute et Ponytail : non utilisés, aucune configuration
modifiée.

## Notes sur les données et écarts

- Mêmes équipes U, mêmes 1 015 lancements, même label Y2 que les études précédentes ; SELECTION avait
  déjà été lu (signal_search le 02/10, forensique des opérateurs le 06/10, rythme des équipes le 07/10).
- Revue avant calcul : 0 BLOQUANT, 3 MAJEUR (retard du détecteur, famille explicative contaminée par le
  label, achats buy-and-burn), 10 MINEUR ; tous traités avant les issues réelles (amendement 1).
- `exit_destination` n'est pas relu (il mélange des événements postérieurs au 15/09) ; seul son délai
  médian publié (81 s) est cité.
- Les métriques de demande et l'inventaire en SOL ont quelques valeurs extrêmes réelles (un lancement à
  7 900 SOL d'achats externes en 27 s, le pool passant à 539 SOL) ; les tests sont des AUC sur rangs.
- Contrôle post hoc (sensibilité sans la population diffuse, bloc par bloc, règle R3 dans cette
  sous-population) : déclaré après lecture, inscrit au registre (22 comparaisons), hors classement.
  Écart au pré-enregistrement, qui excluait toute autre recherche après le rapport : ce contrôle a été
  lancé après un premier jet du rapport, qui avait écrit à tort « rien de nouveau » pour cette
  sensibilité.
- La puissance n'a pas été remesurée pour ces familles ; les contrôles synthétiques de l'étude précédente
  (même statistique intra-équipe) servent d'ordre de grandeur.
