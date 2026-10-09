# Candidat pré-déclaré unique : SWARM + CHEAP ENTRY

Écrit le 2026-10-07 avant toute lecture de SELECTION, VALIDATION ou OOS. Dernière expérience sur la
piste « essaim de bots ». Une fois ce fichier haché dans `CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json`,
rien ci-dessous ne change : ni le seuil A, ni la définition de B, ni la fenêtre, ni la cible, ni le
trade, ni les coûts.

## Origine (honnête)

Sur DISCOVERY (363 lancements), l'autopsie de D1 (`BREAK_THE_LOOP_2026-10-06.md`) a montré que la
continuation suit la taille et l'avance de l'essaim de bots externes. La règle « ≥ 30 wallets
externes entrés avant T − 10 s » seule donne 41 % de ×2 (n 34), EV négative. Le croisement avec une
entrée bon marché a été regardé APRÈS COUP, comme contrôle de confusion, avec d'autres définitions de
l'essaim (≥ 40 wallets à T − 5 s : 47 %, n 17 ; D1 : 44 %, n 16). Le croisement exact ci-dessous
(A à T − 10 s, seuil 30, ET tercile de prime le moins cher) n'a PAS été lu sur DISCOVERY avant le gel.
C'est une hypothèse née des données, testée une seule fois hors échantillon.

## Règle

```
A = nombre de wallets externes DISTINCTS ayant acheté le token avec un temps de bloc <= t_alerte - 10 s
    externe = ni sniper du bundle (role core de cd_table), ni créateur ; achats du slot de création exclus ;
    « achat » tel que parsé par post_detection_forensics/fparse.py sur la fenêtre brute (col. swarm_10s de
    derived/feat_swarm.jsonl.gz, code/feat_29_swarm.py)
B = p_entry_over_operator <= 3.6016666094462075
    = prime d'entrée (P0 / prix moyen payé par l'opérateur, feature fA de l'étude forensique, coupure
    alerte - 1 s) dans le tercile le moins cher des 363 lignes DISCOVERY de référence (tables/atoms.json,
    ref_rows), telle que définie le 2026-10-05 dans code/rob_80_robustness.py (« lift par tercile de
    prime d'entrée »), AVANT l'hypothèse ; prime manquante = condition fausse

IF   A >= 30
AND  B
THEN SIGNAL
```

Pourquoi B : c'est la seule définition de « entrée bon marché » déjà présente dans ce pipeline avant
l'hypothèse (robustesse du 05/10). D'autres définitions existent dans des études antérieures (PDE :
capitalisation < 60 k$, H2 du 29/09) ; elles ne sont pas dans ce pipeline et n'ont pas été regardées
pour choisir. Le seuil 30 de A est celui de la consigne (l'essaim médian d'un lancement ordinaire,
dépassé avant que le détecteur ne tire), pas un optimum. La prime et A sont connus à alerte − 1 s ;
A ne dépend même pas de la dernière seconde (il s'arrête à − 10 s).

## Cible, trade, décision (protocole existant, PLAN §4 et §7)

- Cible primaire : Y2 = deux relevés consécutifs ≥ 2 × le prix d'entrée dans l'heure, entrée au
  premier relevé dans [5 s, 15 s] après l'alerte (`ap_lib`). Y3 et Y5 rapportés à titre descriptif
  (×5 : sans puissance).
- Trade : achat à + 5 s, prise de profit ×2 vendue au relevé suivant, sortie au temps à 1 h, modèle de
  coûts de `trade.py` inchangé, 500 $ (100 $ et 1 000 $ rapportés). Seuil de rentabilité DISCOVERY :
  45,8 % de ×2.
- VALIDATION, une lecture (`val_60_validation.py`) : passe si ≥ 8 déclenchements dans ≥ 5 grappes sur
  ≥ 3 jours, précision > taux de base du bloc, p ≤ 0,10 avec p = max(Fisher exact, bootstrap de
  grappes avec tirages sans déclenchement comptés contre, CMH stratifié par jour). Si elle échoue :
  STOP, classe C.
- OOS, une lecture (`oos_70_oos.py`), seulement si VALIDATION passe : Holm sur un seul candidat
  (= p ≤ 0,05 unilatéral), mêmes minima. Même règle, même seuil, même entrée, mêmes coûts.
- Classement final : A EXPLOITABLE = passe VALIDATION et OOS, et net moyen OOS à 500 $ > 0 ET à 100 $
  > 0 (point) avec borne basse rapportée ; B PROMETTEUR MAIS INSUFFISANT = passe VALIDATION mais pas
  l'OOS corrigé, ou passe l'OOS sans EV positive ; C ÉCHEC = échoue VALIDATION, ou précision OOS sous
  le taux de base.

## Ce qui est consommé

La liste gelée de SELECTION ne contient que ce candidat : la sélection mécanique (10 règles par
cible + composites) n'est pas gelée et ne sera pas testée après cette lecture (VALIDATION et OOS
seront lus). Comptes de déclenchement par bloc, features seules, sans issue : DISCOVERY 10 lignes
éligibles, SELECTION 17, VALIDATION 13, OOS 17 (sur 363 / 249 / 232 / 295). Avec 13 déclenchements en
VALIDATION, la règle ne peut passer que si sa précision y est bien au-dessus du taux de base ; c'est
accepté d'avance.
