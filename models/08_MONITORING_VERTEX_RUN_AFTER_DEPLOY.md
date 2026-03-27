# Vertex AI Model Monitoring - Run apres chaque nouveau deploiement

Objectif : a chaque nouvelle version de modele deployee sur le ML Engine (Cloud Run), lancer un **Model Monitoring** (drift input/output) sur Vertex AI en se basant sur :
- **Target data** : logs d'inference exportes en BigQuery (approche la plus simple et stable pour Vertex)
- **Baseline** : baseline exportee depuis l'entrainement et chargee dans GCS (baseline "Training")

Ce document couvre maintenant :
- le **flux recommande automatise** (une commande principale)
- les **verifications Google Cloud** a faire apres execution
- le **fallback manuel** si tu veux rejouer une etape a la main

---

## Etat actuel du projet : automatique vs manuel

### Ce qui est deja automatise / developpe

1. **Ecriture des logs d'inference dans GCS**
   - Le ML Engine ecrit automatiquement un fichier JSONL par inference dans :
     `gs://sentinelle-485209-ml-data/monitoring/inference_logs/YYYY/MM/DD/`
   - Condition : les variables Cloud Run de monitoring sont bien definies (`MONITORING_GCS_BUCKET`, `MONITORING_SAMPLE_RATE`, etc.).

2. **Export de la baseline d'entrainement**
   - La baseline peut etre produite depuis l'entrainement puis poussee vers :
     `gs://sentinelle-485209-ml-data/monitoring/baseline/v<V>/train_features.jsonl`

3. **Creation du Model Monitor Vertex**
   - Le script `scripts/vertex_setup_monitoring.py` automatise :
     - la creation / reutilisation du reference model
     - la construction du schema de monitoring
     - la creation / reutilisation du `ModelMonitor`

4. **Run Vertex apres deploiement**
   - Le script `scripts/run-vertex-monitoring-after-deploy.py` automatise :
     - la verification / upload de la baseline en GCS
     - la creation / reutilisation du `ModelMonitor`
     - le lancement du `ModelMonitoringJob`

5. **Visualisation simple des logs**
   - Le script `scripts/inference_logs_dashboard.py` permet de visualiser rapidement les logs d'inference presents dans GCS.

### Ce qui reste manuel aujourd'hui

1. **Avoir du trafic d'inference**
   - En prod normale, ce sont les vraies transactions qui alimentent les logs.
   - Le trafic de test ne doit servir qu'a la validation technique.

2. **Lire et interpreter le run Vertex**
   - Les resultats du monitoring (drift) sont a analyser manuellement dans Vertex AI.

### Conclusion pratique

Aujourd'hui, le flux recommande est **largement automatise** :
- **automatique via script** : health check, lecture GCS, normalisation des types, chargement BigQuery, creation de la vue, verification GO/NO-GO, lancement du run Vertex
- **optionnel** : smoke test `/score` post-deploiement
- **manuel** : interpretation du drift et decision metier

---

## Hypotheses / conventions de nommage

1. Version de modele (exemple) : `V = 2.0.1-mlflow`
2. Bucket logs :
   - `B = gs://sentinelle-485209-ml-data`
3. Prefix logs inference ecrits par l'API :
   - `monitoring/inference_logs/`
4. Baseline export en GCS :
   - `gs://sentinelle-485209-ml-data/monitoring/baseline/v<V>/train_features.jsonl`
5. Logs inference charges en BigQuery (exemple de table deja creee) :
   - dataset : `sentinelle-485209`
   - table : `inference_logs_YYYY_MM_DD.inference_logs_YYYY_MM_DD`
6. Colonne timestamp utilisee par Vertex :
   - `request_time`

---

## Flux recommande : une commande principale

Le script recommande est :
`models/scripts/run-monitoring-pipeline-after-deploy.py`

Il automatise, dans cet ordre :
1. verification de `/health`
2. lecture des logs d'inference dans GCS
3. normalisation des booleens en `0/1` pour stabiliser le schema BigQuery
4. chargement dans `ml_monitoring.inference_logs_v2`
5. creation / refresh de `ml_monitoring.inference_logs_last_24h`
6. verification `COUNT + min/max(request_time)`
7. lancement du run Vertex via `run-vertex-monitoring-after-deploy.py`
8. reutilisation par defaut du `reference model` et du `ModelMonitor` existants si leurs noms existent deja

En option, tu peux ajouter un **smoke test post-deploiement** avec `--generate-test-traffic N`.

### Dependances Python

Si besoin :
```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"
python3 -m pip install -r requirements.txt
```

### Commande recommandee (prod normale, sans trafic de test)

```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"

python3 scripts/run-monitoring-pipeline-after-deploy.py \
  --version "2.0.1-mlflow" \
  --project "sentinelle-485209" \
  --region "europe-west1" \
  --bucket "sentinelle-485209-ml-data" \
  --days-back 2 \
  --min-rows 100 \
  --window "24h" \
  --alert-email "carel.clogenson@epitech.digital"
```

### Variante smoke test (validation technique)

Si tu veux valider le pipeline juste apres deploiement :

```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"

python3 scripts/run-monitoring-pipeline-after-deploy.py \
  --version "2.0.1-mlflow" \
  --project "sentinelle-485209" \
  --region "europe-west1" \
  --bucket "sentinelle-485209-ml-data" \
  --generate-test-traffic 30 \
  --days-back 2 \
  --min-rows 20 \
  --window "24h" \
  --alert-email "carel.clogenson@epitech.digital"
```

### Variante preparation uniquement (sans lancer Vertex)

Utile pour verifier BigQuery avant le run :

```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"

python3 scripts/run-monitoring-pipeline-after-deploy.py \
  --version "2.0.1-mlflow" \
  --project "sentinelle-485209" \
  --region "europe-west1" \
  --bucket "sentinelle-485209-ml-data" \
  --days-back 2 \
  --min-rows 100 \
  --window "24h" \
  --skip-vertex-run
```

### Comportement par defaut sur Vertex

Par defaut, le pipeline :
- **reutilise** le `reference model` Vertex le plus recent ayant le display name `sentinelle-ml-engine-reference`
- **reutilise** le `ModelMonitor` le plus recent ayant le display name `sentinelle-ml-engine-v2-monitor-<V>`

Donc :
- si tu relances plusieurs fois pour la meme version `V`, tu n'empiles plus un nouveau monitor a chaque tentative
- tu crees surtout de nouveaux **jobs de monitoring**, ce qui est le comportement souhaite

### Forcer une recreation Vertex (cas exceptionnel)

Seulement si tu veux repartir sur de nouvelles ressources Vertex :

```bash
python3 scripts/run-monitoring-pipeline-after-deploy.py \
  --version "2.0.1-mlflow" \
  --project "sentinelle-485209" \
  --region "europe-west1" \
  --bucket "sentinelle-485209-ml-data" \
  --days-back 2 \
  --min-rows 100 \
  --window "24h" \
  --no-reuse-existing-reference-model \
  --no-reuse-existing-model-monitor
```

---

## A. Pre-requis (a faire seulement quand tu deployes une nouvelle version V)

### A1) Assurer la baseline de la nouvelle version
Depuis le resultat d'entrainement de la nouvelle version :
1. Verifier que tu as le fichier local :
   - `models/artifacts/v<V>/baseline_train.jsonl`
2. Uploader vers GCS :
   - Destination :
     `gs://sentinelle-485209-ml-data/monitoring/baseline/v<V>/train_features.jsonl`

Commande (a adapter a V) :
```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"
gsutil -q cp "artifacts/v<V>/baseline_train.jsonl" \
  "gs://sentinelle-485209-ml-data/monitoring/baseline/v<V>/train_features.jsonl"
```

### A2) Creer/mettre a jour le Model Monitor (baseline associee)
On garde un `ModelMonitor` par version de modele quand c'est possible, puis on le reutilise pour les runs suivants de cette meme version.

1. Utiliser le schema de features de la version V :
   - `models/artifacts/v<V>/feature_schema.json`
2. Lancer le script de setup :
```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"
export PROJECT_ID=sentinelle-485209
export REGION=europe-west1
export ALERT_EMAIL=carel.clogenson@epitech.digital

python3 scripts/vertex_setup_monitoring.py \
  --schema "artifacts/v<V>/feature_schema.json" \
  --model-name "sentinelle-ml-engine-v2" \
  --baseline-gcs "gs://sentinelle-485209-ml-data/monitoring/baseline/v<V>/train_features.jsonl"
```

Note : le script affiche un **lien console** vers le `ModelMonitor` cree.

---

## Ordre operationnel recommande

### 0) Une seule fois (setup)

1. Verifier que le ML Engine ecrit bien dans GCS
   - **Automatique cote code**
   - **Verification manuelle** : verifier les variables Cloud Run et la presence des fichiers JSONL dans GCS

2. Creer la table BigQuery cible
   - **Manuel**
   - Objectif : disposer d'une table stable de destination pour les logs d'inference

3. Creer la vue :
   - `sentinelle-485209.ml_monitoring.inference_logs_last_24h`
   - **Manuel**

4. Verifier que le script `run-vertex-monitoring-after-deploy.py` pointe vers cette vue
   - **Deja developpe / automatise dans le repo**
   - **Verification manuelle** recommandee lors du setup initial

5. Installer les dependances Python
   - **Manuel une seule fois**
   - `python3 -m pip install -r requirements.txt`

### 1) A chaque nouveau deploiement de modele V

1. Deployer le modele en prod
   - **Manuel**

2. Verifier `/health`
   - **Automatise par `run-monitoring-pipeline-after-deploy.py`**
   - Peut aussi etre verifie manuellement
   - Objectif : confirmer le bon `model_version`

3. Avoir du trafic `/score`
   - **Normalement** : trafic reel de production
   - **Optionnel** : smoke test si tu passes `--generate-test-traffic N`
   - Objectif : produire de nouveaux logs d'inference

4. Verifier l'arrivee des fichiers dans GCS
   - **Automatique cote application**
   - **Verification implicite dans le script** via lecture des blobs GCS
   - Peut aussi etre verifie manuellement

5. Charger les logs dans BigQuery
   - **Automatise par `run-monitoring-pipeline-after-deploy.py`**
   - Normalisation des types incluse

6. Verifier la vue 24h (`COUNT + min/max(request_time)`)
   - **Automatise par `run-monitoring-pipeline-after-deploy.py`**
   - Peut aussi etre verifie manuellement dans BigQuery

### 2) Go / No-Go avant run Vertex

1. `COUNT > 0` dans `inference_logs_last_24h`
   - **GO**
   - Le script peut imposer un seuil plus fort via `--min-rows`

2. `COUNT = 0`
   - **STOP**
   - Corriger ingestion / schema / vue BigQuery

3. Schema incoherent (bool / int / string)
   - **STOP**
   - Normaliser puis recharger dans BigQuery

### 3) Lancer le run Vertex

1. Executer `run-monitoring-pipeline-after-deploy.py`
   - **Automatise par script**
   - Le script appelle ensuite `run-vertex-monitoring-after-deploy.py`

2. Attendre `Succeeded`
   - **Verification manuelle**

3. Lire :
   - `Input feature drift`
   - `Output inference drift`
   - **Manuel**

### 4) Apres le run

1. Si drift faible
   - Continuer monitoring

2. Si drift significatif
   - Analyser les features en cause
   - Decider retrain / ajustements / investigation data

3. Archiver le resultat
   - date
   - version de modele
   - volume de data utilise
   - conclusion
   - **Manuel**

---

## A-Ul (option) : scripts disponibles

### Script principal recommande

`models/scripts/run-monitoring-pipeline-after-deploy.py`

Utiliser ce script si tu veux automatiser au maximum :
1. `/health`
2. smoke test optionnel
3. GCS -> BigQuery
4. normalisation des types
5. refresh de la vue 24h
6. GO / NO-GO sur le volume
7. lancement du run Vertex

### Script secondaire (fallback)

`models/scripts/run-vertex-monitoring-after-deploy.py`

Utiliser ce script seulement si :
- ta table / vue BigQuery est deja prete
- tu veux relancer uniquement la partie Vertex
- tu veux reutiliser directement un `ModelMonitor` / `reference model` deja existants

Commande :
```bash
cd "/Users/kclo/Documents/2025/SCHOOL PROJECT/sentinelle/models"

python3 scripts/run-vertex-monitoring-after-deploy.py \
  --version "<V>" \
  --target-bq-table-uri "bq://sentinelle-485209.ml_monitoring.inference_logs_last_24h" \
  --project "sentinelle-485209" \
  --region "europe-west1" \
  --bucket "sentinelle-485209-ml-data" \
  --timestamp-field "request_time" \
  --window "24h" \
  --alert-email "carel.clogenson@epitech.digital"
```

Comportement :
- reutilise par defaut le `reference model` et le `ModelMonitor` existants si le display name correspond
- cree une nouvelle ressource seulement si rien n'existe encore
- pour forcer une recreation, ajouter :
  - `--no-reuse-existing-reference-model`
  - `--no-reuse-existing-model-monitor`

---

## B. Run now dans Vertex AI (a faire a chaque nouvelle version deployee)

### B1) Aller sur le Model Monitor correct
1. Ouvrir le lien du `ModelMonitor` cree/choisi pour la version V
2. Cliquer **Run now**

### B2) Parametres "Target data"

Sur l'ecran "Run details", renseigner :

1. **Run name**
   - Exemple : `deploy-<V>-<YYYY-MM-DD>`

2. **Target data**
   - Source : **BigQuery table**
   - **BigQuery path** : selectionner la vue stable sur les dernieres 24h
     - Exemple recommande : `sentinelle-485209.ml_monitoring.inference_logs_last_24h`

3. **Prediction timestamp column**
   - `request_time`

4. **Data window**
   - Pour un premier test stable : `24 hour(s)`
   - (Si vous utilisez une table correspondant a une journee, `24 hour(s)` est un bon depart)

### B3) Parametres "Baseline data"
- Laisser **Training** (baseline "Training" deja definie dans le Model Monitor via `--baseline-gcs`)

### B4) Objectives (seuils)
Laisser les valeurs par defaut (stables et documentees dans ton setup) :

- Input feature drift
  - Numeric : seuil **0.1** + metric **Jensen-Shannon**
  - Categorical : seuil **0.1** + metric **L-Infinity**
- Output inference drift
  - Numeric : seuil **0.1** + metric **Jensen-Shannon**
  - Categorical : seuil **0.1** + metric **L-Infinity**

### B5) Notifications
- Renseigner l'email d'alertes (par defaut) :
  - `carel.clogenson@epitech.digital`

### B6) Lancer
- Cliquer **Run** / **Continue** puis lancer le run

---

## B-Ul (guide interface Google Cloud) : "quoi cliquer / quoi remplir"
Utiliser la console Google Cloud (Vertex AI → Model Monitoring) pour lancer le run.

1. Ouvrir le lien du `ModelMonitor` (généré par `scripts/vertex_setup_monitoring.py`).
2. Sur la page du `ModelMonitor`, cliquer **Run now**.
3. Sur l'étape **Run details** :
   1. **Run name** : écrire `deploy-<V>-<YYYY-MM-DD>`
   2. **Target data** : sélectionner **BigQuery table**
   3. **BigQuery path** : cliquer **Browse** puis choisir la vue des logs d’inférence sur 24h
      - Exemple recommandé : `sentinelle-485209.ml_monitoring.inference_logs_last_24h`
   4. **Prediction timestamp column** : mettre `request_time`
   5. **Data window** : mettre `24 hour(s)`
4. Sur l'étape **Baseline data** :
   1. Laisser **Training** sélectionné
5. Sur l'étape **Select objectives** :
   1. Garder **Input feature drift** activé
   2. Garder les defaults :
      - Numeric threshold : `0.1`, Metric : `Jensen-Shannon`
      - Categorical threshold : `0.1`, Metric : `L-Infinity`
   3. Garder **Output drift** activé
   4. Garder les defaults :
      - Numeric threshold : `0.1`, Metric : `Jensen-Shannon`
      - Categorical threshold : `0.1`, Metric : `L-Infinity`
6. Sur la section **Notification** :
   1. Vérifier l’email `carel.clogenson@epitech.digital`
7. Cliquer **Continue** puis **Run**.

Une fois lancé :
8. Attendre **Run status = Succeeded**
9. Ouvrir les onglets :
   - **Input feature drift**
   - **Output inference drift**

---

## C. Verification rapide apres le run

1. Run status : doit etre **Succeeded**
2. A regarder dans les onglets :
   - **Input feature drift**
     - drift score et liste des features qui declenchent les alertes
   - **Output inference drift**
     - drift sur `risk_score` et `decision`

### Verification Google Cloud (checklist)

1. **Cloud Run -> service `sentinelle-ml-engine-v2`**
   - verifier `/health`
   - verifier `model_version`

2. **Cloud Storage -> bucket `sentinelle-485209-ml-data`**
   - verifier la presence de fichiers dans :
     `monitoring/inference_logs/YYYY/MM/DD/`

3. **BigQuery -> dataset `ml_monitoring`**
   - verifier la table :
     `inference_logs_v2`
   - verifier la vue :
     `inference_logs_last_24h`
   - verifier `COUNT(*)`, `MIN(request_time)`, `MAX(request_time)`

4. **Vertex AI -> Model monitoring**
   - verifier que le `ModelMonitor` existe pour la version cible
   - verifier que le `Run status` est `Succeeded`
   - ouvrir :
     - `Input feature drift`
     - `Output inference drift`

---

## D. Peut-on dupliquer cette logique ?

Oui :
- Pour chaque nouveau deploiement V :
  1. uploader la baseline `baseline_train.jsonl` -> `monitoring/baseline/v<V>/train_features.jsonl`
  2. relancer `vertex_setup_monitoring.py` pour creer le `ModelMonitor` de V
  3. relancer **Run now** dans Vertex AI sur `sentinelle-485209.ml_monitoring.inference_logs_last_24h` (window 24h)

---

## E. Points d'attention (pour eviter les erreurs frequentes)

1. Si target data est trop petite (peu de rows), les stats de drift peuvent etre trompeuses.
2. La colonne timestamp doit etre `request_time` (ou une colonne equivalente effectivement definie dans la table BigQuery).
3. La baseline doit correspondre a la meme version V (pour une comparaison pertinente).

