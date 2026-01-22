# 12 — Data preparation (cleaning + préparation entraînement)

## Pourquoi c’est nécessaire

Avant entraînement, on doit rendre la data :

- **cohérente** (mêmes types, mêmes catégories, valeurs manquantes gérées)
- **compatible** avec le contrat `Transaction` (ou avec un mapping explicite)
- **sans leakage** (ne pas apprendre à partir de signaux qui “trichent”, ex: `risk_score` déjà calculé)

## Pipeline recommandé (v1)

### Étape A — Ingestion & validation “raw”

Pour chaque CSV :

- lire en gardant le raw intact (pas d’édition de `Data/raw/*`)
- vérifier :
  - header attendu
  - colonnes obligatoires présentes
  - unicité de `transaction_id` (si présent)
  - `amount > 0`

### Étape B — Normalisation de schéma (Payon-format)

Pour les datasets `dataset_*_no_status.csv` :

- **timestamps** : parser `created_at`, `provider_created_at`, `executed_at`
  - si pas de timezone → hypothèse UTC (documenter)
- **direction** : mapper `IN/OUT` → `incoming/outgoing`
- **currency** :
  - v1 API = `PYC`, mais datasets = `EUR`
  - choix v1 recommandé : garder `currency` en catégorie et ne pas forcer `PYC` pendant l’entraînement
  - (si nécessaire) mapping contrôlé `EUR → PYC` uniquement dans un “mode démo”
- **metadata.raw_payload** :
  - parser la string JSON en objet
  - extraire seulement des champs autorisés (ex: `is_vpn`, `ip_version`, `source_device`)
  - **exclure** `risk_score` (leakage)
  - garder le raw en debug uniquement (et jamais en features si PII possible)

### Étape C — Déduplication & valeurs manquantes

- dédupliquer sur `transaction_id`
- gérer les champs manquants (ex: `executed_at`, `provider_tx_id`) :
  - ne pas dropper toute la ligne si le cœur est présent (`transaction_id`, wallets, amount, created_at)
  - créer des indicateurs booléens : `has_provider_tx_id`, `has_executed_at`

### Étape D — Features (tabulaire)

Créer deux niveaux :

1) **Features transactionnelles** (toujours dispo)
2) **Features comportementales** (agrégats historiques) — cf. `docs/04-feature-engineering.md`

Guideline :

- `log_amount = log(1 + amount)`
- encodage catégoriel : one-hot (simple) ou hashing (si beaucoup de pays/villes)
- pour l’unsupervised : scaler robuste (ex: robust scaler) sur numériques + log

### Étape E — Split temporel

- split par ordre de `created_at` (train/val/test)
- éviter tout leakage (features calculées uniquement à partir du passé)

## Spécifique PaySim (`Dataset_flaged.csv`)

PaySim ≠ schéma Payon.

Deux options :

### Option 1 (v1 simple) — Supervisé sur features “overlap”

N’utiliser que des features qui existent aussi (ou peuvent être reconstruites) côté Payon :

- `amount`, `type`, “direction” dérivée si possible, + historiques (velocity, nouveaux destinataires)

### Option 2 — Supervisé PaySim “full”

Utiliser aussi les balances (`oldbalanceOrg`, etc.) → meilleures perfs sur PaySim,
mais ces features ne sont pas dans l’API Payon : il faudra soit

- les ajouter au contrat, soit
- accepter un modèle non portable.

## Artefacts de sortie (recommandé)

Écrire dans `Data/processed/` :

- `paysim_clean.csv`
- `payon_legit_clean.csv`
- `payon_fraud_clean.csv`
- `payon_mixed_clean.csv`
- `payon_all_clean.csv`
- rapport : `Data/reports/cleaning_report.json`

## Script de cleaning (implémenté)

### Installation

```bash
python -m pip install -r requirements.txt
```

### Exécution

```bash
python scripts/clean_data.py
```

Par défaut, le script auto-détecte `Data/` (ou `data/`) et utilise :

- entrée : `Data/raw/*.csv`
- sortie : `Data/processed/*.csv`
- rapport : `Data/reports/cleaning_report.json`

## Checklist anti-leakage (v1)

- ne pas utiliser `metadata.*.risk_score` comme feature
- ne pas utiliser `executed_at` si la décision est “pré-exécution” (sinon fuite d’info future)
- ne pas utiliser `status`/`reason_code` si non disponibles au moment du scoring

