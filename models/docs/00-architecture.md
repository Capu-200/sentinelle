# 00 — Architecture du projet ML

## Vue d'ensemble

Ce document décrit l'architecture et la structure des fichiers du moteur de scoring de fraude bancaire Payon.

## Structure du projet

```
models/
├── src/                          # Code source principal
│   ├── data/                     # Nettoyage et préparation des données
│   ├── features/                 # Feature engineering
│   ├── rules/                    # Règles métier (R1-R4)
│   ├── models/                   # Modèles ML (supervisé + non supervisé)
│   ├── scoring/                  # Scoring global et décision
│   └── utils/                    # Utilitaires (config, versioning)
│
├── configs/                      # Configurations centralisées
│   ├── model_config.yaml         # Configuration des modèles
│   ├── scoring_config.yaml       # Poids et seuils de scoring
│   └── feature_config.yaml       # Configuration des features
│
├── artifacts/                     # Modèles et artefacts versionnés
│   ├── v1.0.0/                   # Version 1.0.0
│   └── latest -> v1.0.0/         # Symlink vers la dernière version
│
├── scripts/                      # Scripts d'entraînement et évaluation
│   ├── train.py                  # Pipeline d'entraînement complet
│   ├── evaluate.py              # Évaluation des modèles
│   ├── clean_data.py             # Nettoyage des données (autonome)
│   ├── push_transaction.py       # Ajouter une transaction à l'historique
│   └── score_transaction.py      # Scorer une transaction (pipeline complet)
│
├── tests/                        # Tests unitaires et d'intégration
│   └── fixtures/                 # Données de test
│
├── Data/                         # Données (raw, processed, reports)
├── docs/                         # Documentation
└── schemas/                      # Schémas JSON (transaction, decision)
```

## Modules principaux

### 1. `src/data/` — Nettoyage et préparation

**Responsabilité** : Préparation des données pour l'entraînement et l'inference.

- `cleaning.py` : Logique de nettoyage réutilisable (normalisation, parsing, anti-leakage)
- `preparation.py` : Pipeline de préparation pour l'entraînement (split temporel, validation)
- `historique_store.py` : Stockage et récupération de l'historique des transactions (phase dev - fichier local)

**Utilisé par** :
- Scripts d'entraînement (`scripts/train.py`)
- Pipeline de feature engineering
- Scripts de scoring (`scripts/score_transaction.py`)

### 2. `src/features/` — Feature Engineering

**Responsabilité** : Extraction et calcul des features pour chaque transaction.

- `extractor.py` : Extraction de features transactionnelles (amount, direction, timestamps, etc.)
- `aggregator.py` : Calcul des agrégats historiques (fenêtres temporelles, profils comportementaux)
- `pipeline.py` : Pipeline complet de feature engineering (orchestration)
- `schemas/v1.json` : Schéma versionné des features (liste et types)

**Utilisé par** :
- Entraînement des modèles
- Inference (scoring en temps réel)

**Contraintes** :
- Latence < 300ms pour l'inference
- Features versionnées (schémas JSON)

### 3. `src/rules/` — Règles métier

**Responsabilité** : Application des règles métier déterministes (R1-R4).

- `engine.py` : Moteur de règles (évaluation de toutes les règles)
- `config/rules_v1.yaml` : Configuration des règles (conditions, actions, contributions)

**Règles** :
- R1 : KYC light (montant max)
- R2 : Pays interdit/sanctionné
- R3 : Vélocité anormale
- R4 : Nouveau destinataire + montant inhabituel

**Sortie** :
- `rule_score` ∈ [0,1]
- `reasons` : liste d'identifiants de règles déclenchées
- `hard_block` : booléen (force BLOCK)
- `decision` : `ALLOW`, `BOOST_SCORE`, ou `BLOCK`
- `boost_factor` : facteur de boost à appliquer au score final (défaut: 1.0)

### 4. `src/models/` — Modèles ML

**Responsabilité** : Entraînement et prédiction des modèles ML.

#### 4.1. `supervised/` — Modèle supervisé

- `train.py` : Entraînement LightGBM (dataset PaySim avec label fraude)
- `predictor.py` : Prédiction (probabilité de fraude)

**Modèle** : LightGBM (gradient boosting tabulaire)
**Métrique** : PR-AUC
**Gestion déséquilibre** : `scale_pos_weight`

#### 4.2. `unsupervised/` — Modèle non supervisé

- `train.py` : Entraînement IsolationForest (dataset normal-only)
- `predictor.py` : Prédiction (score d'anomalie calibré [0,1])

**Modèle** : IsolationForest
**Calibration** : Quantile mapping vers [0,1]

**Base commune** :
- `base.py` : Classe de base pour les modèles (interface commune)

### 5. `src/scoring/` — Scoring global et décision

**Responsabilité** : Combinaison des signaux et prise de décision finale.

- `scorer.py` : Calcul du score global
  - Formule : `risk_score = (0.2 × rule_score + 0.6 × s_sup + 0.2 × s_unsup) × boost_factor`
  - Poids configurables via `configs/scoring_config.yaml`
  - `boost_factor` transmis depuis les règles métier
- `decision.py` : Logique de décision (BLOCK/REVIEW/APPROVE)
  - Seuils configurables (top 0.1% BLOCK, top 1% REVIEW)
  - Gestion des hard blocks (règles R1/R2)

**Sortie finale** :
```json
{
  "risk_score": 0.83,
  "decision": "BLOCK",
  "reasons": ["amount_over_kyc_limit", "sanctioned_country"],
  "model_version": "v1.0.0"
}
```

### 6. `src/utils/` — Utilitaires

**Responsabilité** : Fonctions utilitaires partagées.

- `config.py` : Chargement et gestion des configurations (YAML/JSON)
- `versioning.py` : Gestion du versioning des modèles et features

## Configuration

### `configs/model_config.yaml`

Configuration des modèles ML :
- Hyperparamètres LightGBM
- Hyperparamètres IsolationForest
- Paramètres de calibration

### `configs/scoring_config.yaml`

Configuration du scoring :
- Poids de la formule globale (rule_score, s_sup, s_unsup)
- Seuils de décision (BLOCK, REVIEW)
- Politique de hard blocks

### `configs/feature_config.yaml`

Configuration des features :
- Fenêtres temporelles (5m, 1h, 24h, 7d, 30d)
- Clés d'agrégation (source_wallet_id, destination_wallet_id, etc.)
- Liste des features à calculer

## Versioning

### Structure des artefacts

Chaque version de modèle est stockée dans `artifacts/v<MAJOR>.<MINOR>.<PATCH>/` :

```
artifacts/v1.0.0/
├── supervised_model.pkl          # Modèle LightGBM entraîné
├── unsupervised_model.pkl        # Modèle IsolationForest entraîné
├── feature_pipeline.pkl          # Pipeline de features sauvegardé
├── feature_schema.json           # Schéma des features utilisé
└── thresholds.json               # Seuils calculés (BLOCK/REVIEW)
```

### Symlink `latest`

Un symlink `artifacts/latest` pointe vers la dernière version pour faciliter l'accès.

### Versioning des features

Les schémas de features sont versionnés dans `src/features/schemas/v1.json` (et futures versions v2.json, etc.).

## Flux d'entraînement

1. **Nettoyage** : `scripts/clean_data.py` → `Data/processed/*.csv`
2. **Préparation** : `src/data/preparation.py` → Split temporel, validation
3. **Feature Engineering** : `src/features/pipeline.py` → Features pour entraînement
4. **Entraînement supervisé** : `src/models/supervised/train.py` → Modèle LightGBM
5. **Entraînement non supervisé** : `src/models/unsupervised/train.py` → Modèle IsolationForest
6. **Calibration des seuils** : `scripts/evaluate.py` → Calcul des seuils BLOCK/REVIEW
7. **Sauvegarde** : Tous les artefacts → `artifacts/v1.0.0/`

**Script principal** : `scripts/train.py` (orchestre tout le pipeline)

## Flux d'inference (scoring)

1. **Transaction en entrée** : JSON conforme à `schemas/transaction.schema.json`
2. **Récupération historique** : `src/data/historique_store.py` → Historique des transactions
3. **Feature Engineering** : `src/features/pipeline.py` → Features enrichies (avec historique)
4. **Règles métier** : `src/rules/engine.py` → `rule_score` + `reasons` + `boost_factor` + `decision`
   - Si `decision = BLOCK` → arrêt immédiat, pas de passage par l'IA
   - Si `decision = BOOST_SCORE` → `boost_factor > 1.0` appliqué au score final
   - Si `decision = ALLOW` → passage normal à l'IA
5. **Scoring supervisé** : `src/models/supervised/predictor.py` → `s_sup` (si pas BLOCK)
6. **Scoring non supervisé** : `src/models/unsupervised/predictor.py` → `s_unsup` (si pas BLOCK)
7. **Score global** : `src/scoring/scorer.py` → `risk_score = (formule) × boost_factor`
8. **Décision** : `src/scoring/decision.py` → `decision` (BLOCK/REVIEW/APPROVE)
9. **Sortie** : JSON conforme à `schemas/decision.schema.json`

**Script principal** : `scripts/score_transaction.py` (orchestre tout le pipeline)

**Contrainte** : Latence < 300ms (p95)

### Stockage d'historique (phase dev)

Pour la phase de développement, l'historique est stocké dans `Data/historique.json` :
- **Ajouter une transaction** : `python scripts/push_transaction.py <transaction.json>`
- **Scorer une transaction** : `python scripts/score_transaction.py <transaction.json> --save`
- L'historique est utilisé pour calculer les features comportementales et certaines règles

## Tests

Structure dans `tests/` :
- `test_features.py` : Tests du feature engineering
- `test_rules.py` : Tests des règles métier
- `test_models.py` : Tests des modèles ML
- `test_scoring.py` : Tests du scoring global
- `fixtures/` : Données de test (transactions, historique, etc.)

## Principes de conception

### Simplicité
- Structure claire et modulaire
- Code facile à comprendre et maintenir
- Configuration externalisée (pas de hardcoding)

### Maintenabilité
- Séparation des responsabilités
- Modules indépendants et testables
- Documentation inline

### Performance
- Optimisé pour l'inference rapide (< 300ms)
- Modèles légers (tabulaire, pas de DL)
- Cache des agrégats historiques si possible

### Versioning
- Tous les artefacts versionnés ensemble
- Schémas de features versionnés
- Configuration versionnée avec les modèles

### Collaboration
- Modules indépendants (facile de travailler en parallèle)
- Interfaces claires entre modules
- Tests pour garantir la cohérence

## Dépendances entre modules

```
scripts/train.py
  └─> src/data/preparation.py
  └─> src/features/pipeline.py
  └─> src/models/supervised/train.py
  └─> src/models/unsupervised/train.py
  └─> scripts/evaluate.py

Inference (scoring)
  └─> src/features/pipeline.py
  └─> src/rules/engine.py
  └─> src/models/supervised/predictor.py
  └─> src/models/unsupervised/predictor.py
  └─> src/scoring/scorer.py
  └─> src/scoring/decision.py
```

## Évolutions futures

- **API** : Ajout d'une couche API (FastAPI) dans `src/api/` pour Cloud Run
- **Feature Store** : Intégration d'un feature store pour les agrégats historiques
- **Monitoring** : Ajout de métriques et monitoring (latence, précision, drift)
- **A/B Testing** : Support de plusieurs versions de modèles en parallèle
