# 📊 MLflow pour comparer les entraînements

> ✅ **Statut : Opérationnel**  
> **MLflow** sert à comparer les runs d'entraînement et à décider si une nouvelle version mérite un déploiement.  
> **Vertex AI** reste l'outil de monitoring de production (drift sur vraies inférences).

---

## 🎯 Objectif réel

Le besoin principal de MLflow dans ce projet est simple :

**répondre à la question "est-ce que la version `V+1` est meilleure que la version `V` avant déploiement ?"**

MLflow doit donc permettre de :
1. visualiser les métriques d'entraînement de chaque version
2. comparer facilement deux runs dans l'UI
3. retrouver les seuils et artefacts utilisés
4. décider rapidement si une version est candidate au déploiement

---

## ✅ Répartition des rôles

### MLflow = comparaison des entraînements

MLflow sert à comparer :
- les métriques de validation
- les paramètres d'entraînement
- les seuils finaux
- les artefacts associés à une version

### Vertex AI = monitoring en production

Vertex AI sert à surveiller :
- le drift des données d'entrée
- le drift des sorties du modèle
- le comportement du modèle sur les vraies transactions

### Règle simple

- **Avant déploiement** : regarder **MLflow**
- **Après déploiement** : regarder **Vertex AI**

---

## 🧭 Organisation recommandée

### Recommandation simple

Pour ton besoin, le plus simple est d'utiliser **un seul experiment MLflow principal** :

`/Shared/Sentinelle Production`

Pourquoi :
- toutes les versions candidates sont au même endroit
- la comparaison entre deux runs est plus simple
- l'usage est plus opérationnel

### Convention recommandée

- **1 run MLflow = 1 version entraînée**
- **1 run_name = `train-v<version>`**

Exemple :
- `train-v2.0.0`
- `train-v2.0.1-mlflow`

---

## 🔗 Flux cible

```text
Entraînement -> MLflow -> comparaison -> décision de déploiement
Déploiement -> Production -> Vertex AI -> drift en production
```

Concrètement :
1. entraîner une nouvelle version
2. logger automatiquement le run dans MLflow
3. comparer cette version à la précédente
4. décider si elle mérite le déploiement
5. une fois déployée, surveiller la prod avec Vertex

---

## 🗺️ Plan MLflow retenu

Le plan retenu pour ce projet est volontairement simple.

### Étape 1. Structurer les runs

Chaque run doit indiquer clairement :
- si c'est un run **complet** ou un run **de test**
- s'il est lancé en **local** ou en **cloud**
- quelle version il entraîne

### Étape 2. Rendre les runs comparables

Chaque run doit logger :
- les métriques de validation
- les tailles des datasets
- les périodes temporelles utilisées
- les seuils finaux
- les artefacts essentiels

### Étape 3. Comparer automatiquement au run précédent

Le code doit retrouver le run précédent exploitable dans le même experiment et calculer :
- l'écart de `val_pr_auc`
- l'écart de `val_f1`

### Étape 4. Produire une recommandation simple

Le run doit exposer une recommandation lisible dans MLflow, par exemple :
- `deploy_candidate_better_than_previous`
- `keep_previous_version`
- `manual_review_mixed_metrics`
- `do_not_deploy_test_run`

---

## ✅ Ce que le code log déjà dans MLflow

Le script `models/scripts/train.py` log déjà les éléments suivants.

### Paramètres

| Paramètre | Description |
|----------|-------------|
| `version` | version entraînée |
| `local` | entraînement local ou non |
| `data_dir` | dossier de données |
| `config_dir` | dossier de configuration |
| `artifacts_dir` | dossier de sortie des artefacts |
| `test_size` | présent seulement en mode test |
| `paysim_*_period_*` | périodes temporelles PaySim |
| `payon_*_period_*` | périodes temporelles Payon |

### Métriques

| Métrique | Description |
|----------|-------------|
| `val_accuracy` | accuracy sur validation |
| `val_f1` | F1-score sur validation |
| `val_pr_auc` | PR-AUC sur validation |
| `block_threshold` | seuil final BLOCK |
| `review_threshold` | seuil final REVIEW |
| `paysim_train_rows` | volume train PaySim |
| `paysim_val_rows` | volume val PaySim |
| `paysim_test_rows` | volume test PaySim |
| `payon_train_rows` | volume train Payon |
| `payon_val_rows` | volume val Payon |
| `payon_test_rows` | volume test Payon |
| `paysim_train_fraud_rate` | taux de fraude train |
| `paysim_val_fraud_rate` | taux de fraude val |
| `paysim_test_fraud_rate` | taux de fraude test |
| `feature_count` | nombre de features finales |
| `threshold_gap` | écart entre seuil BLOCK et REVIEW |
| `previous_val_pr_auc` | PR-AUC du run précédent comparable |
| `previous_val_f1` | F1 du run précédent comparable |
| `delta_val_pr_auc` | delta PR-AUC vs run précédent |
| `delta_val_f1` | delta F1 vs run précédent |

### Tags

| Tag | Description |
|-----|-------------|
| `run_type` | `full` ou `test` |
| `training_mode` | `local` ou `cloud` |
| `dataset` | dataset logique utilisé |
| `model_family` | type de pipeline entraîné |
| `compare_ready` | run exploitable pour comparaison ou non |
| `artifacts_present` | artefacts essentiels présents |
| `thresholds_ok` | seuils cohérents ou non |
| `candidate_for_deploy` | `true` / `false` |
| `deployment_recommendation` | recommandation finale |
| `compared_to_run_id` | run précédent utilisé comme baseline |
| `compared_to_version` | version précédente comparée |

### Artefacts

| Artefact | Description |
|----------|-------------|
| `feature_schema.json` | schéma des features |
| `thresholds.json` | seuils finaux |
| `baseline_train.jsonl` | baseline training exportée pour comparaison / Vertex |

---

## 📌 Ce qu'il faut regarder dans MLflow

Si ton objectif est de **choisir la meilleure version**, alors regarde en priorité :

1. **`val_pr_auc`**
   - métrique la plus utile si le dataset est déséquilibré
   - c'est la métrique principale à utiliser pour arbitrer

2. **`val_f1`**
   - utile pour voir l'équilibre précision / rappel
   - bonne métrique secondaire de décision

3. **`val_accuracy`**
   - à regarder, mais moins décisive si la fraude est rare

4. **`block_threshold` et `review_threshold`**
   - permettent de voir si la calibration finale reste cohérente
   - utile pour vérifier qu'une version n'introduit pas des seuils absurdes

5. **les artefacts**
   - pour vérifier que le run a bien produit un `feature_schema.json`, `thresholds.json` et une baseline

6. **`deployment_recommendation`**
   - c'est le résumé le plus rapide à lire
   - il permet de savoir si le run semble meilleur, moins bon ou ambigu

7. **`candidate_for_deploy`**
   - utile pour filtrer rapidement les runs intéressants

---

## ✅ Règle de décision simple avant déploiement

Voici une règle opérationnelle simple.

Une nouvelle version `V+1` mérite d'être déployée si :

1. `val_pr_auc` est meilleure ou au moins aussi bonne que la version précédente
2. `val_f1` ne se dégrade pas de manière significative
3. les seuils `block_threshold` / `review_threshold` restent cohérents
4. les artefacts sont bien présents
5. le run n'est pas un run de test réduit (`test_size`) si l'objectif est un vrai déploiement

### En pratique

**On privilégie `val_pr_auc` puis `val_f1`.**

Si une nouvelle version a :
- une meilleure `val_pr_auc`
- un `val_f1` stable ou meilleur
- des seuils cohérents

alors elle devient une **candidate au déploiement**.

### Traduction dans le code

La logique actuelle dans `train.py` est :

- si le run est un `test` -> `do_not_deploy_test_run`
- si les artefacts ou seuils sont incohérents -> `do_not_deploy_incomplete_run`
- si aucun run précédent comparable n'existe -> `manual_review_no_previous_baseline`
- si `val_pr_auc` et `val_f1` sont meilleurs que le run précédent -> `deploy_candidate_better_than_previous`
- si les deux sont moins bons -> `keep_previous_version`
- sinon -> `manual_review_mixed_metrics`

---

## 🚫 Ce qu'il ne faut pas comparer directement

Pour éviter de mauvaises conclusions, ne compare pas dans la même décision :

- un run complet vs un run `test_size`
- un run de dev local rapide vs un run de prod complet
- un run incomplet sans artefacts

### Règle simple

Pour décider un déploiement, compare seulement :
- des runs complets
- avec le même type de données
- sur une logique d'entraînement comparable

---

## 🧪 Comment lancer un entraînement avec MLflow

### Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| `MLFLOW_TRACKING_URI` | backend MLflow | `databricks` |
| `DATABRICKS_HOST` | host Databricks | `https://dbc-576fb506-d185.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | token d'accès | secret |
| `MLFLOW_EXPERIMENT_NAME` | experiment principal | `/Shared/Sentinelle Production` |

### Exemple local

```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"

export MLFLOW_TRACKING_URI="databricks"
export DATABRICKS_HOST="https://dbc-576fb506-d185.cloud.databricks.com"
export DATABRICKS_TOKEN="<TOKEN>"
export MLFLOW_EXPERIMENT_NAME="/Shared/Sentinelle Production"

python3 scripts/train.py \
  --version "2.0.2-mlflow" \
  --local
```

### Exemple mode test rapide

À ne pas utiliser pour une décision de déploiement finale :

```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"

export MLFLOW_TRACKING_URI="databricks"
export DATABRICKS_HOST="https://dbc-576fb506-d185.cloud.databricks.com"
export DATABRICKS_TOKEN="<TOKEN>"
export MLFLOW_EXPERIMENT_NAME="/Shared/Sentinelle Production"

python3 scripts/train.py \
  --version "2.0.2-mlflow" \
  --local \
  --test-size 10000
```

---

## 🖥️ Comment comparer deux runs dans MLflow

### Ce que tu fais dans l'interface

1. Ouvrir l'experiment `/Shared/Sentinelle Production`
2. Repérer les runs `train-v<version>`
3. Cocher les 2 runs que tu veux comparer
4. Cliquer sur **Compare**

### Ce que tu lis en priorité

1. `val_pr_auc`
2. `val_f1`
3. `val_accuracy`
4. `block_threshold`
5. `review_threshold`
6. présence des artefacts

### Décision

À la fin, tu dois pouvoir répondre à :

**"Est-ce que `train-vX` est meilleur que `train-vY` pour justifier un déploiement ?"**

---

## ✅ Run MLflow "propre" attendu

Un run prêt à être comparé / utilisé doit contenir :

- un nom clair : `train-v<version>`
- les paramètres de contexte (`version`, `local`, `data_dir`, `config_dir`, `artifacts_dir`)
- les métriques de validation
- les métriques de contexte dataset
- les seuils finaux
- les artefacts essentiels
- une recommandation de déploiement lisible

### Minimum acceptable

- `val_pr_auc`
- `val_f1`
- `block_threshold`
- `review_threshold`
- `feature_schema.json`
- `thresholds.json`
- `deployment_recommendation`
- `candidate_for_deploy`

---

## ⚠️ Limites actuelles

Le logging MLflow est déjà utile, mais reste centré sur la décision opérationnelle simple.

Aujourd'hui, le code log :
- les métriques de validation supervisée
- les seuils finaux
- les artefacts essentiels

Il ne log pas encore explicitement :
- des métriques dédiées au modèle non supervisé
- des tags métier plus riches comme `reviewed_by` ou `deployment_decision_owner`
- une comparaison automatique à une "version de référence métier" choisie manuellement

Ce n'est pas bloquant pour commencer à comparer des versions.

---

## 📋 Checklist opérationnelle

### Avant déploiement

- [x] MLflow activé dans `train.py`
- [x] run visible dans MLflow
- [x] métriques principales visibles
- [x] artefacts visibles
- [ ] comparaison de 2 versions faite dans l'UI
- [ ] décision explicite prise : garder l'ancienne version ou déployer la nouvelle

### Après déploiement

- [ ] vérifier `/health`
- [ ] vérifier que la bonne version tourne en prod
- [ ] surveiller le drift dans Vertex AI

---

## 📚 Références

| Document | Contenu |
|----------|---------|
| [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md) | entraînement local et cloud |
| [04_DEPLOIEMENT.md](04_DEPLOIEMENT.md) | déploiement ML Engine |
| [06_MONITORING_VERTEX.md](06_MONITORING_VERTEX.md) | monitoring Vertex AI |
| [08_MONITORING_VERTEX_RUN_AFTER_DEPLOY.md](08_MONITORING_VERTEX_RUN_AFTER_DEPLOY.md) | run Vertex après déploiement |

---

## 🧠 Résumé simple

- **MLflow** sert à choisir une version avant déploiement
- **Vertex AI** sert à surveiller le comportement du modèle après déploiement
- pour ton besoin, la question MLflow est :
  - **"est-ce que cette version est meilleure que la précédente ?"**
- la réponse doit se baser surtout sur :
  - `val_pr_auc`
  - `val_f1`
  - les seuils
  - les artefacts

---

**Version** : 2.0  
**Dernière mise à jour** : Mars 2026  
**Statut** : MLflow opérationnel pour comparer les entraînements
