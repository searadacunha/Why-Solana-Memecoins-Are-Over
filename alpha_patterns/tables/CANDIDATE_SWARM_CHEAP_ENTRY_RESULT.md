# SWARM + CHEAP ENTRY : résultat de l'unique test (2026-10-07)

Règle gelée avant toute lecture (`CANDIDATE_SWARM_CHEAP_ENTRY.md`, gel
`CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json`, `SELECTION_FREEZE.json`, PLAN §11) :

```
IF  swarm_10s >= 30                               # wallets externes distincts entrés avant T - 10 s
AND p_entry_over_operator <= 3.6016666094462075   # prime d'entrée dans le tercile le moins cher (DISCOVERY, rob_80 du 05/10)
THEN SIGNAL (entrée + 5 s, TP x2 au relevé suivant, sortie 1 h, coûts trade.py)
```

Déclenchements par bloc (toutes alertes, features seules) : DISCOVERY 25, SELECTION 26,
VALIDATION 14, OOS 20. Ni DISCOVERY ni SELECTION n'ont été lus pour cette règle avant le gel.

## VALIDATION, une lecture (`val_60_validation.py`, 2026-10-07)

| mesure | valeur |
|---|---|
| lignes éligibles du bloc | 232 (6 jours actifs) |
| déclenchements (n) | 13 (14 sur toutes les alertes du bloc) ; 5 grappes ; 3 jours |
| ×2 : succès / précision / taux de base / lift | 5 / 38,5 % / 30,6 % / 1,26 |
| IC 95 % de Wilson sur la précision ×2 | [17,7 %, 64,5 %] |
| écart règle moins reste, IC 95 % bootstrap de grappes | + 8,3 pts [− 24,5, + 40,2] |
| p (Fisher / bootstrap de grappes / CMH par jour / retenu = max) | 0,362 / 0,223 / 0,394 / **0,394** |
| ×3 : succès / précision / base / lift (descriptif) | 2 / 15,4 % / 13,4 % / 1,15, IC [4,3 %, 42,2 %] |
| ×5 : succès / précision / base (descriptif) | 0 / 0 % / 6,5 % |
| EV nette ×2 à 100 $ / 500 $ / 1 000 $ | − 0,2 % / − 11,6 % / − 23,0 % ; IC 95 % à 500 $ [− 52,8 %, + 8,2 %] ; borne 99 % − 60,7 % |
| EV nette ×3 à 500 $ | − 46,0 % |
| variantes du trade ×2 à 500 $ : toucher / stop − 50 % / sortie 60 s / sortie 300 s / K ×0,5 / K ×2 | − 10,1 % / − 5,6 % / − 14,6 % / + 3,1 % / − 16,7 % / − 7,5 % |
| entrée à + 15 s : précision ×2 | 23,1 % |
| fréquence | 2,3 signaux par jour actif (4,8 % des alertes) |
| stabilité temporelle | 15/09 : 2 sur 5 (base du jour 43,9 %) ; 17/09 : 2 sur 5 (31,6 %) ; 18/09 : 1 sur 3 (26,3 %) ; 0 déclenchement les 16, 20 et 21/09 |

Décision selon le protocole (≥ 8 déclenchements, ≥ 5 grappes, ≥ 3 jours, précision > base,
p ≤ 0,10) : la règle satisfait les minima mais p = 0,39. **ÉCHEC en VALIDATION.** OOS n'est pas lu
(`OOS_READ.json` absent, bloc toujours vierge).

## Classement

**C — ÉCHEC.** Sur 13 lancements, 5 succès contre 4 attendus au taux de base ; EV négative à
500 $ ; la précision tombe à 23 % avec une entrée à + 15 s ; le signal ne se répète pas d'un jour à
l'autre au-delà du bruit. Aucun seuil, aucune variante, aucune autre combinaison ne sera essayée.

Conclusion pour la piste : la famille « nombre précoce de wallets externes / essaim de bots » n'a
pas démontré d'alpha exploitable sur ce snapshot. Elle rejoint les familles éliminées par l'autopsie
du 06/10 (financement partagé, transition de régime, historique des acteurs). Pour l'étude
alpha_patterns dans son ensemble : **NO EXPLOITABLE PATTERN FOUND**, avec la puissance mesurée
(un effet ≥ × 3 le taux de base aurait été vu 2 fois sur 3 ; × 2,2 une fois sur 8 ; en dessous,
rien). La sélection mécanique (10 règles par cible + composites) n'a jamais été gelée ni testée ;
VALIDATION étant lue, elle ne peut plus l'être proprement sur ce snapshot.
