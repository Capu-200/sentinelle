# 🔄 Guide de Redéploiement du ML Engine

Guide pour redéployer le ML Engine après des modifications de code.

---

## 📋 Réponses à Vos Questions

### 1. Redéploiement = Mise à Jour du Code, PAS du Modèle

**Important** : Le redéploiement met à jour **le code du service** (l'API), **PAS le modèle lui-même**.

- ✅ **Modèle** : Reste le même (fichiers `.pkl` dans Cloud Storage)
- ✅ **Code** : Mis à jour (nouveau code Python déployé)
- ✅ **Service** : Redémarre avec le nouveau code

**Le modèle n'est pas modifié**, seulement le code qui l'utilise.

---

### 2. Valeurs par Défaut et Précision

**Problème potentiel** : Oui, les valeurs par défaut peuvent fausser les résultats si mal gérées.

**Solution implémentée** : Gestion intelligente selon la présence d'historique :

- **Si historique présent** : Valeurs par défaut = "pas de données" (0, -1)
- **Si historique absent** : Valeurs par défaut = "nouveau compte" (0, -1, 1 pour "new")

**Exemple** :
- `is_new_destination_30d` :
  - Si historique présent mais feature manquante → `0` (pas nouveau)
  - Si historique absent → `1` (nouveau, plus conservateur)

---

### 3. Gestion Spécifique Historique Présent/Absent

**Oui, c'est implémenté !** ✅

Le système détecte automatiquement :
- **Historique présent** : Au moins une feature historique non-nulle
- **Historique absent** : Toutes les features historiques sont nulles ou manquantes

**Comportement** :
- Historique présent → Valeurs par défaut = "pas de données"
- Historique absent → Valeurs par défaut = "nouveau compte" (plus conservateur)

---

## 🚀 Commandes de Redéploiement

### Étape 1 : Vérifier les Modifications

```bash
cd models
git status
```

### Étape 2 : Redéployer le ML Engine

```bash
cd models

./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.0.0-test"
```

**Ce que ça fait** :
1. ✅ Construit une nouvelle image Docker avec le code mis à jour
2. ✅ Déploie sur Cloud Run (remplace l'ancienne version)
3. ✅ Le service redémarre avec le nouveau code
4. ✅ Les modèles sont rechargés depuis Cloud Storage (mêmes fichiers)

**Temps** : ~5-10 minutes

### Si l’erreur « ambiguous truth value » ou 500 persiste après déploiement

1. **Vérifier le code déployé**  
   Le déploiement utilise le dossier depuis lequel vous lancez le script. Lancez toujours depuis le répertoire `models/` :
   ```bash
   cd /chemin/vers/sentinelle/models
   ./scripts/deploy-ml-engine.sh
   ```
2. **Forcer un rebuild complet**  
   Si Cloud Build réutilise une ancienne image, build puis déploiement à la main sans cache :
   ```bash
   cd models
   # Build sans cache puis déployer l’image
   gcloud builds submit --tag europe-west1-docker.pkg.dev/sentinelle-485209/cloud-run-source-deploy/sentinelle-ml-engine:latest . --no-cache --project=sentinelle-485209
   gcloud run deploy sentinelle-ml-engine --image europe-west1-docker.pkg.dev/sentinelle-485209/cloud-run-source-deploy/sentinelle-ml-engine:latest --region=europe-west1
   ```
   (À adapter selon votre projet/région si besoin.)

---

### Étape 3 : Vérifier le Déploiement

```bash
# Vérifier que le service est prêt
curl https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/health

# Vérifier les logs
gcloud run services logs read sentinelle-ml-engine \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=50
```

---

## 🔍 Ce Qui Change vs Ce Qui Ne Change Pas

### ✅ Change (Code)

- Code Python (`api/main.py`, `src/models/`, `src/features/`)
- Logique de validation des features
- Gestion des valeurs par défaut
- Détection de l'historique

### ❌ Ne Change Pas (Modèle)

- Fichiers `.pkl` (modèles entraînés)
- `feature_schema.json`
- `thresholds.json`
- Artefacts dans Cloud Storage

---

## 💡 Améliorations Apportées

### 1. Détection Automatique de l'Historique

Le système détecte si l'historique est présent :
- Si au moins une feature historique est non-nulle → Historique présent
- Sinon → Historique absent

### 2. Valeurs par Défaut Intelligentes

**Si historique présent** :
- `is_new_destination_30d` manquant → `0` (pas nouveau)
- `days_since_last_src_to_dst` manquant → `-1.0` (jamais)

**Si historique absent** :
- `is_new_destination_30d` manquant → `1` (nouveau, plus conservateur)
- `days_since_last_src_to_dst` manquant → `-1.0` (jamais)

### 3. Complétion Automatique des Features

- Détecte les features manquantes
- Les complète avec valeurs par défaut intelligentes
- Réordonne selon l'ordre attendu par le modèle

---

## ⚠️ Impact sur les Résultats

### Avec Historique Présent

**Avant** : Features manquantes → Erreur
**Après** : Features manquantes → Valeurs par défaut (0, -1) → Score légèrement modifié mais cohérent

**Impact** : Minimal si toutes les features importantes sont présentes

### Sans Historique

**Avant** : Features manquantes → Erreur
**Après** : Features manquantes → Valeurs "nouveau compte" → Score plus conservateur

**Impact** : Plus conservateur (meilleure sécurité), mais peut être moins précis

---

## ✅ Recommandation

**Pour des résultats optimaux** :
1. ✅ **Inclure toutes les features** dans le JSON (voir `JSON_COMPLET_50_FEATURES.md`)
2. ✅ **Utiliser l'historique réel** quand disponible
3. ✅ **Le système complétera automatiquement** les manquantes si nécessaire

**Le système fonctionne maintenant même avec des features manquantes**, mais les résultats seront plus précis avec toutes les features.

---

## 📋 Checklist de Redéploiement

- [ ] ✅ Code modifié et testé localement (optionnel)
- [ ] ✅ Redéployer avec `deploy-ml-engine.sh`
- [ ] ✅ Vérifier le health check
- [ ] ✅ Tester avec Postman (JSON enrichi)
- [ ] ✅ Vérifier les logs pour erreurs

---

## 🎯 Résumé

**Redéploiement** :
- ✅ Met à jour le **code** (pas le modèle)
- ✅ Temps : ~5-10 minutes
- ✅ Commandes : `./scripts/deploy-ml-engine.sh ...`

**Valeurs par défaut** :
- ✅ Gestion intelligente selon présence d'historique
- ✅ Plus conservateur si historique absent
- ✅ Recommandé : inclure toutes les features quand possible

**Gestion historique** :
- ✅ Détection automatique
- ✅ Valeurs par défaut adaptées
- ✅ Plus précis avec historique complet

