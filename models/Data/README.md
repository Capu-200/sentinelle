# Data/

Ce dossier centralise **tous les datasets** du projet (bruts, externes, et préparés).

> Note : en production Cloud Run, ce dossier ne sera pas utilisé tel quel (filesystem éphémère).  
> Il sert au **développement local**, à l’entraînement, et à la traçabilité.

## Structure

- `raw/` : datasets bruts (non modifiés)
- `processed/` : datasets nettoyés / features tabulaires prêtes modèle
- `external/` : sources externes téléchargées (ex: PaySim zip/csv)

## Datasets actuels (dans `raw/`)

- **Supervisé (flaggé)** :
  - `raw/Dataset_flaged.csv`
- **Non flaggés** :
  - `raw/dataset_legit_no_status.csv` (transactions valides uniquement)
  - `raw/dataset_fraud_no_status.csv` (transactions “pas valides” uniquement)
  - `raw/dataset_mixed_no_status.csv` (mix)

## Schémas observés (résumé)

### `raw/Dataset_flaged.csv` (PaySim)

- **Colonnes** : `step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isFraud,isFlaggedFraud`
- **Label** : `isFraud` (0/1)

### `raw/dataset_*_no_status.csv` (format Payon)

- **Colonnes** : `transaction_id,created_at,provider_created_at,executed_at,provider,provider_tx_id,initiator_user_id,source_wallet_id,destination_wallet_id,amount,currency,transaction_type,direction,country,city,description,metadata.raw_payload`
- **Label** : aucun
- **Note** : `metadata.raw_payload` est un JSON sérialisé (string) qui peut contenir `is_vpn`, `source_device`, `risk_score`, etc.

## Convention de nommage (recommandée)

Créer un sous-dossier par dataset :

- `raw/paysim/`
- `raw/normal_only/` (dataset normal fourni)
- `processed/paysim_features_v1/`

Et ajouter un fichier de “carte d’identité” par dataset :

- `dataset_card.md` (ou `dataset_card.json`)

## “Dataset card” (template)

Copie/colle ce template dans `dataset_card.md` pour chaque dataset :

### Identité
- **name**:
- **source**:
- **owner**:
- **created_at**:
- **license**:

### Contenu
- **format**: (csv/parquet/json)
- **rows**:
- **columns**:
- **label**: (ex: fraud 0/1) ou “none”
- **time_field**: (ex: created_at)

### Qualité & limites
- **missing_values**:
- **known_biases**:
- **pii_risk**:

### Split temporel (si applicable)
- **train**:
- **val**:
- **test**:

### Mapping vers Payon (`Transaction`)
- **transaction_id**:
- **source_wallet_id**:
- **destination_wallet_id**:
- **amount**:
- **transaction_type**:
- **created_at**:

