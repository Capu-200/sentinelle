# 03 — Règles métier

## Objectif

Détecter des cas évidents, de manière **déterministe**, **rapide** et **explicable**, même sans ML.

Chaque règle peut :

- ajouter un `reason` (id stable)
- contribuer à un `rule_score` ∈ \[0,1\]
- parfois forcer une décision (`BLOCK`) si c'est un cas "hard" (ex: contrainte KYC light, pays interdit)
- appliquer un `BOOST_SCORE` pour augmenter le risque sans bloquer

## Documentation

- **Règles détaillées** : Voir `03-rules-detailed.md` pour la liste complète des règles (R1-R15)
- **Questions de clarification** : Voir `03-rules-questions.md` pour les points à clarifier avant implémentation

> Les règles détaillées R1→R15 sont définies dans `03-rules-detailed.md`.  
> Cette page conserve les règles initiales R1→R4 comme référence historique.

## Convention “reasons”

- **Format** : snake_case, stable dans le temps
- **Exemples** : `amount_over_kyc_limit`, `sanctioned_country`, `high_velocity`, `new_destination_wallet`

## Rule score (proposition v1)

Proposition simple :

- `rule_score = min(1, sum(rule_contribution))`

avec des contributions par règle (ci-dessous).

## R1 — KYC light : montant max

- **But** : bloquer les transactions qui dépassent le plafond KYC light.
- **Condition** : `amount > 300` (en `PYC`)
- **Action** : **HARD BLOCK**
- **Reason** : `amount_over_kyc_limit`
- **Contribution rule_score** : 1.0

## R2 — Pays interdit / sanctionné

- **But** : bloquer les transactions provenant de pays interdits (ex: Corée du Nord).
- **Condition** : `country` ∈ liste interdite (ex: `["KP"]`)
- **Action** : **HARD BLOCK**
- **Reason** : `sanctioned_country`
- **Contribution rule_score** : 1.0

> Note : si `country` est absent, la règle ne s’applique pas (pas de blocage “par défaut”).

## R3 — Vélocité anormale (burst)

- **But** : détecter un comportement de spam/exfiltration (beaucoup de transferts en peu de temps).
- **Dépend** : features historiques du `source_wallet_id`.
- **Condition (proposée)** :
  - `tx_count_out_1m > 5` **ou**
  - `tx_count_out_1h > 30`
- **Action** : `REVIEW` (ou `BLOCK` si combiné avec R4 + montant élevé)
- **Reason** : `high_velocity`
- **Contribution rule_score** : 0.6

## R4 — Nouveau destinataire + montant inhabituel

- **But** : nouveau bénéficiaire + montant au-dessus de l’habitude.
- **Dépend** : historique des relations `source_wallet_id -> destination_wallet_id`.
- **Condition (proposée)** :
  - `is_new_destination_30d = true` **et**
  - `amount > p95_amount_source_30d`
- **Action** : `REVIEW` (ou `BLOCK` si `amount` très au-dessus, ex: `> p99`)
- **Reason** : `new_destination_wallet` + `amount_unusual`
- **Contribution rule_score** : 0.6 (cap à 1.0 avec R3/R4 combinés)

## Sortie règles (attendue)

Les règles retournent :

- `rule_score` : \[0,1\]
- `reasons` : liste (ids stables)
- `hard_block` (bool) : true si R1/R2 déclenchée

