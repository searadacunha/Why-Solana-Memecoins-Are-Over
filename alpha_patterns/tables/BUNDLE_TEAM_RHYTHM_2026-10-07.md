# Rythme des équipes de bundle : pourquoi la même équipe fait GOOD puis BAD (2026-10-07)

Exploratoire. Tests fixés avant tout calcul d'issue dans `tables/TEAM_RHYTHM_PREREG_2026-10-07.md`
(amendement 1, écrit avant les issues réelles, après une revue à l'aveugle du code :
`audit/TEAM_RHYTHM_PREAUDIT_2026-10-07.md`). Données : les 1 015 alertes antérieures au 2026-09-15
(DISCOVERY et SELECTION, déjà lus par la forensique des opérateurs). Aucune issue de VALIDATION ni
d'OOS n'est chargée ; `X.npz` est chargé en entier (features seulement) mais seules les 1 015 lignes
antérieures au 15/09 entrent dans un calcul. L'étude confirmatoire n'est pas ouverte, OOS reste vierge.
Aucune donnée nouvelle, aucun réseau pour l'analyse (seule la structure du dépôt Ponytail a été lue par
l'API GitHub, section 0). Chiffres : `tables/team_rhythm.json` ; contrôles :
`controles/team_rhythm_controls.json` ; code : `code/mech_47_team_rhythm.py` ; registre : 381
comparaisons sur données réelles dans ce calcul (ligne `team_rhythm`), 49 350 sur données synthétiques.
Le registre d'alpha_patterns compte au total 31 655 945 comparaisons sur données réelles : 13 955 085
(44 %) sur DISCOVERY, 17 699 874 (56 %) dépensées par des études antérieures sur les mêmes 1 657 alertes,
SELECTION comprise (ligne prior_burden) (Bonferroni 0,05 / 31 655 945 = 1,6e-9) ; les q de ce rapport sont des BH à l'intérieur
des familles pré-enregistrées, et aucun p ici n'approche le seuil du registre.

GOOD = ×2 confirmé (deux relevés) dans l'heure qui suit une entrée à alerte + 5 s ; BAD = éligible et
pas ×2. Taux de base 27,5 % (168 / 612). Équipe = groupe U de la forensique (wallets, financeur
dominant, configuration exacte, créateur). Analyse intra-équipe : 456 lancements éligibles dans 33
équipes à ≥ 5 lancements éligibles (DISCOVERY 286, SELECTION 170), 125 GOOD ; 28 équipes ont à la
fois des GOOD et des BAD. Session = suite de lancements d'une équipe sans pause de plus de 90 min.

## 0. Outils : audit court

| outil | état réel dans CETTE session | usage ici |
|---|---|---|
| Claude Code | la session de bureau tourne en 2.1.286 (processus) ; la CLI `claude` du PATH est en 2.1.263 ; modèle Opus 5.5 | |
| claude-mem 13.28 | chargé mais n'enregistre rien : quota de l'observateur épuisé depuis le 2026-10-02 | aucun |
| Graphify 0.9.73 (`~/.local/bin/graphify`, skill `~/.claude/skills/graphify`, hook `graphify_nudge.py`) | installé et fonctionnel ; `alpha_patterns` n'a pas de `graphify-out` | non utilisé, voir section 6 |
| OmniRoute 3.8.51 (`/opt/homebrew/bin/omniroute`) | installé, NON actif : `ANTHROPIC_BASE_URL=https://api.anthropic.com`, aucun processus, port 20128 fermé ; il ne sert que si la session est lancée par `claude-omni` dans un terminal | aucun ; rien n'a été modifié |
| Ponytail (`DietrichGebert/ponytail`, v4.13.0, MIT) | NON installé : absent de `installed_plugins.json`, des marketplaces connues, de `enabledPlugins`, de `~/.claude/skills` et des hooks | principe appliqué à la main (un seul script qui réutilise `mech_45`, aucune dépendance nouvelle) ; rien installé |
| Agent Skills (`~/.agents/skills`) | absent : le dossier `~/.agents` n'existe pas | aucun |
| Ce que Claude Code charge vraiment | skills `~/.claude/skills` (agent-reach, etude-gelee, graphify) ; plugins activés playwright-skill, claude-code-setup, claude-mem (task-observer désactivé) ; agents `~/.claude/agents` (5 auditeurs) ; hooks rtk, protocol_guard, graphify_nudge ; plugins fournis par l'application (brightdata, nimble, tavily, data, etc.) ; projet : `~/Downloads/.claude/settings.local.json` (permissions seulement) ; `alpha_patterns` n'a ni `.claude` ni `CLAUDE.md` | skill etude-gelee, auditeurs |

Structure de Ponytail (lue par l'API GitHub, rien cloné) : `.claude-plugin/plugin.json` qui déclare
`hooks/claude-codex-hooks.json` (activation au démarrage, suivi du mode, sous-agents, ligne d'état),
commandes `ponytail`, `-audit`, `-debt`, `-gain`, `-help`, `-review`, une copie des règles par agent
(Cursor, Windsurf, Kiro, Cline, AGENTS.md…) et des benchmarks. Sa règle (« la solution la plus courte
qui marche ») va dans le sens de cette étude ; l'installer n'apporterait rien à la question posée.

## 1. Réponses courtes

| question | réponse |
|---|---|
| A. Les équipes ont-elles un rythme identifiable ? | **Oui, très net, mais aucun lien détecté avec le résultat.** Une équipe lance toutes les 20 min environ (médiane 20,6 min dans une session, la moitié entre 15 et 30 min) et presque jamais à moins de 10 min (39 intervalles sur 827, 4,7 %, contre 47 % entre deux alertes consécutives du marché). Au moins cinq équipes à wallets fixes de ≥ 10 lancements travaillent en une seule session de 4 à 5 heures puis disparaissent ; les autres reviennent sur 3 à 9 sessions. Ce pas est proche du cycle de refinancement décrit par economic_mechanics (21 min ; interprétation, non testée ici). Aucun des 17 tests rythme / séquence ne passe (meilleur q 0,26). |
| B. Les GOOD et BAD d'une même équipe diffèrent-ils structurellement ? | **Aucune différence détectée.** Sur 32 variables (configuration, wallets, financeurs, tickets, ordre dans le slot, rythme, essaim, autres équipes, marché), aucune ne sépare les GOOD des BAD de la même équipe après correction (meilleur q 0,13). La plus forte, l'essaim à − 5 s, vient de la population diffuse et de DISCOVERY seulement : elle s'inverse sur SELECTION et disparaît chez les vraies équipes. |
| C. Une configuration annonce-t-elle un GOOD avant le mouvement ? | **Non détecté.** Ni la configuration de l'équipe (en écart à ses propres habitudes), ni son rythme, ni la réaction du marché avant l'alerte n'améliorent la prédiction du prochain GOOD dans les deux sens (DISCOVERY → SELECTION et SELECTION → DISCOVERY). Changer de configuration, de wallets, de financeur, de nombre de snipers ou de mise n'est associé à aucun écart détecté (puissance non mesurée pour ces tests). |
| D. Les équipes interagissent-elles de façon systématique ? | **Rien de systématique détecté.** Aucun lien détecté entre les issues des autres équipes à ± 60 min et celle d'un lancement (corrélation 0,001, p 0,20 ; puissance non mesurée). Des snipers d'une autre équipe achètent avant l'alerte sur 113 lancements sur 1 015 (11 %) ; 5 paires d'équipes reviennent au moins 5 fois, toutes avec la population diffuse. Aucun des 10 bots récurrents les plus fréquents n'est associé à un écart qui passe la correction (puissance non mesurée). |
| E. D'où vient le phénomène ? | Ce qui varie tient à l'équipe pour le niveau moyen (écart-type 0,63 en logit) et au jour (0,43), moins à la session (0,25), estimations descriptives sans intervalle. À l'intérieur d'une équipe, aucune des variables mesurées avant l'alerte ne sépare de façon détectable le GOOD du BAD. |

**Classement : C. Mêmes équipes, GOOD / BAD essentiellement imprévisibles à l'intérieur de l'équipe**
avec ce que nous mesurons. Interprétation compatible, non testée ici (section 7) : la cadence de
l'équipe suivrait celle de son capital, et la liquidation de l'équipe tomberait en médiane après notre
entrée, dans la fenêtre du ×2 ; aucune différence de configuration n'est détectée entre ses GOOD et ses BAD.

Puissance (contrôles synthétiques sur les vraies équipes, sessions et variables, mesurée pour la
section 4 et pour S1 seulement) : un effet intra-équipe d'AUC 0,68 planté sur une variable est retrouvé
dans 47 mondes sur 50 ; une dépendance « + 15 points après un BAD » dans 31 sur 50, « + 20 points » dans
46 sur 50, « + 10 points » dans 5 sur 50. Sous le nul, 11 mondes sur 200 font passer une variable de la
section 4 et 15 sur 200 un test des sections 2 et 3. Les résultats négatifs rendent donc improbables un
effet intra-équipe d'AUC proche de 0,68 et une dépendance de séquence de + 20 points ; ils n'excluent
ni les AUC entre 0,5 et 0,68, ni les dépendances jusqu'à 15 points (manquées 19 fois sur 50 à + 15).
Aucune puissance n'a été mesurée pour les sections 5 et 6, ni pour I1 et I4 : là, « rien ne passe » ne
veut pas dire « rien ».

## 2. Rythme des équipes

Intervalles entre lancements consécutifs d'une même équipe (827 intervalles) : 10e, 25e, 50e, 75e et
90e centiles = 12,6 / 16,9 / 24,9 / 77,9 / 1 286 min. Dans une session (634 intervalles) : 5e, 25e, 50e,
75e, 95e centiles = 8,7 / 15,1 / 20,6 / 29,5 / 68,3 min. Coefficient de variation médian des
intervalles d'une équipe dans ses sessions : 0,37 (52 équipes ; un processus sans mémoire ferait 1).
381 sessions ; 697 lancements sur 1 015 sont dans une session d'au moins 3.

| équipe (mode) | lancements | période | sessions (tailles) | pas médian dans la session | CV | heures UTC dominantes | chronologie par session (F, 2, 3 ; . = non observé) |
|---|---|---|---|---|---|---|---|
| g850 (wallets fixes) | 14 | 09-10 10:16 → 15:26 | 1 (14) | 23,5 min | 0,19 | 12-14 h | 2F2F2F22F3F... |
| g855 (wallets fixes) | 14 | 09-10 10:54 → 15:03 | 1 (14) | 21,4 min | 0,29 | 11-14 h | 2FFF22F3F2FF.. |
| g606 (wallets fixes) | 14 | 09-06 19:12 → 23:40 | 1 (14) | 20,3 min | 0,32 | 20-22 h | FF22FFFFFF3FF3 |
| g811 (wallets fixes) | 17 | 09-09 22:09 → 09-10 03:15 | 1 (17) | 17,7 min | 0,36 | 22-00 h | F2FFFF2F3F2223... |
| g493 (wallets fixes) | 13 | 09-03 20:31 → 09-04 00:57 | 1 (13) | 19,4 min | 0,45 | | FFFFFFFFFFFFF |
| g570 (wallets fixes) | 23 | 09-05 → 09-07 | 4 (13, 5, 4, 1) | 17,8 min | 0,57 | 16-20 h | FFFFF / F2FF3F2222FF3 / . / FF.. |
| g5 (wallets fixes) | 46 | 08-21 → 09-04 | 9 (11, 10, 7, 6…) | 20,6 min | 0,52 | 23 h, 16 h | 2 GOOD sur 17 |
| g789 (script) | 20 | 09-09 → 09-10 | 2 (13, 7) | 19,7 min | 0,44 | 8-9 h, 19 h | FFFFFFF / FF...2FFFF3FF |
| g169 (script, wallets neufs) | 38 | 08-25 → 09-09 | 26 (au plus 4) | 27,0 min | 0,59 | dispersées | lancements isolés, 10 GOOD sur 25 |
| g578 (script, wallets neufs) | 20 | 09-05 → 09-14 | 15 (au plus 3) | 77,3 min | 0,21 | 13-16 h | lancements isolés, 2 GOOD sur 15 |
| g31 (population diffuse) | 224 | 08-22 → 09-14 | 28 (20, 20, 20, 17…) | 17,9 min | 0,79 | 1-3 h | 38 GOOD sur 115 |

Deux rythmes coexistent. Parmi les équipes à wallets fixes de ≥ 10 lancements, cinq du tableau (g811, g606,
g850, g855, g493) travaillent comme une équipe de quart : une seule session de 4 à 5 heures, un
lancement toutes les 18 à 24 minutes (CV 0,19 à 0,45), puis elles disparaissent ; g5, g570, g679, g745
et g12 reviennent sur 3 à 9 sessions étalées sur 2 à 15 jours (CV jusqu'à 0,57). Les scripts à wallets
neufs lancent surtout des tokens isolés (g169, g578), certains aussi par rafales (g789 : 13 et 7). Sur le marché entier, les
lancements couvrent les 24 heures avec un léger creux entre 4 h et 7 h UTC.

Rythme contre résultat (χ² sommé sur les équipes, nul = permutation des issues dans l'équipe ; « excès »
= écart au taux propre de l'équipe ; BH sur les 17 tests des sections 2 et 3 ; « même sens » = χ²
au-dessus de la moyenne du nul sur DISCOVERY et sur SELECTION pris séparément) :

| test | catégories : n, taux GOOD, excès (points) | p | q | même sens DISC / SEL |
|---|---|---|---|---|
| R1 heure UTC (dans l'équipe) | 0-6 h : 86, 30 %, + 1,0 ; 6-12 : 83, 33 %, + 1,8 ; 12-18 : 138, 27 %, − 3,3 ; 18-24 : 106, 33 %, + 2,1 | 0,062 | 0,26 | oui |
| R1 heure UTC (marché entier) | 26 %, 27 %, 30 %, 26 % | 0,87 | 0,98 | non |
| R2 intervalle depuis le lancement précédent | premier de l'équipe : 23, 30 % ; après une pause > 90 min : 81, 26 %, − 3,4 ; 30-90 min : 74, 34 %, + 2,7 ; 15-30 : 170, 31 % ; < 15 : 65, 29 % | 0,043 | 0,26 | oui |
| R3 rang dans la session | 1er : 104, 27 %, − 2,7 ; 2-3 : 109, 28 % ; 4-6 : 97, 26 %, − 3,5 ; ≥ 7 : 103, 40 %, + 8,0 | 0,14 | 0,34 | oui |
| R4 tiers de la session (non causal) | début : 144, 26 %, − 5,5 ; milieu : 122, 34 %, + 2,8 ; fin : 70, 36 %, + 6,5 | 0,38 | 0,59 | oui |
| R5 taille de la session (non causal) | 1 : 41, 39 %, + 8,9 ; 2-3 : 43, 26 % ; 4-9 : 142, 24 % ; ≥ 10 : 187, 34 % | 0,058 | 0,26 | oui |
| R6 lancements de l'équipe sur 60 min | 0 : 124, 27 % ; 1-2 : 218, 31 % ; ≥ 3 : 71, 32 % | 0,18 | 0,35 | oui |
| S10 surdispersion entre sessions d'une équipe (non causal) | | 0,061 | 0,26 | oui |

Après une longue pause, aucun gain détecté (26 %, − 3,4 points). Début, milieu et fin de session : la
fin fait 36 % contre 26 % au début, mais seulement sur DISCOVERY (fin + 12,0 points ; − 5,1 sur
SELECTION), et rien ne tient après correction. La piste la plus régulière est « tard dans la session » :
41 / 103 = 40 % de GOOD à partir du 7e lancement, contre 84 / 310 = 27 % aux rangs 1 à 6 (+ 8,0 points
sur le taux propre de l'équipe) ; χ² au-dessus du nul sur les deux blocs séparément (p 0,15 et 0,32) ;
p 0,043 avec des sessions coupées à 180 min mais 0,24 à 60 min ; AUC intra-équipe du rang 0,68 pour
le ×3 (p 0,007, l'une des 10 p ≤ 0,05 sur 128 tests de sensibilité, pour 6,4 attendus). Elle ne passe
pas la correction (q 0,34) et 40 % reste sous le seuil de rentabilité du trade déclaré (45,8 %).

## 3. Hypothèses de rythme

Paires et triplets de lancements consécutifs d'une même équipe, tous éligibles ; « excès » = différence
moins la moyenne du nul (permutation dans l'équipe), car la composition entre équipes gonfle
mécaniquement « après un GOOD » et le biais de Miller-Sanjurjo tire l'autre sens.

| hypothèse | P(GOOD) si oui / sinon | n (oui / total) | différence brute, moyenne du nul, excès | p | q | même sens |
|---|---|---|---|---|---|---|
| S1 après un GOOD | 30,8 % / 25,7 % | 104 / 396 | + 5,1 ; + 6,6 ; − 1,5 | 0,74 | 0,90 | non |
| S2 après un GOOD, même session | 30,1 % / 27,2 % | 83 / 333 | + 2,9 ; + 6,3 ; − 3,4 | 0,52 | 0,68 | non |
| S3 après deux BAD | 21,6 % / 35,5 % | 185 / 340 | − 13,9 ; − 8,4 ; − 5,4 | 0,18 | 0,35 | oui |
| S4 après trois BAD | 19,0 % / 36,6 % | 126 / 290 | − 17,5 ; − 10,3 ; − 7,3 | 0,092 | 0,31 | oui |
| S5 dernière issue RÉSOLUE GOOD (causal) | 31,6 % / 25,5 % | 133 / 368 | + 6,0 ; + 6,2 ; − 0,1 | 0,98 | 1,00 | oui |
| S6 deux dernières résolues BAD (causal) | 21,0 % / 36,0 % | 162 / 334 | − 15,1 ; − 7,8 ; − 7,2 | 0,11 | 0,31 | oui |
| S7 rang modulo 3 (« un sur trois » programmé) | rangs 3, 6, 9… : 26 % ; 1, 4, 7… : 30 % ; 2, 5, 8… : 35 % | 413 | | 0,50 | 0,68 | non |
| S8 rang modulo 2 | 31 % / 30 % | 413 | | 0,32 | 0,55 | non |
| S9 séries (runs) | 158 changements GOOD ↔ BAD contre 158,1 attendus | 423 paires adjacentes | | 1,00 | 1,00 | non |

Le « 1 pump sur 3 » programmé est exclu : après deux BAD, une équipe fait un GOOD 21,6 % du temps
(40 / 185), pas presque toujours ; après trois BAD, 19,0 % (24 / 126). Une série de pertes n'annonce
pas de rebond. Les écarts, non significatifs, iraient plutôt dans l'autre sens (après deux ou trois BAD,
5 à 7 points sous le nul, même sens sur les deux blocs, p 0,09 à 0,18, q 0,31 à 0,35) ; rien de cela
n'est un résultat. S10 (p 0,061, q 0,26) ne passe pas non plus, et les suites ne sont ni groupées ni
alternées (S9 : exactement le nombre de changements attendu). « Après un changement de configuration »
et « après un changement de wallets » : section 5.

## 4. GOOD contre BAD dans la même équipe

AUC intra-équipe = probabilité qu'un GOOD ait une valeur plus haute qu'un BAD de la même équipe (0,5 =
aucune différence) ; nul = permutation dans l'équipe ; BH sur 32. Une variable n'est attribuée à
l'équipe que si elle tient aussi sans le plus grand groupe et à l'intérieur des sessions (amendement 1,
point 7), car le plus grand groupe U, la population diffuse, porte 80 % des paires (GOOD, BAD).

| variable (famille) | AUC | p | q | DISC / SEL | sans le plus grand groupe | dans la session | lecture |
|---|---|---|---|---|---|---|---|
| essaim externe à − 5 s (réaction) | 0,636 | 0,004 | 0,13 | 0,67 / 0,46 | 0,49 | 0,54 | population diffuse, DISCOVERY seul |
| essaim externe à − 10 s (réaction) | 0,610 | 0,019 | 0,24 | 0,66 / 0,47 | 0,48 | 0,56 | idem |
| bots récurrents à − 10 s (réaction) | 0,604 | 0,023 | 0,24 | 0,65 / 0,49 | 0,48 | 0,56 | idem |
| ordre des snipers dans le slot (config.) | 0,415 | 0,064 | 0,51 | 0,43 / 0,46 | 0,45 (p 0,049) | 0,43 (p 0,022) | la plus cohérente, ne passe pas |
| rang dans la session (rythme) | 0,574 | 0,11 | 0,66 | 0,58 / 0,61 | 0,56 | 0,57 | voir section 2 |
| ticket médian (config.) | 0,429 | 0,13 | 0,66 | 0,39 / 0,49 | 0,51 | 0,44 | |
| les 26 autres | 0,43 à 0,57 | ≥ 0,16 | ≥ 0,66 | | | | aucune séparation détectée |

Aucune séparation détectée pour : le nombre de snipers (0,52), le SOL total (0,51), la dispersion des
tickets (0,47), la part d'offre (0,51), le nombre de transactions (0,47), l'achat du créateur (0,49),
l'âge des wallets (0,43), les wallets nouveaux pour l'équipe (0,54), le recouvrement avec le lancement
précédent (0,45), le nombre de financeurs (0,52), le financeur commun avec le précédent (0,52), le délai
financement → achat (0,50), la synchronisation des financements (0,49), la même configuration que le
précédent (0,46), l'intervalle (0,50), les lancements sur 60 min (0,51), les snipers d'autres équipes
parmi les acheteurs (0,51), les acheteurs non snipers du slot de création (0,47), les ventes des snipers
avant l'alerte (0,52), l'âge à l'alerte (0,57), la prime d'entrée (0,47), le taux du marché sur 24 h
(0,49), les alertes et candidats sur 60 min (0,52, 0,56), les lancements des autres équipes sur 30 min
(0,49). Les achats groupés (0,50, p 1,00) sont constants dans chaque équipe, donc pas testables dans
l'équipe. Le témoin négatif (heure de l'alerte) est plat (AUC 0,53, p 0,57) : aucune dérive monotone du
taux d'une équipe dans le temps n'est détectée ; une dérive non monotone n'est pas exclue.

Sensibilités (B = 2 000, 4 × 32 tests, aucune ne compte pour le classement) : 10 p ≤ 0,05 sur 128 pour
6,4 attendus. Les plus basses : le délai financement → achat sans le plus grand groupe (AUC 0,37,
p 0,001 : chez les vraies équipes, les GOOD auraient été financés plus près de l'achat), le taux du
marché à l'intérieur des sessions (0,38, p 0,003), la prime d'entrée en strates L1 (0,35, p 0,005), le
rang et le ticket médian pour le ×3 (0,68 et 0,33, p 0,007 et 0,008). Aucune ne tient à la fois dans la
population principale, sans le plus grand groupe et dans la session. Ce sont des pistes nées des
données, pas des résultats.

Profils médians GOOD / BAD des huit plus grandes équipes (descriptif, médianes parfois sur 1 ou 2 GOOD) :
g570 lance ses GOOD plus tard dans la session (rang 8 contre 3, 7 GOOD sur 20) ; g789 (2 GOOD sur 17)
et g31 (38 sur 115) ont un essaim plus gros sur leurs GOOD (192 contre 25, 19 contre 10) ; g169 et g578
(scripts) ont exactement la même configuration sur leurs GOOD et leurs BAD. Un seul trait revient dans
les six équipes autres que g169 et g578 (dont les financements sont quasi instantanés, 0,5 à 1 s) : le
délai financement → achat est plus court sur les GOOD
(g31 357 contre 362 s ; g570 273 contre 331 ; g5 247 contre 407, 2 GOOD ; g225 110 contre 351, 1 GOOD ;
g789 74 contre 378, 2 GOOD ; g606 120 contre 201, 4 GOOD). C'est descriptif, cohérent avec la
sensibilité sans la population diffuse (AUC 0,37), et ce n'est pas un résultat.

## 5. Changement de configuration

| changement par rapport au lancement précédent de l'équipe | GOOD si changé / si même | n changé / même | excès « changé » | p | q |
|---|---|---|---|---|---|
| configuration exacte des tickets | 34 % / 30 % | 114 / 266 | + 0,3 | 1,00 | 1,00 |
| wallets (Jaccard < 0,5) | 29 % / 33 % | 182 / 198 | + 1,2 | 0,50 | 1,00 |
| financeur dominant | 28 % / 36 % | 162 / 132 | − 0,6 | 0,70 | 1,00 |
| nombre de snipers | 31 % / 31 % | 42 / 338 | + 1,0 | 1,00 | 1,00 |
| SOL total (écart > 5 %) | 27 % / 32 % | 45 / 335 | − 2,0 | 0,84 | 1,00 |

| hétérogénéité à l'intérieur d'une équipe | catégories (≥ 3 lancements) | p | q | même sens |
|---|---|---|---|---|
| entre configurations exactes | 132 (43) | 0,059 | 0,47 | non (SELECTION sous le nul) |
| entre financeurs dominants | 187 (30) | 0,13 | 0,54 | non |
| entre ensembles exacts de wallets | 201 (38) | 0,43 | 1,00 | non |

Aucune configuration particulière de l'équipe n'est associée à ses GOOD de façon détectable. Mêmes
wallets avec des tickets différents, wallets différents avec les mêmes tickets, autre financeur, autre
nombre de snipers : aucun écart au taux de l'équipe n'est détecté (puissance non mesurée pour ces
tests). L'écart brut sur le financeur (28 % contre 36 %) est un effet ENTRE équipes (les équipes qui
changent de financeur ont un taux plus bas) ; dans l'équipe, il tombe à − 0,6 point. Présence ou
absence d'une deuxième équipe : section 6.

Prédiction chronologique (identité d'équipe causale, 352 lancements avec ≥ 3 antécédents ;
DISCOVERY 217 dont 55 GOOD, SELECTION 135 dont 43 GOOD ; logistique L2 fixée d'avance ; le test sur
DISCOVERY porte sur les 204 lancements qui ont un taux de marché) :

| modèle | DISC → SEL : AUC, gain de log-loss sur le marché [IC par équipe] | SEL → DISC | annonce ? |
|---|---|---|---|
| M0 taux du marché 24 h | 0,50 | 0,58 | référence |
| M1 historique de l'équipe | 0,60, + 0,024 [+ 0,003, + 0,047] | 0,56, − 0,009 [− 0,032, + 0,023] | non (un seul sens, comme la forensique) |
| M2 configuration (écart aux habitudes de l'équipe) + rythme | 0,47, − 0,074 [− 0,167, + 0,015] | 0,55, − 0,050 [− 0,094, + 0,017] | non |
| M3 réaction avant l'alerte (essaim, bots, autres équipes, prime) | 0,49, − 0,105 [− 0,304, + 0,022] | 0,50, − 0,013 [− 0,054, + 0,034] | non |
| M4 tout | 0,45, − 0,171 [− 0,362, − 0,021] | 0,55, − 0,063 [− 0,113, + 0,025] | non |

AUC intra-équipe sur le bloc de test : de 0,41 à 0,56, le plus petit p 0,23 (M1, DISC → SEL) ; elles
reposent sur 10 (SELECTION) et 14 (DISCOVERY) équipes qui ont à la fois des GOOD et des BAD.

## 6. Interaction entre équipes et environnement

| test | résultat | p | lecture |
|---|---|---|---|
| I1 issue d'un lancement contre taux GOOD des AUTRES équipes à ± 60 min (584 lancements, 7,3 voisins en moyenne) | corrélation 0,001 ; taux GOOD 26,7 %, 29,4 %, 25,4 % selon le tiers du taux des voisins | 0,20 dans le jour (moyenne nulle 0,06), 0,27 dans équipe × jour, 0,92 global | aucune synchronisation détectée entre équipes à l'échelle de l'heure |
| I1 à ± 30 min | − 0,012 | 0,23 | idem |
| I4 les 10 bots récurrents les plus fréquents à − 10 s (présents sur 199 à 388 lancements) | écarts présent − absent de − 4,8 à + 9,8 points ; le plus fort `HcWPg6…` 38 % contre 28 % (n 98) | 0,073 à 1,0 ; q ≥ 0,47 | rien ne passe ; 4 bots sur 10 vont dans le même sens (+ 3,6 à + 9,8 points) sur les deux blocs |
| I3 snipers d'une équipe B parmi les acheteurs d'une équipe A avant l'alerte | 113 lancements sur 1 015 (11 %) ; 5 paires à ≥ 5 cooccurrences (au plus 7), chacune avec g31 d'un côté | descriptif | pas de couple d'équipes récurrent hors population diffuse |

Pas de « équipe A arrive, puis B déclenche » détecté. Par construction, un bundle appartient à une seule
équipe U (deux équipes qui partageraient un sniper sont fusionnées). Des snipers d'autres équipes
achètent avant l'alerte sur 11 % des lancements, sans couple récurrent hors population diffuse, et les
bons et mauvais lancements des différentes équipes ne tombent pas aux mêmes heures de façon détectable.
Ce qui suit le bundle, c'est l'essaim de bots génériques : médiane de 11 acheteurs externes à − 10 s et
de 8 bots déjà vus sur ≥ 5 lancements antérieurs (variables 21 et 23, médianes sur les 1 015
lancements, sans issue) ; chacun des 10 bots les plus fréquents est présent sur 199 à 388 lancements.

Graphify : non utilisé. Ses graphes indexent le code (AST) et les documents ; les wallets, financeurs
et lancements n'y sont pas. Le graphe équipe → wallet → financeur → lancement existe déjà sous forme
d'union-find dans `mech_45` / `mech_47`, et il n'a rien à montrer côté interaction : 5 paires d'équipes
à ≥ 5 cooccurrences, toutes impliquant la population diffuse. Un dessin n'aurait rien ajouté aux
tableaux.

## 7. D'où vient le phénomène

Décomposition (logistique mixte variationnelle, prime d'entrée en tercile fixe, écarts-types en logit,
estimations sans intervalle) :

| modèle | équipe | session | jour |
|---|---|---|---|
| équipe seule | 0,75 | | |
| équipe + session | 0,67 | 0,30 | |
| équipe + session + jour | 0,63 | 0,25 | 0,43 |
| session + jour (ajout descriptif) | | 0,60 | 0,39 |
| jour seul (ajout descriptif) | | | 0,44 |

Ce partage est fragile : pour les équipes fixes qui vivent une seule session un seul jour, équipe,
session et jour se confondent. Le niveau propre de chaque équipe a été observé en exploratoire par la
forensique des opérateurs (écart-type d'environ 13 points, p nominal ≈ 0,001, non corrigé sur le
registre) ; le jour pèse aussi (taux ×2 du marché par semaine 33, 21, 32, 18 %). M1 (historique de
l'équipe) aide dans un seul sens (DISC → SEL) et pas dans l'autre : il n'annonce rien selon la règle. À l'intérieur d'une équipe, aucune
séparation détectée : ni configuration, ni rythme, ni séquence, ni autre équipe, ni contexte mesuré.

Interprétation, non testée ici, compatible avec les études antérieures (WSMO, groupes coordonnés ; leurs chiffres VALIDATION couvrent
une période postérieure au 15/09) :

1. Le capital. Les snipers d'un lancement coordonné reçoivent une médiane de 25 SOL et en dépensent 20
   dans le slot de création ; entre deux lancements, le SOL repart au financeur du premier (60 % en
   TRAIN, 92 % en VALIDATION), qui refinance les mêmes snipers une médiane de 21 minutes plus tard
   (18 en VALIDATION) (`WSMO-signal-search/economic_mechanics/results.md`). Le pas médian mesuré ici
   dans une session, 20,6 minutes, en est proche. Les deux chiffres mesurent l'écart entre lancements
   des mêmes wallets : leur concordance ne montre pas que le capital fixe la cadence, elle est seulement
   compatible avec cette idée.
2. La sortie. Les snipers coordonnés n'ont rien bougé avant l'alerte (médiane 0 %) ; ils transfèrent
   leurs tokens à un wallet de sortie une médiane de 11 s après l'achat (83 % par simple transfert)
   (economic_mechanics), et ce wallet les vend lui-même sur PumpSwap une médiane de 81 s plus tard
   (p90 330 s), à des acheteurs non identifiés (`exit_destination/results.md`). La liquidation de
   l'équipe tombe donc APRÈS notre entrée à alerte + 5 s, dans la fenêtre d'une heure où se joue le ×2.
   Aucune étude citée ne calcule le gain de l'équipe.
3. Lecture possible : la part d'offre que l'équipe met en vente est presque la même à chaque lancement
   (77,7 % en médiane, fixée par la règle de sélection du détecteur) et sa configuration ne diffère pas
   de façon détectable entre ses GOOD et ses BAD. Un GOOD demanderait alors que la demande extérieure
   absorbe cette liquidation et pousse encore le prix ; l'origine de cette demande n'est pas mesurée, et ce
   que nous en voyons avant l'alerte (l'essaim) ne la sépare pas à l'intérieur des vraies équipes. Le
   lien entre la vente de l'équipe et l'issue n'est pas mesuré ici.

## 8. Ce qui n'est pas exclu, et une seule hypothèse

Pas exclus : des effets intra-équipe d'AUC entre 0,5 et 0,68, des dépendances de séquence jusqu'à
15 points, tout effet des sections 5 et 6 ou des interactions (puissance non mesurée), des rythmes
propres à une ou deux équipes (19 équipes seulement ont ≥ 10 lancements éligibles), des interactions par
des wallets qui ne sont ni snipers ni acheteurs avant l'alerte. Les achats des autres équipes dans le
slot de création ne sont pas dans la liste des acheteurs externes : ils ne sont comptés que par la
variable « acheteurs non snipers du slot de création », qui ne sépare rien.

Une hypothèse, pour un test prospectif seulement, pas une règle : **« à partir du 7e lancement d'une
session, une équipe fait plus de ×2 »** : 41 / 103 = 40 % contre 84 / 310 = 27 % aux rangs 1 à 6, dans
les 413 lancements des 28 équipes mixtes ; + 8,0 points sur le taux propre de l'équipe ; même sens sur
les deux blocs ; p 0,14, q 0,34 ; p 0,24 avec des sessions à 60 min. Le n effectif est petit : environ
une vingtaine de sessions dans une douzaine d'équipes, dont une bonne part de la population diffuse g31.
Le rang est calculé sur l'identité U finale : à refaire en identité causale avant tout test. Raison
possible, non testée : une équipe ne prolonge une session que tant que ses sorties trouvent preneur, ce
qui sélectionnerait des moments où la demande suit. Même vraie, elle reste sous le seuil de rentabilité
du trade déclaré (45,8 %) : elle ne donne pas d'edge seule. Le délai financement → achat (section 4) reste une observation de sensibilité, pas une
hypothèse.

Rien n'est proposé pour VALIDATION ou OOS ; OOS reste vierge. Aucune nouvelle phase de recherche n'est
lancée.

## Notes sur les données et écarts

- Population, labels, identité U, prime en tercile : identiques à la forensique des opérateurs.
  SELECTION avait déjà été lu (signal_search le 02/10, forensique des opérateurs le 06/10, rapport écrit
  le 07/10).
- Variables d'historique (« précédent de l'équipe », rang, sessions) sur l'identité U finale pour les
  sections 2 à 4, de la section 5 (sauf la prédiction) et de la section 6 ; seule la prédiction
  chronologique (fin de la section 5) utilise l'identité causale. Aucun test causal n'a passé, la
  vérification prévue en identité causale (amendement 1, point 8) n'a donc pas eu lieu.
- La sensibilité L1 garde les variables calculées en U (`strata_L1_variables_U`).
- Revue avant calcul : 0 BLOQUANT ; 12 MAJEUR (certains signalés par deux auditeurs), dont 9 confirmés
  par l'agent de réfutation et 3 rétrogradés ; tous traités avant les issues réelles (amendement 1) ;
  MINEURS traités ou écrits ici.
- Contrôles v1 (100 mondes) remplacés par la v2 (200 mondes nuls, 50 mondes par effet planté,
  puissance selon la vraie règle) ; les deux sont au registre comme données synthétiques. Écart au
  pré-enregistrement : B = 1 000 (500 par bloc) dans les contrôles au lieu de 2 000.
- Ajouts descriptifs hors pré-enregistrement : modèles de variance « session + jour » et « jour seul ».
- Revue des conclusions : deux auditeurs indépendants (claims-auditor) ; leurs corrections de chiffres
  et de formulation sont reprises dans cette version, sans changement de méthode.
