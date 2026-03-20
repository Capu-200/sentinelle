# ⚙️ Configuration du Backend API

## 🔗 URL du ML Engine

L'URL du ML Engine doit être configurée dans une variable d'environnement.

### URL Actuelle

```
https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app
```

### Comment Récupérer l'URL

```bash
gcloud run services describe sentinelle-ml-engine-v2 \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --format="value(status.url)"
```

---

## 📝 Configuration Locale

### 1. Créer un fichier `.env`

Copiez `.env.example` vers `.env` :

```bash
cd backend
cp .env.example .env
```

### 2. Modifier `.env`

Éditez `.env` et mettez à jour l'URL :

```bash
ML_ENGINE_URL=https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app
```

### 3. Charger les variables d'environnement

Le backend charge automatiquement les variables depuis `.env` si vous utilisez `python-dotenv`.

**Installation** :
```bash
pip install python-dotenv
```

**Utilisation dans `main.py`** :
```python
from dotenv import load_dotenv
load_dotenv()  # Charge .env automatiquement
```

---

## ☁️ Configuration Production (Cloud Run)

Pour le backend déployé sur Cloud Run, configurez les variables d'environnement lors du déploiement :

```bash
gcloud run deploy sentinelle-backend \
  --set-env-vars="ML_ENGINE_URL=https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app" \
  --region=europe-west1 \
  --project=sentinelle-485209
```

---

## 🔄 Mise à Jour de l'URL

Si vous redéployez le ML Engine et que l'URL change :

1. **Récupérer la nouvelle URL** :
   ```bash
   gcloud run services describe sentinelle-ml-engine-v2 \
     --region=europe-west1 \
     --project=sentinelle-485209 \
     --format="value(status.url)"
   ```

2. **Mettre à jour `.env`** (local) :
   ```bash
   ML_ENGINE_URL=<nouvelle-url>
   ```

3. **Mettre à jour Cloud Run** (production) :
   ```bash
   gcloud run services update sentinelle-backend \
     --update-env-vars="ML_ENGINE_URL=<nouvelle-url>" \
     --region=europe-west1 \
     --project=sentinelle-485209
   ```

---

## ✅ Vérification

### Tester la connexion au ML Engine

```bash
# Health check
curl https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app/health

# Depuis le backend
curl http://localhost:8000/health
```

Le endpoint `/health` du backend devrait retourner :
```json
{
  "status": "healthy",
  "ml_engine": "healthy"
}
```

---

## 📋 Checklist

- [ ] ✅ Fichier `.env` créé (copié depuis `.env.example`)
- [ ] ✅ `ML_ENGINE_URL` configurée dans `.env`
- [ ] ✅ `python-dotenv` installé
- [ ] ✅ Backend charge les variables depuis `.env`
- [ ] ✅ Health check du backend fonctionne
- [ ] ✅ Connexion au ML Engine vérifiée

---

## 🎯 Pourquoi C'est Important

1. **Séparation des environnements** : Dev vs Production
2. **Sécurité** : Pas d'URLs hardcodées dans le code
3. **Flexibilité** : Changement d'URL sans modifier le code
4. **Reproductibilité** : Chaque développeur peut avoir sa propre config

