# Informations pour le commit GitHub

## 🌿 Nom de branche

```
feat/scoring-pipeline-with-rules-engine
```

**Alternative** :
```
feat/transaction-scoring-system
```

---

## 📝 Message de commit

```
feat: Implémentation du système de scoring avec moteur de règles et historique

- Ajout du système d'historique des transactions (historique_store.py)
  - Stockage local en JSON pour la phase dev
  - Récupération par critères (wallet, utilisateur, fenêtre temporelle)
  - Gestion des timezones (normalisation UTC)

- Scripts d'ajout et de scoring de transactions
  - push_transaction.py : Ajout manuel/interactif de transactions
  - score_transaction.py : Pipeline complet de scoring
  - test_flow.py : Tests automatiques du flux

- Moteur de règles métier (R1-R4)
  - R1 : Montant max > 300 PYC → BLOCK
  - R2 : Pays interdit (KP) → BLOCK
  - R3 : Vélocité anormale → BOOST_SCORE
  - R4 : Nouveau destinataire → BOOST_SCORE
  - Calcul et transmission du boost_factor à travers la pipeline

- Pipeline de scoring complet
  - Feature Engineering (structure prête)
  - Évaluation des règles métier
  - Scoring ML (mock pour l'instant)
  - Calcul du score global avec boost_factor
  - Décision finale (APPROVE/REVIEW/BLOCK)

- Documentation
  - docs/13-historique-et-scoring.md
  - README-SCORING.md
  - TEST-GUIDE.md
  - RECAP-SYSTEME.md

- Tests fonctionnels
  - Transaction normale → APPROVE
  - Transaction bloquée R1 → BLOCK
  - Transaction bloquée R2 → BLOCK

Closes #[numéro_issue_si_pertinent]
```

---

## 📋 Description du PR (Pull Request)

```markdown
## 🎯 Objectif

Implémentation du système de scoring de transactions avec moteur de règles métier et gestion de l'historique.

## ✨ Fonctionnalités ajoutées

### 1. Système d'historique des transactions
- Module `historique_store.py` pour stocker et récupérer l'historique
- Stockage local en JSON (phase dev, prêt pour migration DB)
- Support des fenêtres temporelles (5m, 1h, 24h, 7d, 30d)
- Gestion des timezones (normalisation UTC)

### 2. Scripts d'utilisation
- `push_transaction.py` : Ajout manuel/interactif de transactions
- `score_transaction.py` : Pipeline complet de scoring
- `test_flow.py` : Tests automatiques

### 3. Moteur de règles métier
- Règles bloquantes (R1, R2) : BLOCK immédiat
- Règles boost (R3, R4) : BOOST_SCORE avec calcul du boost_factor
- Transmission du boost_factor à travers toute la pipeline

### 4. Pipeline de scoring
- Feature Engineering (structure prête, extraction à implémenter)
- Évaluation des règles métier
- Scoring ML (mock pour l'instant)
- Calcul du score global : `(0.2 × rule + 0.6 × sup + 0.2 × unsup) × boost_factor`
- Décision finale : APPROVE / REVIEW / BLOCK

## 🧪 Tests

- ✅ Transaction normale → APPROVE
- ✅ Transaction bloquée R1 (montant > 300) → BLOCK
- ✅ Transaction bloquée R2 (pays KP) → BLOCK
- ✅ Tous les tests passent

## 📚 Documentation

- `docs/13-historique-et-scoring.md` : Documentation complète
- `README-SCORING.md` : Guide rapide d'utilisation
- `TEST-GUIDE.md` : Guide de test
- `RECAP-SYSTEME.md` : Récapitulatif du système

## 🔄 Prochaines étapes

- [ ] Implémenter les règles R1-R15 complètes
- [ ] Implémenter les features transactionnelles et historiques
- [ ] Connecter les vrais modèles ML
- [ ] Migration vers PostgreSQL pour la production

## 📦 Dépendances ajoutées

- `pyyaml>=6.0` (déjà dans requirements.txt)
```

---

## 🚀 Commandes Git

```bash
# Créer et basculer sur la branche
git checkout -b feat/scoring-pipeline-with-rules-engine

# Ajouter les fichiers
git add .

# Commit avec le message
git commit -m "feat: Implémentation du système de scoring avec moteur de règles et historique

- Ajout du système d'historique des transactions (historique_store.py)
- Scripts d'ajout et de scoring de transactions
- Moteur de règles métier (R1-R4) avec boost_factor
- Pipeline de scoring complet
- Documentation complète
- Tests fonctionnels"

# Push vers GitHub
git push origin feat/scoring-pipeline-with-rules-engine
```

---

## 📝 Version courte du commit (si besoin)

```
feat: Système de scoring avec règles métier et historique
```

