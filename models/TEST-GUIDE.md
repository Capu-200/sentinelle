# Guide de test rapide

Ce guide vous permet de tester rapidement le système d'historique et de scoring avant d'implémenter toutes les règles R1-R15.

## 🚀 Test rapide (tout en un)

```bash
cd models
python scripts/test_flow.py
```

Ce script teste automatiquement :
1. ✅ Ajout d'une transaction à l'historique
2. ✅ Visualisation de l'historique
3. ✅ Scoring d'une transaction
4. ✅ Test des règles bloquantes (R1, R2)

## 📝 Tests manuels étape par étape

### 1. Ajouter une transaction normale

```bash
python scripts/push_transaction.py tests/fixtures/transaction_normal.json
```

**Résultat attendu** : Transaction ajoutée avec succès

### 2. Voir l'historique

Le fichier `Data/historique.json` contient toutes les transactions ajoutées.

```bash
# Voir le contenu (si vous avez jq installé)
cat Data/historique.json | jq

# Ou simplement
cat Data/historique.json
```

### 3. Scorer une transaction normale

```bash
python scripts/score_transaction.py tests/fixtures/transaction_normal.json
```

**Résultat attendu** :
- ✅ Features calculées
- ✅ Décision règles: ALLOW
- ✅ Score calculé
- ✅ Décision finale: APPROVE ou REVIEW

### 4. Tester une transaction bloquée (R1 - Montant > 300)

```bash
python scripts/score_transaction.py tests/fixtures/transaction_blocked_r1.json
```

**Résultat attendu** :
- 🚫 Transaction bloquée par R1
- Décision: BLOCK
- Raison: amount_over_kyc_limit

### 5. Tester une transaction bloquée (R2 - Pays interdit)

```bash
python scripts/score_transaction.py tests/fixtures/transaction_blocked_r2.json
```

**Résultat attendu** :
- 🚫 Transaction bloquée par R2
- Décision: BLOCK
- Raison: sanctioned_country

## 🧪 Mode interactif

### Ajouter une transaction interactivement

```bash
python scripts/push_transaction.py --interactive
```

Vous serez invité à saisir :
- transaction_id
- initiator_user_id
- source_wallet_id
- destination_wallet_id
- amount
- currency
- etc.

### Scorer une transaction interactivement

```bash
python scripts/score_transaction.py --interactive
```

## 📊 Créer un historique et scorer

```bash
# 1. Ajouter plusieurs transactions pour créer un historique
python scripts/push_transaction.py tests/fixtures/transaction_normal.json
python scripts/push_transaction.py tests/fixtures/transaction_normal.json  # Même transaction, ID différent

# 2. Scorer une nouvelle transaction (utilisera l'historique)
python scripts/score_transaction.py tests/fixtures/transaction_normal.json --save
```

## 🔍 Vérifier les règles

Les règles actuellement implémentées :

- **R1** : Montant max > 300 PYC → BLOCK
- **R2** : Pays interdit (KP) → BLOCK
- **R3** : Vélocité anormale → BOOST_SCORE (nécessite features historiques)
- **R4** : Nouveau destinataire + montant inhabituel → BOOST_SCORE (nécessite features historiques)

## 📁 Fichiers générés

- `Data/historique.json` : Historique des transactions (créé automatiquement)
- `Data/test_historique.json` : Historique de test (si vous utilisez test_flow.py)

## ⚠️ Notes importantes

1. **Features historiques** : R3 et R4 nécessitent des features historiques qui ne sont pas encore complètement implémentées. Elles ne se déclencheront pas pour l'instant.

2. **Mock des données** : Les informations wallet/user sont mockées (balance=1000, status=active, etc.). En production, cela viendra de la DB.

3. **Scoring ML** : Les modèles ML sont mockés (score=0.5). Le scoring fonctionne mais utilise des valeurs par défaut.

## 🐛 Dépannage

### Erreur : Module not found

```bash
# Assurez-vous d'être dans le répertoire models
cd models

# Vérifiez que les dépendances sont installées
pip install -r requirements.txt
```

### Erreur : Fichier de configuration non trouvé

Les scripts utilisent des chemins relatifs. Assurez-vous d'exécuter depuis le répertoire `models/` :

```bash
cd models
python scripts/test_flow.py
```

### Historique vide

Si l'historique est vide, ajoutez d'abord des transactions :

```bash
python scripts/push_transaction.py tests/fixtures/transaction_normal.json
```

## ✅ Checklist de test

- [ ] Test rapide (`test_flow.py`) fonctionne
- [ ] Ajouter une transaction fonctionne
- [ ] Voir l'historique fonctionne
- [ ] Scorer une transaction normale fonctionne
- [ ] Transaction bloquée R1 (montant > 300) fonctionne
- [ ] Transaction bloquée R2 (pays KP) fonctionne
- [ ] Mode interactif fonctionne

Une fois tous ces tests passés, vous pouvez commencer à implémenter les règles R1-R15 complètes ! 🎉

