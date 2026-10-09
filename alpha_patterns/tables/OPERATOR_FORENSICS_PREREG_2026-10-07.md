# Pré-enregistrement : forensique des opérateurs de bundle (2026-10-07)

Écrit AVANT tout calcul d'issue de cette analyse. Exploratoire, séparé de l'étude confirmatoire.

## Données

- Population : les 1 015 alertes antérieures au 2026-09-15 00:00 UTC (DISCOVERY 643, SELECTION 372).
  Issues seulement sur les lignes éligibles (régime fin, entrée + 5 s, fenêtre 1 h observée) :
  DISCOVERY 363, SELECTION 249. VALIDATION et OOS ne sont ni chargés ni lus (`ap_lib.load_labels`
  avec l'étape `selection`), les features de leurs alertes non plus.
- SELECTION est lu ici pour la première fois par alpha_patterns (la sélection mécanique a été
  abandonnée, PLAN §11). Il n'est pas vierge pour cette question : signal_search l'a lu le 02/10
  (VAL1) pour des historiques à 15 min.
- Identités, toutes connues avant l'alerte : `cd_table` (snipers `role core`, financeurs dernier et
  de genèse avec temps de bloc < t − 1 s, règle « hub » stricte de `feat_20_history.py`), journal
  du détecteur (tickets, créateur).

## Niveaux d'identité (liens entre lancements, puis composantes connexes)

| niveau | lien entre deux lancements | défendabilité attendue |
|---|---|---|
| L1 wallet | ≥ 1 wallet sniper commun | forte : même clé privée |
| L2 wallet + financeur | ≥ 1 paire (wallet sniper, dernier financeur) commune | forte, plus stricte que L1 |
| L3 financeur | même financeur dominant non hub (≥ 2 snipers du lancement) | moyenne : trésorerie commune ou service |
| L4 co-occurrence | ≥ 2 wallets snipers communs | forte : un groupe qui agit ensemble |
| L5 signature | même configuration exacte de tickets (triés, arrondis à 0,01 SOL) | moyenne : script commun, possiblement partagé |
| U union | L1 ∪ L3 ∪ L5 ∪ même créateur | identité « opérateur » la plus complète, risque de chaînage |
| L3b, L5b (diagnostic) | même source au 2e saut ; signature grossière (nb de snipers, ticket médian à 1 SOL, groupé / unique) | faible, montrées pour mesurer le chaînage |

Défendabilité mesurée : pour chaque type de lien, part des paires liées qui partagent AUSSI un autre
type de lien, contre la même part parmi les paires de lancements de la même semaine.

## Tests (tous pré-spécifiés, issues ×2 primaire, ×3 secondaire, ×5 descriptif)

1. Hétérogénéité entre groupes : χ² de Pearson groupes × issue sur les groupes à ≥ m lancements
   éligibles, m ∈ {5, 10, 20, 30, 50}, pour L1, L3, L4, L5, U. Nuls : permutation des issues entre
   lancements (globale), à l'intérieur du jour calendaire, à l'intérieur de (jour × tercile de prime
   d'entrée ; terciles de `rob_80`, DISCOVERY). B = 10 000. Écart-type entre groupes des vrais taux
   par la méthode des moments.
2. « Un pump sur trois » : par groupe, P(×2), P(×3), P(×5) et IC de Wilson ; nombre de groupes dont
   l'IC exclut le taux de base, comparé au nombre attendu sous permutation.
3. Séquences (groupes U et L5 à ≥ 10 lancements éligibles, ordre chronologique) : P(S | S précédent)
   − P(S | F précédent), P(S | deux F précédents) ; nul = permutation à l'intérieur du groupe.
   Comparaison avec la même dépendance sur le marché entier (lancement précédent, tous groupes).
4. Régimes (groupes à ≥ 20 lancements éligibles) : χ² semaines × issue à l'intérieur du groupe, nul =
   permutation dans le groupe ; même statistique pour le marché entier.
5. Historique → prochain lancement, chronologique : identité causale U (primaire), L1 et L5
   (secondaires) par union-find incrémental (un lancement devient visible 60 s après son alerte) ;
   issues antérieures utilisées seulement si résolues (t_j + 3 810 s ≤ t_i − 1). Prédicteurs fixés :
   n_prev, taux antérieur, taux sur les 5 et 10 derniers, succès parmi les 10 derniers, jours depuis
   le dernier succès, lancements du groupe sur 24 h. Base « marché » p_m = taux résolu des 24 h
   précédentes si ≥ 10 lancements, sinon taux résolu cumulé. Prédiction de groupe
   p_g = (succès + 10 p_m) / (n_prev + 10). Mesures : log-loss et Brier de p_g contre p_m (IC
   bootstrap par groupe), AUC des prédicteurs (n_prev ≥ 5), par bloc.
6. Règles HIGH-CONFIDENCE (fixées ici) : HC1 = n_prev ≥ 10 ET borne basse de Wilson à 90 %
   unilatéral du taux antérieur > p_m ; HC2 = n_prev ≥ 10 ET taux antérieur ≥ seuil de rentabilité
   (45,8 % pour ×2, 32,8 % pour ×3). P(succès | HC) contre P(succès | historique non HC),
   chronologiquement, par bloc, avec Fisher et bootstrap par groupe, EV du trade déclaré.
7. Portefeuille (groupes U à ≥ 10 lancements éligibles) : distribution des multiples MFE 1 h,
   moyenne, médiane, meilleur ; trade suiveur déclaré (×2 au relevé suivant, 500 $) : moyenne,
   cumul, plus forte baisse du cumul, plus longues séries de pertes et de gains. Descriptif.
8. Effet opérateur contre effet lancement : nuls stratifiés du test 1 et modèle logistique mixte
   (statsmodels, variationnel) avec effets aléatoires groupe U et jour, tercile de prime fixe.
9. Présence avant le mouvement : par groupe, âge à l'alerte, essaim externe à − 10 s et − 5 s ;
   corrélation entre groupes du taux ×2 et de l'essaim médian. Descriptif.

## Réponse attendue

A équipes distinctes avec edge historique / B équipes sans différence de performance / C mêmes
équipes, bons et mauvais lancements, stratégie probabiliste / D impossible de distinguer / E pas
d'entités persistantes. Aucune règle de trading n'est tirée de cette analyse ; au plus UNE
hypothèse « quand le groupe X intervient » si les tests 1, 5 et 6 vont dans le même sens.
