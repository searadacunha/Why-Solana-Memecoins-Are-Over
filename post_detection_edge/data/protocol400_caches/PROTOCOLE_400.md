# Protocole hors échantillon : les quatre candidats du 29/08/2026

Écrit le 29/08/2026 à 18:36 UTC, **point de coupure T0 = 2026-08-29 18:36:00
UTC**. Tout ce qui précède T0 (325 alertes) a servi à TROUVER les candidats,
rien de ce qui précède ne compte. Rien de ce fichier ne se retouche après.
Script : `protocole_400.py`. Il n'affiche que des COMPTES tant que la taille
requise n'est pas atteinte ; `--forcer` affiche tout et inscrit un « regard en
route » dans `protocole_400_regards.log`. Les taux qui en sortiraient avant la
taille ne sont pas des résultats.

Définitions communes
- Alerte de test : `alerte_lancement` avec `t > T0`.
- Succès : ×2 CONFIRMÉ dans la série (deux relevés consécutifs ≥ 2, ou un seul
  hors fenêtre fine), comme `elimination_precoce.x2_confirme`.
- Échec : aucun ×2 confirmé ET âge ≥ 24 h (pas 3 h : la marge de MATURITE_S
  est consommée). Une alerte plus jeune sans ×2 ne compte pas encore.
- Wilson 95 %. Fisher bilatéral exact.

C1. Acteur groupé hors lignée 4kwM (trouvé le 29/08 sur 66 lancements : 55 %
    de ×2 confirmés, +20 % par trade en backtest).
    Population : `outil == groupe` et aucun financeur `4kwMyUNQVYkKrUU9Zatf8cQsWbBy2tvGgtX4YWQX6gQb`
    ni `B1pCmsG1EjDKXibCezG2maQdYbHKXkuR19EQBEKPNxcX` dans la lignée (3 sauts)
    des snipers et du créateur. Lignée collectée par `--collecte`, snipers et
    créateur, 3 sauts, mêmes règles que `financeurs.py`.
    Taille : 40 alertes de test tranchées (succès ou échec).
    Confirmé : borne basse de Wilson > 40 % ET rendement moyen du backtest
    (`backtest_x2.trade`, 3 % de frais) > 0. Rétracté : taux ponctuel < 45 %.
    Sinon non conclusif, et la taille passe à 80, une seule fois.
C1b. Lignée 4kwM : ses 10 premières alertes de test tranchées. 0 ×2 : élimination
    confirmée. ≥ 1 ×2 : rétractée. Pas d'extension.
C2. Nom copié : symbole (insensible à la casse) identique à un coin pump.fun
    ≠ mint, créé dans [t − 48 h, t[, dont `ath_market_cap` ∈ [1 M$, 1e12[ et
    `ath_market_cap_timestamp` < t. Source : `coins?searchTerm=SYM&sort=market_cap`,
    lue à l'évaluation. Taille : 15 copies tranchées. Confirmé : Wilson bas
    > 40 %. Rétracté : taux ponctuel < 45 %. Sinon non conclusif, taille 30.
C3. Densité faible à 60 s, dans la population C1 : n60 = transactions sur le
    pool dans [t, t + 60 s[, mesurées avec curseur temporel (`demande_reprise`),
    seuil FIXÉ n60 ≤ 100 (médianes vues : 65 contre 150).
    Taille : 30 alertes C1 tranchées avec n60. Confirmé : Fisher p < 0,05 ET
    taux (n60 ≤ 100) > taux (n60 > 100). Rétracté sinon.
C4. Second verdict à 15 min : parmi les alertes de test sans ×2 confirmé avant
    900 s, celles dont le multiple au dernier relevé ≤ 900 s vaut ≤ 0,50 sont
    « éliminées ». Taille : 60 éliminées tranchées. 0 ×2 ensuite : confirmé.
    ≥ 2 : rétracté. 1 : non conclusif, taille 100, une seule fois.

C6. Destination du noyau (ajouté le 30/08 après `destinations_noyau.py`,
    T0 identique) : acteur unitaire, sortie du noyau ANTÉRIEURE à l'alerte,
    destination de transfert déjà vue dans un lancement antérieur à l'alerte
    (`destinations_cache.json` + `sortie_noyau_cache.json`, collecte manuelle
    `sortie_noyau.py` puis `destinations_noyau.py --collecte`, ~15 crédits par
    alerte unitaire). Hypothèse : réutilisée < jamais vue. Taille : 30
    « jamais vue » tranchées. Confirmé : Fisher p < 0,05 dans ce sens.
    Rétracté sinon. Ce n'est pas un filtre à 80 %, c'est une élimination.

Coût : lignée ~15 crédits par alerte groupée, n60 ~7 crédits par alerte C1,
C2 et C4 gratuits. Ordre de grandeur 400 à 500 crédits par jour.

Commande, à lancer une fois par jour :
    cd ~/Documents/Crypto/lafetecontinue_bot/analyse && python3 protocole_400.py --collecte
