# Sortir de la boucle : autopsie de D1 et recherche du mécanisme (2026-10-06)

DISCOVERY seul (363 lancements du régime fin, 91 ×2, 40 ×3, 9 ×5). Aucune lecture de SELECTION,
VALIDATION ni OOS, rien de l'étude confirmatoire, aucun label Pump-Gold. Aucun mining : des
décompositions pré-spécifiées, des trajectoires par groupe, une dizaine de règles à seuils fixes, une
échelle de seuils montrée en entier. Chiffres : `tables/break_the_loop.json`,
`tables/break_the_loop_swarm.npz`, code `code/mech_40_break_the_loop.py` et le script de suivi
(ladders) enregistré au registre (`mechanism_disc`, `mechanism_disc_followup`, exploratoires).

## 1. Pourquoi les recherches précédentes tournaient en rond

- Toutes cherchaient une PROPRIÉTÉ du lancement (une feature, un seuil, une conjonction) sur les
  mêmes 363 lignes, et prenaient le maximum sur des millions de candidats. Le maximum de bruit sur
  cette taille d'échantillon est une précision de 60 à 72 % sur 25 lancements ; tout ce qui a été
  trouvé est à ce niveau ou en dessous. Les contrôles le montrent : issues mélangées, mêmes comptes.
- Les features sont presque toutes des reformulations d'une poignée de quantités : combien de bots ont
  acheté avant l'alerte, à quel prix on entre, quel opérateur a lancé. Les 547 colonnes recombinent
  ces trois axes ; les « interactions » retrouvent leurs copies.
- Personne n'avait regardé la SÉQUENCE : qui arrive quand, avant l'alerte, et ce qui diffère entre
  les lancements qui continuent et les autres. C'est ce que fait ce document.

## 2. Autopsie de D1

D1 = `pg_sync_same_size_pairs ≥ 4` ET `pg_same_slot_max_buyers ≥ 8` ET `g_early_funders_shared > 0`
(seuils = quantiles 65 % de DISCOVERY ; le troisième = au moins deux acheteurs externes partageant un
financeur de genèse). 40 lancements, 16 ×2 (40 % contre 25 %), 9 ×3 (23 % contre 11 %), 17 grappes,
11 jours, EV nette − 12 % par trade à 500 $. Seuils plus stricts : lift ×2 **0,80** (retombe sous 1) ;
plus permissifs : 1,44 ; coupure − 2 s : 1,64. La « robustesse 9/10 » du rapport précédent venait du
×3 et des moitiés ; sur le ×2, D1 ne survit pas à un seuil plus strict.

Ce que les 40 fenêtres montrent (bins en secondes avant l'alerte, moyennes par lancement) :

| groupe | n | achats −30..−20 | achats −20..−10 | achats −10..−5 | achats −5..−2 | wallets cumulés à −1 s | récurrents | indépendants | liés (même financeur) | paires sync −20..−10 | paires sync −10..−2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 ×2 | 16 | 4,7 | 28,2 | 21,1 | 8,5 | 56 | 40 | 11 | 0 | 7,8 | 4,0 |
| D1 échec | 24 | 0,0 | 14,0 | 19,0 | 8,3 | 43 | 40 | 11 | 0 | 2,4 | 20,0 |
| D1 ×3 | 9 | 8,3 | 40,9 | 23,4 | 9,6 | 71 | 46 | 14 | 1 | 12,2 | 4,6 |
| non D1 ×2 | 75 | 0,6 | 13,8 | 12,3 | 5,2 | 33 | 29 | 11 | 0 | 1,6 | 1,4 |
| non D1 échec | 248 | 0,0 | 11,2 | 11,6 | 5,2 | 29 | 24 | 11 | 0 | 1,2 | 2,5 |

(« récurrents » = déjà vus comme acheteurs précoces d'une alerte antérieure ; « indépendants » =
financeur de genèse connu et partagé avec personne, ou wallet trop ancien pour lire sa genèse ;
« liés » = partagent un financeur de genèse avec un autre participant.)

Ce que D1 mesure réellement : **la taille et la précocité de l'essaim de bots récurrents**, pas une
structure de financement. Les acheteurs externes sont, dans tous les groupes, les mêmes ~40 bots
anciens (médiane 39 lancements antérieurs chacun, 1 000 transactions et plus, genèse illisible). Les
wallets « liés » par un financeur sont 0 par lancement en médiane : la condition « financeur
partagé » est satisfaite sur 65 % des lancements par un seul duo de wallets neufs, et seule elle a un
lift de 1,04. Les « paires synchronisées de même taille » sont la signature de l'essaim qui arrive
dans un même slot avec ses tickets standard. La « rafale » (premier slot à ≥ 3 acheteurs de même
taille ou ≥ 2 wallets liés) existe sur 93 % des D1 et se situe au tout début de l'activité externe
(position 0,07 de la fenêtre) : ce n'est pas un événement au milieu d'une trajectoire, c'est le
départ de l'essaim.

## 3. D1 contre les contrôles : la différence est une trajectoire

Entre D1 ×2 et D1 échec, les moyennes finales diffèrent peu (prime d'entrée 3,70 contre 3,78,
acheteurs 50 contre 46, indépendants 11 contre 11) ; ce qui diffère, c'est QUAND l'essaim arrive :

- premier achat externe à − 13,1 s (×2) contre − 11,1 s (échec) ; les ×3 ont déjà 8 achats entre
  − 30 et − 20 s, les échecs 0 ;
- acheteurs déjà présents à − 10 s : 20 contre 14 (×3 : davantage) ; à − 5 s : 38 contre 30 ;
- les paires synchronisées des gagnants sont tôt (− 20..− 10 s : 7,8) et celles des perdants tard
  (− 10..− 2 s : 20) ;
- dans TOUS les groupes l'activité décélère vers l'alerte (achats − 5..− 2 ≈ 40 % de − 10..− 5) : il
  n'y a pas d'accélération avant l'alerte, ni chez les gagnants.

Lecture : un lancement qui continue est un lancement où la vague de bots était plus grosse et plus tôt
par rapport au moment où le détecteur a tiré. Ce « plus tôt » mêle deux choses qu'on ne sépare pas
ici : le lancement a attiré plus vite, et le détecteur a tiré plus tard (âge à l'alerte, tercile
vieux : 28 % de ×2 contre 23 % pour les jeunes).

## 4. Décomposition de D1 (DISCOVERY, seuils de D1 ; A = ≥ 8 acheteurs dans un slot, B = part de tailles répétées ≥ 0,40, C = financeur partagé > 0)

| composant | n | ×2 | lift ×2 | ×3 | lift ×3 | EV 500 $ | grappes |
|---|---|---|---|---|---|---|---|
| A synchronisation seule | 134 | 28 % | 1,13 | 14 % | 1,29 | − 0,28 | 37 |
| B tailles similaires seules | 128 | 30 % | 1,18 | 16 % | 1,49 | − 0,27 | 45 |
| C financeur partagé seul | 235 | 26 % | 1,04 | 12 % | 1,08 | − 0,31 | 68 |
| A + B | 55 | 33 % | 1,31 | 22 % | 1,98 | − 0,24 | 22 |
| A + C | 70 | 29 % | 1,14 | 16 % | 1,43 | − 0,27 | 27 |
| B + C | 79 | 28 % | 1,11 | 20 % | 1,84 | − 0,25 | 35 |
| A + B + C | 29 | 34 % | 1,38 | 31 % | 2,82 | − 0,21 | 12 |
| D1 (paires sync ≥ 4, slot ≥ 8, C) | 40 | 40 % | 1,60 | 23 % | 2,04 | − 0,12 | 17 |
| aucun des trois | 41 | 10 % | 0,39 | 5 % | 0,44 | − 0,62 | 16 |

Le signal ne vient pas du financeur partagé (C n'ajoute rien, ni seul ni en combinaison). Il vient de
A et B ensemble, c'est-à-dire d'un gros slot d'acheteurs aux tickets standard : l'essaim. Et le
résultat le plus net du tableau est négatif : un lancement sans AUCUNE de ces signatures (41 cas)
ne double que 10 % du temps. L'absence d'essaim est un lancement mort.

## 5. Hypothèses mécanistiques (testées, DISCOVERY)

| hypothèse | verdict | ce qui le dit |
|---|---|---|
| H1 un financeur alimente plusieurs wallets pour simuler la demande | non | wallets liés ≈ 0 par lancement ; C seul lift 1,04 |
| H2 un financeur contrôle un groupe qui intervient avant l'expansion | non | idem ; 6 financeurs de D1 sur 11 reviennent sur ≥ 2 lancements, ce sont des lots de wallets neufs d'opérateurs, sans effet mesurable |
| H3 la coordination signale un acteur sophistiqué présent | en partie | l'acteur, c'est l'essaim de bots génériques ; sa présence est universelle, c'est sa TAILLE qui compte |
| H4 le script n'intervient que sur les lancements à demande latente | compatible | les bots filtrent les lancements ; un gros essaim = beaucoup de filtres déclenchés = consensus de bots |
| H5 le financeur partagé est un proxy d'opérateur | oui pour le ×3 | D1 sans la grappe dominante : ×2 44 % (n 18) mais ×3 11 % : tout le ×3 de D1 est un seul opérateur (k:21.13+21.08…, 22 des 40 D1) |
| H6 la synchronisation compte après une phase organique | non | la rafale est au départ de l'activité (position 0,07) dans tous les groupes |
| H7 prédictif seulement si les indépendants continuent d'arriver | non | indépendants après la rafale : médiane 0 partout ; total 11 partout |
| H8 transition coordonné → indépendants → accélération | non | aucune accélération vers l'alerte (ratio 0,36 à 0,5 dans tous les groupes) |
| H9 les wallets coordonnés signalent qu'un seuil de demande va être franchi | compatible | l'échelle de taille d'essaim est monotone sur le ×3 jusqu'à 40 acheteurs ; sur le ×2 elle plafonne à 35 % |
| H10 c'est la POSITION de la coordination qui compte | oui | rafale dans la première moitié de la fenêtre : 28 % (n 89) ; dans la seconde : 12 % (n 24) ; premier achat externe ≤ − 15 s : 33 % (n 57) |

## 6. Transition de régime

Cherchée, pas trouvée. Dans tous les groupes la séquence est : création, bundle, puis une seule
vague de bots récurrents qui démarre entre − 15 et − 10 s et décélère jusqu'à l'alerte ; les wallets
indépendants (≈ 11) arrivent dans la même vague, pas après ; un second groupe de financeur apparaît
sur 2 lancements sur 363. Les règles « rafale puis ≥ 5 indépendants » (n 15, 27 %), « indépendants
qui accélèrent dans les 5 dernières secondes » (n 7, 14 %), « second groupe de financeurs » (n 2,
0 %) ne portent rien. Ce qui sépare les gagnants n'est pas un changement de régime avant l'alerte
mais l'amplitude et l'avance de l'unique vague.

## 7. Analyse des acteurs

- Acheteurs externes des 40 D1 : 1 552 wallet-lancements, 1 549 récurrents (médiane 39 lancements
  antérieurs), 0 neuf, 36 liés par financeur. Leur taux de ×2 antérieur (lancements résolus avant
  l'alerte, porte 1 h) : 0,30, le taux de base. Un wallet « performant » (≥ 3 lancements résolus,
  ≥ 50 % de ×2) est présent sur 57 % des D1 et 54 % des autres : lift 1,11. Les bots ne savent pas
  mieux que nous.
- Financeurs : 11 groupes sur les D1, 6 revus sur ≥ 2 lancements DISCOVERY ; ce sont des lots de
  wallets neufs (2 wallets) que certains opérateurs ajoutent à leurs lancements ; aucun effet.
- Délai entre le premier wallet lié et le ×2 : médiane 565 s (n 7).
- Le groupe reconnaissable qui apparaît avant les succès ×3 de D1 est… l'opérateur dominant du
  snapshot (hypothèse H5), déjà connu : ce n'est pas une découverte exploitable, c'est l'identité de
  celui qui a produit le plus de ×3 pendant les deux semaines de DISCOVERY.

## 8. Points de bascule

| événement | D1 ×2 | D1 échec | non D1 ×2 | non D1 échec |
|---|---|---|---|---|
| premier achat externe (s avant l'alerte, médiane) | − 13,1 | − 11,1 | − 11,9 | − 11,8 |
| rafale (médiane) | − 12,8 | − 9,9 | − 11,2 | − 8,6 |
| 5e wallet indépendant | − 12,9 | − 11,0 | − 11,6 | − 10,9 |
| acheteurs cumulés à − 10 s | 20 | 14 | 14 | 10 |
| acheteurs cumulés à − 5 s | 38 | 30 | 24 | 20 |

Le seul point de bascule observable est le moment où l'essaim dépasse une trentaine de wallets : s'il
est atteint 10 s avant l'alerte, la continuation est plus fréquente. Échelle complète, seuils fixes :

| règle (acheteurs externes déjà entrés) | n | ×2 | lift | ×3 | lift | EV 500 $ | grappes | jours |
|---|---|---|---|---|---|---|---|---|
| ≥ 20 à − 5 s | 205 | 30 % | 1,21 | 12 % | 1,06 | − 0,31 | 44 | 12 |
| ≥ 30 à − 5 s | 112 | 35 % | 1,39 | 16 % | 1,46 | − 0,27 | 28 | 12 |
| ≥ 40 à − 5 s | 54 | 35 % | 1,40 | 24 % | 2,18 | − 0,31 | 18 | 9 |
| ≥ 50 à − 5 s | 20 | 30 % | 1,20 | 20 % | 1,81 | − 0,32 | 7 | 6 |
| ≥ 20 à − 10 s | 95 | 32 % | 1,26 | 16 % | 1,43 | − 0,33 | 26 | 12 |
| **≥ 30 à − 10 s** | **34** | **41 %** | **1,64** | **29 %** | **2,67** | **− 0,17** | **11** | **9** |
| ≥ 40 à − 10 s | 10 | 40 % | 1,60 | 30 % | 2,72 | − 0,19 | 5 | 6 |

Confusions vérifiées : cette quantité est la feature connue `m_buys_10s` (Spearman 0,94 ; `m_buyers`
0,89), que l'étude forensique avait vue répliquer en VALIDATION puis expliquer par le prix et
l'opérateur ; par tercile de prime d'entrée, l'essaim ≥ 40 à − 5 s fait 47 % dans le tercile le moins
cher (n 17, EV − 0,04), 26 % au milieu (n 31), 50 % dans le plus cher (n 6) ; sans la grappe
dominante, ≥ 40 à − 5 s tombe à 32 % (n 31) et D1 garde 44 % sur le ×2 (n 18) mais perd tout son ×3.

## 9. TOP 5 mécanismes

| # | MÉCANISME | OBSERVATION | EXPLICATION POSSIBLE | VARIABLE DIRECTE | VARIABLE DYNAMIQUE | FRÉQUENCE | LIFT DISCOVERY | EV | ROBUSTESSE − 1 s / − 2 s | RISQUE DE CONFUSION | TEST FUTUR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Essaim de bots précoce et gros | ≥ 30 acheteurs externes déjà entrés 10 s avant l'alerte : 41 % de ×2, 29 % de ×3 | les bots récurrents filtrent les lancements ; un gros essaim tôt = beaucoup de filtres déclenchés = demande latente, et le mouvement est déjà lancé quand l'alerte tire | acheteurs cumulés à − 10 s (≈ `m_buys_10s`) | moment où le cumul franchit 30 | 34 / 363 = 9 % des lancements, ≈ 3 par jour actif | ×2 1,64 ; ×3 2,67 | − 17 % par trade à 500 $ (seuil de rentabilité 45,8 %) | ne dépend pas de la coupure (mesuré à − 10 s) ; échelle monotone de 20 à 40 | prime d'entrée (l'essaim pousse le prix), âge à l'alerte (latence du détecteur), opérateur dominant | règle pré-enregistrée, VALIDATION puis OOS |
| 2 | Position de la rafale dans la fenêtre | rafale dans la première moitié : 28 % ; dans la seconde : 12 % (n 24) | une vague qui démarre tard par rapport à l'alerte n'a pas eu le temps de porter le prix ; ou le détecteur a tiré sur un démarrage tardif | position de la rafale (0 à 1) | idem | 24 % des lancements ont une rafale tardive | 0,50 (filtre négatif) | − 62 % par trade sur les tardives | mesuré sur blocs ≤ − 1 s ; à vérifier à − 2 s | taille de l'essaim (les tardives sont petites) | filtre négatif pré-enregistré |
| 3 | Absence totale de signature d'essaim | ni gros slot, ni tailles répétées, ni financeur partagé : 10 % de ×2 (n 41) | lancement que les bots ont ignoré : pas de demande | les trois indicateurs à 0 | — | 11 % | 0,39 (négatif) | − 62 % | stable (quantités du slot) | aucune évidente ; c'est le bas de l'échelle d'activité | filtre négatif pré-enregistré |
| 4 | Essaim + entrée bon marché | essaim ≥ 40 à − 5 s ET prime dans le tercile le moins cher : 47 % (n 17) ; D1 ET prime basse : 44 %, EV + 11 % (n 16, 5 grappes) | la demande est là et le prix n'a pas encore tout pris | essaim ET prime | — | ≈ 5 % | 1,75 à 1,88 | − 4 % à + 11 % | non vérifié | VU APRÈS COUP (croisement fait comme contrôle de confusion), 5 à 6 grappes, l'étude forensique avait trouvé l'inverse (prime basse = ×2 arithmétique) | seulement comme règle pré-enregistrée à part, comptée dans Holm |
| 5 | Identité de l'opérateur dominant | tout le ×3 de D1 vient d'un opérateur (22 des 40) | cet opérateur a produit les ×3 de la période | grappe (hindsight) | — | 22 % des lancements | ×3 2,8 avec lui, 1,0 sans | — | — | c'est de l'hindsight (union-find sur le snapshot) ; déjà exclu par le plan ; l'opérateur meurt ou change | aucun : non exploitable |

## 10. La règle la plus prometteuse

Réponse à la question posée : **non, aucune règle observable à alerte − 1 s n'atteint, sur
DISCOVERY, la précision de rentabilité (45,8 % sur le ×2, 32,8 % sur le ×3) avec une fréquence et une
assise d'opérateurs suffisantes.** Le mécanisme trouvé est réel mais modeste : la continuation suit
l'amplitude et l'avance de l'essaim de bots, pas une structure de coordination ou de financement ; et
cette quantité est une feature déjà connue (`m_buys_10s`), que l'étude forensique avait vue
répliquer puis s'expliquer par le prix et l'opérateur.

Ce qui mérite tout de même d'être écrit pour une validation, parce que c'est une règle simple, dérivée
d'un mécanisme, à seuil justifié (30 wallets, soit l'essaim médian d'un lancement non D1 dépassé
avant que l'alerte ne tire), à fréquence exploitable (≈ 3 par jour), et dont le ×3 (29 %, seuil de
rentabilité 32,8 %) est à portée de l'incertitude :

En langage naturel : « Si, dix secondes avant l'alerte, au moins trente wallets externes distincts
ont déjà acheté le token (l'essaim de bots est à la fois gros et en avance sur le détecteur), alors
signal ; sinon rien. »

```
IF   n_external_buyer_wallets(bt <= t_alert - 10 s) >= 30      # essaim gros et précoce
AND  burst_position <= 0.5                                       # la rafale est au début de la fenêtre (filtre négatif 2)
THEN SIGNAL (entrée + 5 s, prise de profit x3 vendue au relevé suivant, sortie 1 h)
ELSE rien
```

Attendu honnête : DISCOVERY donne 41 % de ×2 et 29 % de ×3 sur 34 lancements et 11 opérateurs, EV
− 17 % à 500 $ sur le ×2 ; la chaîne de contrôles ne détecte un tel lift (1,6) qu'une fois sur 24.
Si Benjamin décide de la valider, elle doit entrer dans la liste gelée comme candidat pré-déclaré
(avec le mécanisme 4 à part, étiqueté « vu après coup »), être comptée dans Holm, et ne jamais être
retouchée après la lecture.

Familles réellement éliminées par cette autopsie : financement partagé des acheteurs externes (H1,
H2, F), transition de régime avant l'alerte (H6, H7, H8), historique des wallets précoces (acteurs :
taux antérieur = taux de base), second groupe de financeurs (2 cas). Mécanismes qui restent :
l'amplitude et l'avance de l'essaim (1), sa position (2), et l'entrée bon marché conditionnelle à
l'essaim (4), ce dernier à considérer comme une hypothèse née des données.
