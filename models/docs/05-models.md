# 05 — Modèles ML (supervisé + non supervisé)

## 2A — Supervisé (fraude 0/1)

### Dataset

- Source : PaySim (transactions + label fraude 0/1)
- Volume cible : > 1M transactions
- Split : **temporel** (pas aléatoire) via `created_at`/timestamp équivalent

### Modèle (choix v1 recommandé)

- **LightGBM** (gradient boosting tabulaire)
  - raisons : très bon sur tabulaire, inference rapide, support du déséquilibre via `class_weight`/`scale_pos_weight`

> Alternative acceptée : XGBoost (similaire).

### Gestion du déséquilibre (v1)

Comme la fraude est rare :

- utiliser `scale_pos_weight` (ou `class_weight`)
- optimiser une métrique robuste aux classes rares : **PR-AUC**
- choisir un **seuil** via un objectif “top-k bloqués” (voir `docs/06-scoring-thresholds.md`)

### Sortie

- `s_sup` ∈ \[0,1\] = probabilité estimée de fraude

## 2B — Non supervisé (anomalies)

### Dataset

- Entraîné sur un dataset contenant **majoritairement des transactions normales**
- Tu fourniras un dataset “normal-only” (ou filtré `fraud=0`)
- Volume cible : ≥ 300k transactions normales

### Modèle (choix v1 recommandé)

- **IsolationForest**
  - raisons : simple, rapide, efficace pour anomalies tabulaires, pas trop sensible à l’échelle si on stabilise les features (log_amount, etc.)

> Alternatives : OneClassSVM (souvent plus lent), LocalOutlierFactor (pratique mais plus complexe pour scorer en prod si pas “novelty mode”).

### Calibration vers \[0,1\]

Le score brut d’anomalie n’est pas une proba.  
Proposition v1 :

- convertir le score brut en quantile sur le train normal
- map quantile → `s_unsup` dans \[0,1\]

### Sortie

- `s_unsup` ∈ \[0,1\]

## Versioning & artefacts

- `model_version` : SemVer (ex: `v1.0.0`)
- Artefacts à versionner :
  - modèle supervisé
  - modèle non supervisé
  - pipeline features (encodage, normalisation)
  - config règles + seuils

