# ✅ Checklist Avant Push sur GitHub

## 🔍 Vérifications à Faire

### 1. ✅ Fichiers Sensibles (Mots de passe, Secrets)

**Vérifier qu'aucun mot de passe/secret n'est dans le code** :
- [ ] Pas de mots de passe en dur dans le code
- [ ] Pas de clés API dans le code
- [ ] Utiliser `.env` ou variables d'environnement
- [ ] `.env` est dans `.gitignore` ✅

**Fichiers à vérifier** :
- `backend/app/database.py` - Utilise `DATABASE_URL` (env var) ✅
- `backend/env.example` - Template seulement ✅
- Scripts de déploiement - Demandent le mot de passe interactivement ✅

---

### 2. ✅ Fichiers Volumineux (Données)

**À exclure** :
- [ ] `models/Data/raw/*.csv` - Données brutes (volumineuses)
- [ ] `models/Data/processed/*.csv` - Données traitées (volumineuses)
- [ ] `models/artifacts/*.pkl` - Modèles entraînés (volumineux)
- [ ] `backend/venv/` - Environnement virtuel (déjà dans .gitignore) ✅

**Action** : Ajouter à `.gitignore` si pas déjà fait

---

### 3. ✅ Fichiers Temporaires

**Déjà dans .gitignore** :
- ✅ `__pycache__/`
- ✅ `*.pyc`
- ✅ `*.log`
- ✅ `.DS_Store`
- ✅ `venv/`
- ✅ `.env`

**Vérifier** : Ces fichiers ne doivent pas être commités

---

### 4. ✅ Documentation

**À vérifier** :
- [ ] README.md à jour
- [ ] Documentation claire pour l'équipe
- [ ] Pas de documentation obsolète (déjà nettoyé) ✅

---

### 5. ✅ Code

**À vérifier** :
- [ ] Pas de code commenté/debug
- [ ] Imports propres
- [ ] Pas de fichiers de test locaux (déjà supprimés) ✅

---

### 6. ✅ Configuration

**À vérifier** :
- [ ] `requirements.txt` à jour
- [ ] `package.json` à jour (frontend)
- [ ] Scripts de déploiement fonctionnels

---

## 🚨 Actions à Faire

### 1. Mettre à jour `.gitignore`

Ajouter les exclusions pour :
- Données CSV volumineuses
- Artifacts ML (.pkl)
- Fichiers temporaires Cloud

### 2. Vérifier les fichiers sensibles

S'assurer qu'aucun secret n'est commité.

### 3. Tester les scripts

Vérifier que les scripts de déploiement fonctionnent.

---

## 📋 Résumé

**À faire maintenant** :
1. ✅ Mettre à jour `.gitignore` (données, artifacts)
2. ✅ Vérifier qu'aucun secret n'est dans le code
3. ✅ Vérifier que les fichiers volumineux sont exclus

**Déjà fait** :
- ✅ Nettoyage des fichiers obsolètes
- ✅ Documentation à jour
- ✅ Code propre

