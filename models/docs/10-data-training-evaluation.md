# 10 — Données, entraînement, évaluation

## Datasets

### Datasets présents dans le projet (local)

Ils sont stockés dans `Data/raw/` :

- `Data/raw/Dataset_flaged.csv` : dataset **flaggé** (supervisé)
- `Data/raw/dataset_legit_no_status.csv` : dataset **non flaggé**, transactions “valides” uniquement
- `Data/raw/dataset_fraud_no_status.csv` : dataset **non flaggé**, transactions “non valides” uniquement
- `Data/raw/dataset_mixed_no_status.csv` : dataset **non flaggé**, mix

> Note : “valide / pas valide” = notion métier du dataset.  
> Pour le ML, on distingue surtout “label présent (supervisé)” vs “pas de label (unsupervisé / scoring anomalies / règles)”.

### Dataset 1 — `Dataset_flaged.csv` (supervisé, format PaySim)

- **Format** : CSV
- **Nombre de lignes (approx)** : 110 814 lignes (≈ 110 813 transactions, hors header)
- **Colonnes (11)** :
  - `step` (int)
  - `type` (cat) : ex `PAYMENT`, `TRANSFER`, `CASH_OUT`, ...
  - `amount` (float)
  - `nameOrig` (id)
  - `oldbalanceOrg` (float)
  - `newbalanceOrig` (float)
  - `nameDest` (id)
  - `oldbalanceDest` (float)
  - `newbalanceDest` (float)
  - `isFraud` (label 0/1)
  - `isFlaggedFraud` (flag 0/1)
- **Usage** :
  - apprentissage supervisé → `s_sup`
  - base pour tester la logique règles/ML sur un dataset labelisé

### Datasets 2–4 — `dataset_*_no_status.csv` (non flaggés, format “Transaction” Payon)

Ils ont le **même schéma** (17 colonnes) et **pas de label**.

#### Schéma commun (17)
- `transaction_id`
- `created_at`
- `provider_created_at`
- `executed_at`
- `provider`
- `provider_tx_id`
- `initiator_user_id`
- `source_wallet_id`
- `destination_wallet_id`
- `amount`
- `currency`
- `transaction_type`
- `direction` (valeurs observées : `IN` / `OUT`)
- `country`
- `city`
- `description`
- `metadata.raw_payload` (string contenant un JSON sérialisé)

#### Dataset 2 — `dataset_legit_no_status.csv` (transactions valides)

- **Nombre de lignes (approx)** : 29 743 lignes (≈ 29 742 transactions)
- **Caractéristiques observées (exemples)** :
  - `metadata.raw_payload` contient souvent `source_device`, `ip_version`, `is_vpn`
  - montants majoritairement “normaux” (mais présence possible de montants élevés)

#### Dataset 3 — `dataset_fraud_no_status.csv` (transactions “pas valides”)

- **Nombre de lignes (approx)** : 32 790 lignes (≈ 32 789 transactions)
- **Caractéristiques observées (exemples)** :
  - `destination_wallet_id` contient souvent des ids type `mule_*`
  - `metadata.raw_payload` contient `is_vpn: true`, `source_device: "bot_script"` et un champ `risk_score` élevé (ex: 86–99)
  - `executed_at` et `provider_tx_id` peuvent être vides (valeurs manquantes)

#### Dataset 4 — `dataset_mixed_no_status.csv` (mix)

- **Nombre de lignes (approx)** : 34 256 lignes (≈ 34 255 transactions)
- **Caractéristiques observées (exemples)** :
  - `metadata.raw_payload` contient souvent `is_vpn` + un `risk_score` (faible sur les exemples vus)

### Remarques importantes (mappings)

- **Devise** : les exemples observés sont en `EUR` dans les CSV “Payon”, alors que le contrat API v1 cible `PYC`.
  - Guideline : traiter `currency` comme un champ catégoriel et/ou mapper `EUR → PYC` dans le pipeline d’entraînement si besoin.
- **Direction** : CSV = `IN`/`OUT` vs API = `incoming`/`outgoing`
  - mapping recommandé : `IN → incoming`, `OUT → outgoing`
- **Timestamps** : souvent sans timezone explicite (ex: `2025-08-02T04:03:12`)
  - hypothèse v1 : UTC, à documenter si besoin
- **Metadata** : `metadata.raw_payload` est un JSON sérialisé (string)
  - guideline : parser ce champ en dict si on veut en extraire `is_vpn`, `source_device`, etc.

## Supervisé vs non supervisé (comment on s’en sert)

- **Supervisé** : `Dataset_flaged.csv` (label via `isFraud`)
- **Non supervisé** :
  - “normal-only” recommandé : `dataset_legit_no_status.csv`
  - “mix” utile pour tests de robustesse : `dataset_mixed_no_status.csv`
  - dataset “pas valide” utile pour tests adversariaux/règles : `dataset_fraud_no_status.csv`

## Mapping PaySim → contrat Payon (guideline)

PaySim a ses propres colonnes. Pour documenter clairement le pipeline, on maintient un mapping explicite :

- ids → `transaction_id`, `source_wallet_id`, `destination_wallet_id` (ou champs équivalents)
- `amount` → `amount`
- type PaySim → `transaction_type`
- timestamps PaySim → `created_at`
- currency : forcer `PYC` en v1 (ou champ constant)

## Split temporel

Important : ne pas faire de split aléatoire (risque leakage).

Guideline v1 :

- train : 70%
- val : 15%
- test : 15%

basé sur l’ordre temporel.

## KPI & monitoring offline

On considère le ML “bon” si :

- Recall fraude élevé
- Precision sur `BLOCK` élevée
- PR-AUC élevée
- faux positifs contenus
- stabilité (pas de dérive brutale)

KPI suivis :

- Recall fraude
- Precision sur `BLOCK`
- PR-AUC
- % transactions `BLOCK` / `REVIEW`

## Seuils pilotés par volume

Les seuils sont choisis pour atteindre une cible de volume (ex: top 0,1% bloqués), puis validés via les KPI.

Voir `docs/06-scoring-thresholds.md`.

