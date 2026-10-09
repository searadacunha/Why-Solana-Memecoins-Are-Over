# Revue des conclusions, passage 1 : BUNDLE_TEAM_RHYTHM_2026-10-07.md (2026-10-07)

Deux claims-auditor indépendants (workflow `team-rhythm-claims-audit`, run wf_c6171f53-127). Verdict : FAIL
pour les deux (critères 1, 4, 5, 7, 10 ; le second aussi 8). Classement C confirmé par les deux (aucun
drapeau « passe » dans `tables/team_rhythm.json`). Toutes les corrections ci-dessous ont été reprises dans
le rapport (formulation et chiffres, aucune méthode changée). Erreur de fond corrigée : la section 7 disait
que l'équipe vend avant notre entrée ; les études citées montrent une liquidation par les wallets de sortie
une médiane de 81 s après le transfert, donc après l'entrée à alerte + 5 s.

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
| 9 | PASS |
| 10 | FAIL |

Corrections demandées (32) :

- « C'est le cycle du capital mesuré par l'étude economic_mechanics (refinancement des mêmes snipers une médiane de 21 min plus tard). » : formulation : identité affirmée, non testée ici ; la source donne 21 min sur TRAIN et 18 min sur VALIDATION
- « les équipes fixes travaillent par sessions de 4 à 5 heures, puis disparaissent. » : formulation : généralisation ; 5 des 9 équipes fixes à ≥ 10 lancements seulement (team_rhythm.json, teams_ge10)
- « Aucun des 17 tests rythme / séquence ne relie ce rythme au GOOD (meilleur q 0,27). » : formulation : q_bh_sections_2_3 = 0,2647, arrondi 0,26 ; même erreur pour R1, R2, R5 et S10 aux lignes 87, 89, 92 et 94
- « presque jamais à moins de 10 min (4,7 % des intervalles, contre 47 % entre deux alertes quelconques du marché) » : formulation : dénominateur manquant
- « Changer de configuration, de wallets, de financeur, de nombre de snipers ou de mise ne change pas le taux. » : formulation : une absence de détection présentée comme une absence d'effet ; puissance non mesurée pour C1
- « Les issues des autres équipes à ± 60 min n'ont aucun lien avec celle d'un lancement » : formulation : une absence de détection présentée comme une absence de lien ; pas de puissance pour I1
- « À l'intérieur d'une équipe, le GOOD ou le BAD ne dépend de rien de ce que nous mesurons avant l'alerte. » : formulation : dépasse la puissance mesurée
- « L'équipe a vendu bien avant que le ×2 se joue. » : formulation : contredit par les sources. economic_mechanics/results.md:114-115 : les snipers coordonnés n'ont rien sorti avant l'alerte (médiane 0 %). exit_destination/results.md:18, 62 : vente une médiane de 81 s après le transfert. Le mécanisme est aussi présenté comme une explication, pas comme u
- « excluent donc les effets de cette taille, pas les petits (AUC ≤ 0,6, écarts de séquence ≤ 10 points). » : formulation : + 15 points n'est retrouvé que dans 31 mondes sur 50, et la puissance n'est pas mesurée entre AUC 0,6 et 0,68 ; contredit aussi la section 8 (10 à 15 points)
- « d'AUC 0,68 est retrouvé 94 fois sur 100 ; une dépendance « + 15 points après un BAD » 62 fois sur 100, » : formulation : le dénominateur est de 50 mondes plantés par niveau, pas 100
- « une session de 4 à 5 heures, un lancement toutes les 17 à 24 minutes, très régulier (CV 0,2 à 0,4), » : formulation : contredit par g570 dans le même tableau (4 sessions, CV 0,57), ainsi que par g5, g679, g745 et g493 (CV 0,45)
- « p 0,043 avec des sessions coupées à 180 min, et AUC intra-équipe du rang 0,68 pour le ×3 (p 0,007, » : formulation : sensibilité citée de façon sélective ; le p à 60 min est omis et le p 0,007 sort d'une famille de 128 tests
- « S'il y a quelque chose, c'est l'inverse (une série de BAD tend à continuer » : formulation : des p nominaux non significatifs (q ≥ 0,31) lus comme une tendance
- « sessions (S10, p 0,061) : des sessions un peu meilleures que d'autres, pas une alternance. » : formulation : un p nominal (q 0,26) présenté comme un constat
- « aucune dérive du taux d'une équipe dans le temps ne » : formulation : un témoin plat ne montre qu'une absence de dérive monotone détectée
- « g225 et g789 financent leurs snipers plus près de l'achat sur leurs GOOD » : formulation : médianes calculées sur 1 GOOD (g225, 1 sur 17 éligibles) et 2 GOOD (g789, 2 sur 17) ; même remarque pour l'essaim de g789
- « | entre financeurs dominants | 187 (30) | 0,14 | 0,54 | non | » : formulation : p = 0,1349 dans configuration_changes.C2_between_dominant_funders
- « le taux reste celui de l'équipe » : formulation : une absence de détection présentée comme un fait
- « AUC intra-équipe sur le bloc de test : de 0,41 à 0,56, aucune avec p < 0,23 » : formulation : M1 DISC→SEL a un p de 0,2299, donc inférieur à 0,23
- « n'apparaissent presque jamais parmi les acheteurs avant l'alerte » : formulation : 113 lancements sur 1 015, soit 11 %
- « commun à toutes les équipes » : formulation : non mesuré équipe par équipe. Les médianes 11 et 8 de la même phrase ne figurent dans aucune sortie (reproduites sur 1 015 lancements depuis derived/feat_swarm.jsonl.gz et feat_team_rhythm_ext.jsonl.gz)
- « la session presque rien une fois l'équipe » : formulation : avertissement manquant. Pour les équipes fixes à session unique, équipe, session et jour se confondent, et les écarts-types variationnels n'ont pas d'intervalle
- « revend à l'essaim de bots dans les secondes qui » : formulation : absent de la source citée. economic_mechanics/results.md:97-99 et 104 décrivent un transfert vers les wallets de sortie, sans observer la vente ; exit_destination/results.md:18, 62 donne une vente sur PumpSwap une médiane de 81 s après le transfert, contrepartie non identifiée
- « L'équipe gagne au moment de la sortie, avant notre entrée. » : formulation : contredit par les sources. Aucun profit n'est calculé (economic_mechanics:104-105, exit_destination:7) et la sortie a lieu après l'alerte (economic_mechanics:114-115)
- « L'équipe n'a aucune raison de régler sa configuration sur une issue qui ne la concerne plus » : formulation : intention prêtée, sans preuve ; la suite de la phrase transforme une absence de détection en égalité
- « Ce qui reste prévisible tient au niveau de l'équipe (certaines équipes choisissent des tokens ou des » : formulation : intention prêtée (« choisissent ») ; « prévisible » contredit l'échec de M1 dans un sens et la forensique (décrire, pas prédire)
- « (40 % contre 27 %, n 103, même sens sur les deux blocs, q 0,34) » : formulation : numérateurs, excès intra-équipe, sensibilité à 60 min, n effectif et identité non causale manquants
- « VALIDATION et OOS ne sont ni » : formulation : X.npz (1 657 lignes, features VALIDATION et OOS comprises) est chargé, comme le reconnaît la ligne 287
- « Aucune donnée nouvelle, » : formulation : « aucun réseau » est contredit par la section 0 (structure de Ponytail lue par l'API GitHub)
- « registre : 381 comparaisons sur données réelles (ligne » : formulation : le total du registre n'est pas cité (compter : 31 655 945 comparaisons réelles, Bonferroni 1,58e-9)
- « | Agent Skills (`~/.agents/skills`) | vide | aucun | » : formulation : le dossier ~/.agents n'existe pas
- « SELECTION avait déjà été lu (signal_search le 02/10, forensique le 07/10). » : formulation : le registre date la forensique du 2026-10-06 à 18:05 UTC (fichier BUNDLE_OPERATOR_FORENSICS_2026-10-06.md)

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
| 8 | FAIL |
| 9 | PASS |
| 10 | FAIL |

Corrections demandées (34) :

- « Aucun des 17 tests rythme / séquence ne relie ce rythme au GOOD (meilleur q 0,27). » : formulation : chiffre mal arrondi. q_bh_sections_2_3 = 0,2647 pour R1, R2, R5 et S10 ; même erreur dans les cases q des lignes R1 (:87), R2 (:89), R5 (:92) et S10 (:94).
- « | entre financeurs dominants | 187 (30) | 0,14 | 0,54 | non | » : formulation : chiffre mal arrondi, p = 0,1349.
- « d'AUC 0,68 est retrouvé 94 fois sur 100 ; une dépendance « + 15 points après un BAD » 62 fois sur 100, « + 20 points » 92 fois sur 100, « + 10 points » 10 fois sur 100. » : formulation : mauvais dénominateur. Chaque contrôle planté compte 50 mondes, pas 100 (controles/team_rhythm_controls.json). L'effet n'est planté que sur snipe_sol et testé sur S1.
- « Les résultats négatifs excluent donc les effets de cette taille, pas les petits (AUC ≤ 0,6, écarts de séquence ≤ 10 points). » : formulation : la portée de la puissance est trop large. Elle n'a été mesurée que pour la section 4 (une variable) et pour S1, pas pour les sections 5 et 6 ni pour I1 et I4 ; la zone 0,60 à 0,68 n'est pas couverte.
- « (médiane de 11 acheteurs externes à − 10 s ; médiane de 8 bots déjà vus sur ≥ 5 lancements antérieurs) » : formulation : ces chiffres ne figurent dans aucune sortie de l'étude, seulement dans un print de session, et leur dénominateur n'est pas donné.
- « AUC intra-équipe sur le bloc de test : de 0,41 à 0,56, aucune avec p < 0,23 » : formulation : faux au sens strict, M1 DISC → SEL a p = 0,2299. De plus, le test SEL → DISC porte sur 204 lignes, pas 217.
- « SELECTION avait déjà été lu (signal_search le 02/10, forensique le 07/10). » : formulation : date fausse. La ligne operator_forensics du registre est datée 2026-10-06 18:05 UTC.
- « | Claude Code 2.1.263 | actif, application de bureau, modèle Opus 5.5 | | » : formulation : version fausse. La session de bureau tourne en 2.1.286 (transcript et processus) ; 2.1.263 est la CLI `claude` du PATH.
- « | Agent Skills (`~/.agents/skills`) | vide | aucun | » : formulation : le dossier ~/.agents n'existe pas.
- « Aucune donnée nouvelle, aucun réseau. » : formulation : contredit la section 0, qui a lu la structure de Ponytail par l'API GitHub.
- « C'est le cycle du capital mesuré par l'étude economic_mechanics (refinancement des mêmes snipers une médiane de 21 min plus tard). » : formulation : une interprétation est écrite comme un fait. Le 21 min (18 en VALIDATION) mesure lui aussi l'écart entre lancements des mêmes wallets.
- « Avec un mécanisme qui l'explique (section 7) : la cadence de l'équipe est celle de son capital, pas celle des pumps. L'équipe a vendu bien avant que le ×2 se joue. » : formulation : mécanisme présenté comme un résultat, et sa deuxième phrase est contredite par economic_mechanics:114-115 (médiane de 0 % [2 %] des tokens bougés avant l'alerte) et par exit_destination (vente 81 s après la remise).
- « 1. La cadence de 20 minutes est celle du capital. L'équipe achète environ 78 % de l'offre dans le slot de création (economic_mechanics, non remesuré ici), revend à l'essaim de bots dans les secondes q » : formulation : l'étude citée parle de transferts, pas de ventes (83 %, première action 11 s après l'achat) ; la vente n'y est pas observée. D'après exit_destination, c'est le wallet de sortie qui vend, une médiane de 81 s plus tard, à des acheteurs non identifiés. Les 78 % sont fixés par la règle de 
- « Le pas médian mesuré ici dans une session, 20,6 minutes, correspond à ce cycle » : formulation : le rapprochement est presque tautologique, les deux chiffres mesurent l'écart entre lancements des mêmes wallets.
- « 2. L'équipe gagne au moment de la sortie, avant notre entrée. » : formulation : contredit les études citées. Aucun profit n'est calculé (economic_mechanics:106-107), les tokens coordonnés ne sont presque pas bougés avant l'alerte (médiane 0 % [2 %]), et la vente a lieu une médiane de 81 s après la remise, donc après l'entrée à alerte + 5 s.
- « L'équipe n'a aucune raison de régler sa configuration sur une issue qui ne la concerne plus : ses GOOD et ses BAD ont la même configuration, le même financement, le même rythme. » : formulation : une intention est prêtée sans preuve, et l'absence d'écart détecté est présentée comme une égalité. Hors population diffuse, le délai financement → achat donne AUC 0,37, p 0,001, et les 6 équipes non-script des profils vont dans le même sens.
- « 3. Ce qui reste prévisible tient au niveau de l'équipe (certaines équipes choisissent des tokens ou des heures où la demande suit un peu plus souvent) » : formulation : M1 (historique d'équipe) n'annonce rien dans les deux sens, et le choix prêté aux équipes n'est pas démontré.
- « Chaque équipe a sa petite différence, aucune n'est commune. » : formulation : contredit par les profils publiés. Le délai financement → achat est plus court sur les GOOD dans les 6 équipes non-script (g31, g570, g5, g225, g789, g606), et certaines médianes GOOD reposent sur 1 ou 2 GOOD.
- « g225 et g789 financent leurs snipers plus près de l'achat sur leurs GOOD (110 s contre 351 s, 74 s contre 378 s) » : formulation : dénominateur absent. g225 n'a qu'1 GOOD sur 17 éligibles, g789 2 sur 17.
- « Le témoin négatif (heure de l'alerte) est plat (AUC 0,53, p 0,57) : aucune dérive du taux d'une équipe dans le temps ne fabrique d'effet. » : formulation : ce témoin AUC ne détecte qu'une dérive monotone.
- « Les équipes fixes (mêmes 4 wallets) travaillent comme une équipe de quart : une session de 4 à 5 heures, un lancement toutes les 17 à 24 minutes, très régulier (CV 0,2 à 0,4), puis elles disparaissent » : formulation : généralisation abusive. g570, équipe fixe du tableau, a 4 sessions sur 3 jours et un CV de 0,57 ; hors tableau, g5 a 9 sessions du 08-21 au 09-04 et g745 4 sessions sur 6 jours. Même correction pour « les équipes fixes travaillent par sessions de 4 à 5 heures, puis disparaissent » (:40
- « Début, milieu et fin de session : la fin semble meilleure (36 % contre 26 % au début), mais rien ne tient après correction. » : formulation : la fin est au-dessus sur DISCOVERY (+ 12,0 points) mais en dessous sur SELECTION (− 5,1). Le « même sens : oui » du tableau porte sur le χ², pas sur la direction de la fin.
- « un χ² au-dessus du nul sur DISCOVERY et sur SELECTION séparément, p 0,043 avec des sessions coupées à 180 min, et AUC intra-équipe du rang 0,68 pour le ×3 (p 0,007, sensibilité). » : formulation : sensibilité choisie. La coupure à 60 min donne p 0,24 et n'est pas citée, et l'AUC du ×3 est une des 128 sensibilités (10 p ≤ 0,05 pour 6,4 attendus).
- « (40 % contre 27 %, n 103, même sens sur les deux blocs, q 0,34) » : formulation : il manque les dénominateurs, l'excès ajusté à l'équipe et le n effectif. D'après les chronologies de teams_ge10 : environ 22 sessions de 13 équipes, g31 en fournit environ 40 %.
- « Changer de configuration, de wallets, de financeur, de nombre de snipers ou de mise ne change pas le taux. » : formulation : une absence de détection est écrite comme une absence d'effet, sans puissance mesurée pour la section 5.
- « Les issues des autres équipes à ± 60 min n'ont aucun lien avec celle d'un lancement » : formulation : absence de détection écrite comme une absence de lien ; la puissance d'I1 n'est pas mesurée.
- « les autres équipes n'apparaissent presque jamais parmi les acheteurs avant l'alerte » : formulation : 113 lancements sur 1 015, soit 11 %, ce n'est pas « presque jamais ».
- « 5 paires d'équipes à ≥ 5 cooccurrences, toutes dans la population diffuse. » : formulation : chaque paire a UN membre dans g31, pas les deux.
- « S'il y a quelque chose, c'est l'inverse (une série de BAD tend à continuer, 5 à 7 points sous le nul, même sens sur les deux blocs, p 0,09 à 0,18) » : formulation : des p nominaux sont lus comme une tendance, sans leurs q.
- « L'équipe porte le niveau moyen (déjà montré : écart-type d'environ 13 points, p ≈ 0,001) » : formulation : un p nominal de la forensique exploratoire, sur les mêmes données, est présenté comme acquis. Le registre compte 31 655 945 comparaisons réelles (Bonferroni 1,58e-09).
- « registre : 381 comparaisons sur données réelles (ligne `team_rhythm`), 49 350 sur données synthétiques. » : formulation : le seuil corrigé sur tout le registre (`compter`) n'est pas cité.
- « presque pas de la session (0,25) » : formulation : ce sont des écarts-types estimés par VB, sans intervalle, et équipe et jour sont confondus pour les équipes d'un jour (la forensique le dit elle-même).
- « les achats groupés (0,50) » : formulation : AUC 0,500 et p 1,00 dans les 6 analyses, signe que la variable est constante dans chaque équipe ; elle n'est donc pas testable dans l'équipe.
- « Contrôles v1 (100 mondes) remplacés par la v2 (200 mondes nuls, puissance selon la vraie règle) ; les deux sont au registre comme données synthétiques. » : formulation (écart non déclaré) : le prérég fixe B = 2 000 dans les contrôles, le code utilise B = 1 000 (500 par bloc), voir mech_47:40-41 et controles JSON. Les modèles de variance « session + jour » et « jour seul » sont hors prérég. Faut-il relancer les contrôles à B = 2 000 ? C'est à Benjamin d

