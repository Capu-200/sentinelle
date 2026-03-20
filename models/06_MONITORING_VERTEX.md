# Vertex AI Model Monitoring – Service Cloud Run (GCS)

Guide pour monitorer le modèle Payon servi sur **Cloud Run** avec **Vertex AI Model Monitoring v2**, en utilisant **Google Cloud Storage (GCS)** comme source de données.

> **Choix Payon** : les logs d’inférence et la baseline sont stockés dans **GCS** (bucket `sentinelle-485209-ml-data`). Vertex lit ces données pour le drift. BigQuery n’est pas utilisé dans cette setup.

---

## En résumé

Vertex ne lit pas directement les requêtes du service Cloud Run. Il faut :

1. **Exporter** les entrées/sorties du scoring vers **GCS** (JSONL).
2. **Enregistrer** le modèle dans le Model Registry (reference model).
3. **Créer un Model Monitor** : schéma (features + prédictions), baseline optionnelle (GCS), objectifs (drift), alertes.
4. **Lancer des jobs** : à la demande ou planifiés, en pointant la **target** vers le chemin GCS des inference logs.

L’API ML Engine écrit déjà les scores dans GCS si `MONITORING_GCS_BUCKET` est défini. Le reste se configure dans Vertex (console ou script Python).

---

## Config Payon (actuelle)

| Paramètre      | Valeur |
|----------------|--------|
| Projet         | `sentinelle-485209` |
| Région         | `europe-west1` |
| Bucket logs    | `sentinelle-485209-ml-data` |
| Préfixe logs   | `monitoring/inference_logs/` |
| Version modèle | `v1.0.0-test` (bucket ; Cloud Run utilise `latest`) |
| Email alertes  | `carel.clogenson@epitech.digital` |
| Baseline       | Optionnel : export via `EXPORT_BASELINE_GCS_BUCKET` → `gs://<bucket>/monitoring/baseline/v<VERSION>/train_features.jsonl` |

---

## Étape 1 – Exporter les données de scoring vers GCS

**Source de données utilisée dans Payon : GCS uniquement.**

L’API ML Engine écrit chaque score (ou un échantillon) dans des objets JSONL dans le bucket.

### Variables d’environnement (Cloud Run)

| Variable               | Description | Exemple |
|------------------------|-------------|---------|
| `MONITORING_GCS_BUCKET` | Bucket (obligatoire pour activer le logging) | `sentinelle-485209-ml-data` |
| `MONITORING_GCS_PREFIX` | Préfixe des objets (défaut) | `monitoring/inference_logs` |
| `MONITORING_SAMPLE_RATE` | Taux d’échantillonnage 0.0–1.0 (défaut 1.0) | `0.1` pour 10 % |

### Format écrit

- **Chemin** : `gs://<bucket>/<prefix>/YYYY/MM/DD/<uuid>.jsonl`
- **Contenu** : une ligne JSON par requête : `request_time`, features (mêmes noms que `feature_schema.json`), `risk_score`, `decision`, `model_version`.

Le déploiement Cloud Run (voir **04_DEPLOIEMENT.md**) peut inclure ces variables ; le script `deploy-ml-engine.sh` les définit déjà.

### Droits

Le compte de service Cloud Run doit pouvoir **écrire** dans le bucket (droits par défaut si le bucket est dans le même projet).

---

## Étape 2 – Enregistrer le modèle (reference model)

Pour un modèle servi **en dehors** de Vertex (dont Cloud Run), on enregistre un **reference model** : pas d’upload d’artefact, juste un nom dans le Model Registry.

- **APIs** : Vertex AI API activée sur le projet.
- **Script** : `scripts/vertex_setup_monitoring.py` fait l’enregistrement (voir plus bas).  
  Sinon, depuis la console : **Vertex AI → Model Registry** → créer un modèle « non déployé » et noter son resource name pour l’étape 4.

---

## Étape 3 – Schéma (features + prédictions)

Vertex a besoin du schéma des features et des sorties pour parser les JSONL sur GCS.

- **feature_fields** : noms et types (float, integer, categorical) déduits de `artifacts/v1.0.0-test/feature_schema.json`.
- **prediction_fields** : `risk_score` (float), `decision` (categorical).

Le script `vertex_setup_monitoring.py` construit ce schéma automatiquement à partir de `feature_schema.json`.

---

## Étape 4 – Créer le Model Monitor

Le Model Monitor associe à une version de modèle : schéma, baseline (optionnelle), objectifs (drift), notifications.

### Baseline (optionnelle)

Si tu exportes une baseline depuis l’entraînement :

- **Variable** : `EXPORT_BASELINE_GCS_BUCKET=sentinelle-485209-ml-data` lors de l’entraînement.
- **Chemin** : `gs://sentinelle-485209-ml-data/monitoring/baseline/v<VERSION>/train_features.jsonl`  
  (généré par `train.py` si `EXPORT_BASELINE_GCS_BUCKET` est défini).

Sinon, tu peux créer le Model Monitor sans baseline et ne pointer que la **target** (inference logs) lors des jobs « Run now ».

### Script Vertex : reference model + Model Monitor

Script : **`scripts/vertex_setup_monitoring.py`**

**Prérequis** : `python3 -m pip install --upgrade google-cloud-aiplatform`

**Exemple** :

```bash
cd models
export PROJECT_ID=sentinelle-485209 REGION=europe-west1
export ALERT_EMAIL=carel.clogenson@epitech.digital
# Optionnel si baseline déjà exportée
export BASELINE_GCS_URI=gs://sentinelle-485209-ml-data/monitoring/baseline/v1.0.0-test/train_features.jsonl

python3 scripts/vertex_setup_monitoring.py
```

**Arguments** : `--project`, `--region`, `--model-name`, `--schema` (chemin vers `feature_schema.json`), `--baseline-gcs`, `--alert-email`, `--model-resource` (si le modèle existe déjà dans le Registry).

---

## Étape 5 – Lancer des jobs de monitoring

- **À la demande** : console **Vertex AI → Model monitoring** → ouvrir le Model Monitor → **Run now** → choisir la **target** = `gs://sentinelle-485209-ml-data/monitoring/inference_logs/` (ou un sous-dossier contenant des JSONL). Baseline = chemin GCS de la baseline si configurée.
- **Planifié** : **Schedule a recurring run** → target = même chemin GCS ; pour les fenêtres temporelles, les fichiers doivent contenir un champ `request_time` (déjà le cas dans les logs Payon).

Les résultats (drift par feature, par prédiction, alertes) sont dans la console Monitoring et, si configuré, dans un bucket GCS de sortie.

---

## Récap des étapes (GCS uniquement)

| # | Action | Où / Comment |
|---|--------|--------------|
| 1 | Exporter entrées + sorties du scoring | API → GCS via `MONITORING_GCS_BUCKET` (un objet JSONL par requête ou par échantillon) |
| 2 | Enregistrer le modèle Payon | Vertex Model Registry en “reference model” (script ou console) |
| 3 | Définir le schéma | `feature_schema.json` + risk_score/decision (script ou manuel) |
| 4 | Créer le Model Monitor | Script `vertex_setup_monitoring.py` ou console : modèle, schéma, baseline GCS optionnelle, objectifs drift, notifications |
| 5 | Lancer les jobs | Run now ou Schedule, target = `gs://sentinelle-485209-ml-data/monitoring/inference_logs/` |

---

## Export baseline (entraînement)

Pour alimenter Vertex en baseline depuis l’entraînement :

- Définir **`EXPORT_BASELINE_GCS_BUCKET`** (ex. `sentinelle-485209-ml-data`) lors de l’exécution de `train.py` (local ou Cloud Run Job).
- Les features d’entraînement (Payon) sont exportées en JSONL vers :  
  `gs://<bucket>/monitoring/baseline/v<VERSION>/train_features.jsonl`

Exemple :

```bash
export EXPORT_BASELINE_GCS_BUCKET=sentinelle-485209-ml-data
./scripts/train-local.sh 1.0.0-test ...
```

---

## Où trouver le monitoring dans la console

**Vertex AI → Model monitoring**  
Lien direct (projet sentinelle-485209) :  
[Vertex AI – Model monitoring](https://console.cloud.google.com/vertex-ai/model-monitoring/model-monitors?project=sentinelle-485209)

Sur cette page : **Configure monitoring**, liste des Model Monitors, **Run now**, **Schedule a recurring run**, historique des Runs.

---

## Limites (modèles hors Vertex)

- **Feature attribution** (SHAP) : non supportée pour les reference models. Seuls **feature drift** et **prediction output drift** sont disponibles.
- **Source de données** : pas de “Vertex Endpoint Logging” pour Cloud Run. Payon utilise **GCS** uniquement pour les inference logs et la baseline.
- **Monitoring continu** avec fenêtres temporelles : supporté si les JSONL contiennent un champ **timestamp** (ex. `request_time`) ; c’est le cas dans les logs écrits par l’API.

---

## Évolution : Kafka, Grafana

- **Aujourd’hui** : l’API écrit directement dans GCS (`monitoring/inference_logs/`). Vertex lit ce chemin.
- **Avec Kafka** : un consumer peut écrire les events “scoring completed” dans le même bucket (même schéma de fichiers JSONL). Vertex et le Model Monitor restent inchangés, seule la source des fichiers change.
- **Grafana** : pour des dashboards métier (volumes, décisions, scores), tu peux soit interroger des exports agrégés, soit ajouter plus tard un sink BigQuery/Prometheus alimenté depuis Kafka ou depuis une lecture du bucket ; Vertex reste branché sur GCS pour le drift.

En résumé : **GCS comme pivot** pour Vertex, et **Kafka comme bus d’events** plus tard si besoin.
