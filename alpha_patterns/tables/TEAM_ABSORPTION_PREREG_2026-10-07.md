# Pré-enregistrement : absorption de l'inventaire de l'équipe par la demande externe (2026-10-07)

Écrit AVANT tout calcul d'issue de cette analyse. Exploratoire, séparé de l'étude confirmatoire. Suite de
`tables/BUNDLE_TEAM_RHYTHM_2026-10-07.md` (réponse C). Hypothèse : le GOOD / BAD dépend de la capacité du
marché à absorber l'inventaire que l'équipe revend, pas de la qualité du bundle.

## Ce qui a été regardé avant d'écrire ce fichier (structure seulement, aucune issue)

- Fenêtres brutes : chacune couvre la création jusqu'à alerte + 30 s, toutes les transactions réussies du
  mint ; les 195 669 signatures sans détail sont toutes des transactions échouées (le collecteur ne les
  détaille pas, par construction) ; toutes les fenêtres atteignent le slot de création.
- Premier passage de `code/feat_48_absorption.py` : des transferts de 1 token vers des centaines
  d'adresses (poussière) gonflaient l'équipe ; seuil fixé à 1e6 tokens (0,1 % de l'offre), les vrais
  transferts de sortie portant de l'ordre de 10 % de l'offre. Valeur de l'inventaire au prix p0 de
  l'alerte (référence des séries de prix), plutôt qu'au dernier échange (ordre ambigu dans un slot).
- Distributions sans issue : à + 30 s l'équipe n'a vendu qu'une médiane de 4,2 % de son inventaire
  (90e centile 16 %) ; premier transfert vers un wallet de sortie 7 s après la création (médiane, 654
  lancements sur 1 015), première vente de l'équipe 8,7 s après l'alerte (848 sur 1 015) ; acheteurs
  externes à + 29 s : médiane 81, 31,6 SOL ; inventaire : 78 % de l'offre, médiane 299 SOL au prix
  d'alerte ; 82 lancements ont plus de 10 wallets de sortie.
- Validation de l'inventaire contre la part d'offre mesurée en direct par le détecteur : 11 écarts au
  premier passage, deux causes corrigées avant toute issue : (1) des achats de snipers logés dans la
  transaction de création ou de migration du slot 0 (types create / migrate, plus seulement buy) ;
  (2) dans 11 lancements le créateur est lui-même un sniper du bundle (rôle creator) : tous les snipers
  entrent dans l'inventaire. Après correction, écart maximal 0,012 de l'offre sur les 1 015 lancements.
- Contrôles structurels K1 et K3 faits avant toute issue (`tables/team_absorption_checks.json`).
- Ce qui n'existe pas sans réseau : les ventes après alerte + 30 s. `exit_destination` (ventes complètes
  des wallets de sortie) mélange des événements postérieurs au 15/09 : il n'est pas utilisé ; seules ses
  médianes publiées sont citées comme contexte.

## Données

- Les 1 015 alertes antérieures au 2026-09-15 (DISCOVERY 643, SELECTION 372). Issues par
  `ap_lib.load_labels("selection")` ; VALIDATION et OOS ne sont ni chargés ni lus. Les séries de prix sont
  lues par `pde.load_series()` (fichier entier) et filtrées tout de suite sur les 1 015 mints.
- Équipe (identité) = groupe U de `mech_47_team_rhythm.build()` ; intra-équipe = groupes U à ≥ 5
  lancements éligibles pour le label considéré.
- Équipe (wallets, par lancement et par coupure) = snipers du noyau + créateur + tout wallet ayant reçu
  un transfert de ≥ 1e6 tokens d'un wallet de l'équipe visible à la coupure (fermeture).
- Coupures c (secondes depuis l'alerte ; une transaction est visible si bt ≤ t_alerte + c) : − 1 (avant
  l'alerte), 4, 9, 19, 29, soit les moments de décision T = + 5, + 10, + 20, + 30 s avec 1 s de marge.

## Labels

- Y2 explicatif : le label de l'étude, ×2 confirmé en 1 h depuis l'entrée à + 5 s (premier relevé dans
  [5, 15] s). Sert à DÉCRIRE le mécanisme à toutes les coupures, jamais à revendiquer un signal.
- Y2_T tradable, T ∈ {5, 10, 20, 30} : même définition avec l'entrée au premier relevé dans [T, T + 10] s
  (`pde.entry_point`, `lab_10.path_labels`, couverture inchangée) ; trade déclaré `tp2_next` simulé à la
  même latence (`lab_10.trades`, coûts inchangés, 500 $). Une décision à la coupure T − 1 ne se juge que
  sur Y2_T. Y2_5 = Y2.

## Les 10 métriques (à chaque coupure c)

| # | métrique | définition |
|---|---|---|
| M1 | acheteurs externes | wallets distincts hors équipe ayant acheté après le slot de création |
| M2 | volume externe | SOL payés par ces achats |
| M3 | vitesse de la demande | SOL externes achetés dans (c − 10, c] |
| M4 | accélération | acheteurs externes dans (c − 10, c] moins dans (c − 20, c − 10] |
| M5 | part de l'inventaire vendue | tokens vendus par l'équipe / inventaire |
| M6 | SOL sortis par l'équipe | SOL reçus par les ventes de l'équipe |
| M7 | demande / inventaire | M2 / valeur de l'inventaire au prix d'alerte |
| M8 | absorption | M2 / (M6 + SOL des ventes externes + 1 SOL) |
| M9 | part de bots récurrents | part des acheteurs externes déjà vus acheteurs externes avant l'alerte sur ≥ 5 lancements antérieurs visibles (t_j + 60 ≤ t_i − 1) |
| M10 | mouvement déjà réalisé | multiple du prix au dernier relevé de la série ≤ c (p0 = 1) ; non défini à c = − 1 |

Descriptifs (hors tests) : inventaire (tokens, part de l'offre, valeur, concentration), wallets de
sortie, délais création → transfert → première vente, part vendue à création + 10 / 20 / 30 / 40 s,
concentration et taille médiane des achats externes, chemin du prix après l'entrée (séries).

## Hypothèses (5) et tests

- H1 (A de la consigne) : avant la liquidation massive (toutes les coupures ≤ 29 : l'équipe a vendu
  ~4 %), les GOOD ont plus de demande externe (M1, M2, M3, M7) que les BAD de la même équipe.
- H2 (B) : la différence de demande n'apparaît qu'aux coupures tardives, une fois les ventes commencées.
- H3 (C) : le résultat est déjà inscrit avant que l'équipe vende : séparation à c = − 1 (l'équipe n'a
  rien vendu) aussi forte qu'à c = 29.
- H4 : le rapport d'absorption M8 (ou M7) sépare les GOOD des BAD et donne une règle au-dessus du seuil
  de rentabilité.
- H5 (côté offre) : les GOOD sont ceux où l'équipe vend moins vite (M5 plus bas).

Tests : AUC intra-équipe (paires GOOD, BAD de la même équipe ; nul = permutation des issues dans
l'équipe, B = 5 000, bilatéral). Famille « explicative » : M1 à M10 × 5 coupures contre Y2 (49 tests) ;
famille « tradable » : M1 à M10 × coupures 4, 9, 19, 29 contre Y2_T (40 tests) ; BH à l'intérieur de
chaque famille. « Passe » = q ≤ 0,10 ET même sens sur DISCOVERY et SELECTION pris séparément (AUC
intra-équipe recalculée dans chaque bloc). AUC poolée à côté. Sensibilités (hors classement) : sans le
plus grand groupe U ; sans les 82 lancements à plus de 10 wallets de sortie ; latence : métriques à
c − 2 pour la meilleure métrique tradable.

Règles (seuils fixés ici ; évaluées contre Y2_T, à chaque T, précision, nombre, DISC / SEL, net moyen à
500 $) :
- R1 absorption M8 ≥ 1 (les acheteurs externes ont payé au moins autant que tout ce qui a été vendu) ;
- R2 demande / inventaire M7 ≥ 0,25 (un quart de la valeur de l'inventaire déjà payé par l'extérieur) ;
- R3 vitesse M3 ≥ 80e centile de sa distribution DISCOVERY à cette coupure (sans issue) ;
- R4 M5 ≥ 0,05 ET M10 ≥ 1 (l'équipe a commencé à vendre et le prix tient au moins au niveau d'alerte) ;
- R5 M5 = 0 ET M1 ≥ médiane DISCOVERY de la coupure (demande forte, l'équipe n'a encore rien vendu).

GOOD contre BAD par équipe : équipes à ≥ 3 GOOD et ≥ 3 BAD (Y2) ; médianes à c = 29 de l'inventaire,
M5, M1, M2, M7, M8 ; nombre d'équipes où la médiane GOOD dépasse la médiane BAD (test du signe).

## Contrôles

K1 horodatages : chaque enregistrement a un bt dans [création, alerte + 30 s] ; inversions slot / bt.
K2 part des ventes de l'équipe (SOL, à + 29 s) faites après l'entrée à + 5 s.
K3 externalité des acheteurs : part du volume externe venant (a) de wallets qui rejoignent l'équipe après
la coupure, (b) de financeurs des snipers, (c) de snipers d'autres lancements de la même équipe U,
(d) de snipers d'autres équipes.
K4 fuite : le code refuse toute métrique avec bt > t_alerte + c et toute entrée tradable avant T.
K5 DISCOVERY et SELECTION séparés ; un effet présent sur l'un et absent ou inversé sur l'autre n'est pas
robuste.

## Classement fixé d'avance

- A mécanisme clair et exploitable : une règle à une coupure T fait ≥ 45,8 % de Y2_T sur DISCOVERY ET sur
  SELECTION, avec ≥ 15 déclenchements dans chaque bloc et un net moyen positif dans les deux, et une
  métrique tradable passe.
- B mécanisme réel mais pas assez prédictif : une métrique de demande ou d'absorption passe dans la
  famille tradable, sans règle qui atteigne A.
- C explique après coup mais pas avant : une métrique de demande ou d'absorption passe dans la famille
  explicative (aux coupures tardives ou par le chemin de prix), aucune dans la famille tradable.
- D hypothèse rejetée : aucune métrique de demande ou d'absorption (M1 à M4, M7, M8) ne passe, même en
  explicatif.
- E autre mécanisme : seule une métrique hors demande passe (M5, M9, M10).
Au plus 10 métriques, 5 hypothèses, 5 règles ; pas d'autre recherche après le rapport.

## Amendement 1 (2026-10-07, avant tout calcul d'issue réelle ; résultats vus : non)

Après la revue à l'aveugle du code (`audit/TEAM_ABSORPTION_PREAUDIT_2026-10-07.md` : leakage-auditor et
silent-failure-hunter, aucun BLOQUANT, 3 MAJEUR, 10 MINEUR).

1. Retard du détecteur. Le prix d'alerte p0 égale exactement l'état du pool après les transactions de
   bt ≤ t_alerte − 2 pour 58,5 % des lancements (31 % seulement à bt ≤ t_alerte) : le détecteur, et donc
   le relevé d'entrée, voit la chaîne avec 1 à 2 s de retard. La coupure tradable PRINCIPALE devient
   c = T − 3 (2, 7, 17, 27) ; T − 1 (4, 9, 19, 29) passe en sensibilité. Les règles R1 à R5 sont
   évaluées à c = T − 3.
2. Famille explicative. Aux coupures 9, 19 et 29, le chemin du prix après l'entrée fait partie du label
   (M10 lit des relevés postérieurs à l'entrée ; M2, M7, M8 fixent les réserves donc le prix). La famille
   BH explicative ne garde que les coupures d'avant l'entrée, − 1 et 2 (M10 non défini à − 1). Les
   coupures 9, 19, 29 sont publiées en descriptif (AUC, sans q), M10 exclu. Test ajouté, « la demande
   explique-t-elle au-delà du prix ? » : M2, M7, M8 à c = 29, AUC intra-équipe avec strates équipe ×
   tercile de M10 à c = 29 (BH sur 3).
3. Classement précisé : C = aucune métrique tradable ne passe ET un des 3 tests « à prix égal » passe ;
   D = aucune métrique de demande (M1 à M4, M7, M8) ne passe dans les familles tradable ou explicative
   d'avant l'entrée, ni dans les tests à prix égal ; E = seules M5, M6, M9 ou M10 passent. Un passage
   explicatif à c ≤ 2 compte comme « avant », pas pour C.
4. Achats « buy-and-burn » (enregistrements buyburn : SOL entré dans le pool, tokens brûlés ; un seul
   signataire, présent dans 978 lancements) : exclus de la demande externe organique (M1 à M4, M7, M8),
   enregistrés à part (buyburn_sol) ; sensibilité M8 et R1, R2 avec ce SOL ajouté à M2.
5. Inventaire de M5 = tokens du slot 0 de toute l'équipe (snipers + créateur, types buy, create,
   migrate) ; la validation contre le détecteur reste sur les snipers seuls. Les ventes du slot 0 sont
   comptées (seuls les ACHATS externes sont pris après le slot 0).
6. Classement des enregistrements par les soldes plutôt que par le nom d'instruction : après le slot 0,
   tout enregistrement avec une venue et des legs est un achat (v_tok < 0) ou une vente ; tout
   enregistrement sans venue où un wallet de l'équipe perd ≥ 1e6 tokens et un autre en reçoit ≥ 1e6 est
   un transfert (cas d'un transfert typé « create » par le parseur).
7. Sensibilité « nombreux wallets de sortie » : le nombre de wallets de sortie est mesuré à la coupure
   de décision, pas à + 29 s.
8. Descriptifs sans p ; tableau par équipe à c = 29 (pré-enregistré) plus médianes à c = 2 sans test.
   K2 compté avec l'équipe finale ; K3 en SOL à chaque coupure ; K4 : assertion explicite bt ≤ coupure
   sur chaque enregistrement utilisé.
