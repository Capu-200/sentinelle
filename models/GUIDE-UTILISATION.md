# Guide d'utilisation complet — Système de scoring de transactions

Guide complet pour utiliser le système de scoring de transactions avec historique et règles métier.

---

## 📋 Table des matières

1. [Prérequis et installation](#1-prérequis-et-installation)
2. [Commandes de base](#2-commandes-de-base)
3. [Gestion de l'historique](#3-gestion-de-lhistorique)
4. [Tests des règles métier](#4-tests-des-règles-métier)
5. [Cas d'usage avancés](#5-cas-dusage-avancés)
6. [Débogage et troubleshooting](#6-débogage-et-troubleshooting)
7. [Référence des règles](#7-référence-des-règles)

---

## 1. Prérequis et installation

### Installation des dépendances

```bash
cd models
pip3 install -r requirements.txt
```

**Dépendances principales** :
- `pandas>=2.2.0`
- `python-dateutil>=2.9.0`
- `pyyaml>=6.0`

### Vérification de l'installation

```bash
# Vérifier que Python 3.8+ est installé
python3 --version

# Vérifier que les scripts sont exécutables
python3 scripts/push_transaction.py --help
python3 scripts/score_transaction.py --help
```

---

## 2. Commandes de base

### 2.1 Format de transaction

Le système supporte deux formats :

#### Format enrichi (recommandé - production)

Format avec features pré-calculées côté backend :

```json
{
  "schema_version": "1.0.0",
  "transaction": {
    "transaction_id": "tx_001",
    "amount": 150.0,
    ...
  },
  "context": {
    "source_wallet": { ... },
    "user": { ... }
  },
  "features": {
    "transactional": { ... },
    "historical": { ... }
  }
}
```

Voir `docs/14-transaction-enriched-schema.md` pour la structure complète.

#### Format simple (legacy - dev uniquement)

Format minimal pour développement :

```json
{
  "transaction_id": "tx_001",
  "initiator_user_id": "user_123",
  "source_wallet_id": "wallet_src_456",
  "destination_wallet_id": "wallet_dst_789",
  "amount": 150.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z"
}
```

⚠️ **Note** : Le format simple nécessite `historique_store` et est réservé au développement.

**Champs optionnels** :
- `country` : Code pays ISO (ex: "FR", "KP")
- `city` : Ville
- `description` : Description de la transaction
- `provider` : Système de paiement
- `provider_tx_id` : ID transaction fournisseur

**Créer et ajouter une transaction** :

```bash
# Créer le fichier JSON
cat > ma_transaction.json << EOF
{
  "transaction_id": "tx_001",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 100.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z",
  "country": "FR"
}
EOF

# Ajouter à l'historique
python3 scripts/push_transaction.py ma_transaction.json
```

**Résultat attendu** :
```
✅ Transaction tx_001 ajoutée avec succès!
📊 Historique total: 1 transactions
```

#### Option B : Mode interactif

```bash
python3 scripts/push_transaction.py --interactive
```

Le script vous demandera de saisir :
- `transaction_id` : Identifiant unique de la transaction
- `initiator_user_id` : ID de l'utilisateur initiateur
- `source_wallet_id` : ID du wallet source
- `destination_wallet_id` : ID du wallet destination
- `amount` : Montant en PYC
- `currency` : Devise (PYC par défaut)
- `transaction_type` : Type (P2P par défaut)
- `direction` : Direction (outgoing/incoming)
- `country` : Code pays (optionnel)
- `city` : Ville (optionnel)
- `description` : Description (optionnel)

### 2.2 Scorer une transaction

Le script détecte automatiquement le format (enrichi ou simple).

#### Option A : Transaction enrichie (recommandé)

```bash
python3 scripts/score_transaction.py tests/fixtures/enriched_transaction_example.json
```

#### Option B : Transaction simple (legacy - dev uniquement)

```bash
python3 scripts/score_transaction.py tests/fixtures/test_normal.json
```

**Résultat attendu** :
```
🔧 Initialisation des composants...

📊 Calcul des features (tx_id: tx_001)...
   ✅ 0 features calculées

⚖️  Évaluation des règles métier (tx_id: tx_001)...
   ✅ Décision règles: ALLOW
   📋 Raisons: Aucune
   📈 Rule score: 0.000
   🚀 Boost factor: 1.00

🤖 Scoring ML (tx_id: tx_001)...
   ✅ Supervisé: 0.500
   ✅ Non supervisé: 0.500

🎯 Calcul du score global (tx_id: tx_001)...
   ✅ Risk score: 0.400

⚖️  Décision finale (tx_id: tx_001)...

📊 Résultat final (tx_id: tx_001):
   Transaction ID: tx_001
   Risk score: 0.400
   Decision: APPROVE
   Reasons: Aucune
   Model version: v1.0.0
```

#### Option B : Mode interactif

```bash
python3 scripts/score_transaction.py --interactive
```

#### Option C : Scorer et sauvegarder

```bash
# Scorer la transaction et l'ajouter à l'historique après
python3 scripts/score_transaction.py ma_transaction.json --save
```

### 2.3 Test automatique complet

```bash
python3 scripts/test_flow.py
```

Ce script teste automatiquement :
- ✅ Scoring d'une transaction enrichie normale
- ✅ Test des règles bloquantes (R1)
- ✅ Test des règles boost (R13)
- ✅ Test du cas 0 transaction historique

---

## 3. Gestion de l'historique

### 3.1 Voir l'historique

L'historique est stocké dans `Data/historique.json` (créé automatiquement).

```bash
# Voir le contenu (si vous avez jq installé)
cat Data/historique.json | jq

# Ou simplement
cat Data/historique.json

# Voir le nombre de transactions
cat Data/historique.json | jq 'length'
```

### 3.2 Filtrer l'historique

```bash
# Voir les transactions d'un wallet spécifique
cat Data/historique.json | jq '.[] | select(.source_wallet_id == "wallet_001")'

# Voir les transactions d'un montant > 100
cat Data/historique.json | jq '.[] | select(.amount > 100)'

# Voir les transactions bloquées (si status est présent)
cat Data/historique.json | jq '.[] | select(.status == "BLOCKED")'
```

### 3.3 Réinitialiser l'historique

```bash
# Sauvegarder l'ancien historique (optionnel)
cp Data/historique.json Data/historique_backup.json

# Réinitialiser
echo "[]" > Data/historique.json
```

### 3.4 Utiliser un historique personnalisé

```bash
# Spécifier un fichier d'historique différent
python3 scripts/push_transaction.py transaction.json --storage Data/mon_historique.json
python3 scripts/score_transaction.py transaction.json --storage Data/mon_historique.json
```

---

## 4. Tests des règles métier

### 4.1 Règles bloquantes (BLOCK immédiat)

Ces règles bloquent la transaction sans passer par l'IA.

#### R1 — Montant maximum (> 300 PYC)

**Description** : Bloque toute transaction dépassant 300 PYC.

**Test** :

```bash
# Créer une transaction avec montant > 300
cat > test_r1.json << EOF
{
  "transaction_id": "tx_test_r1",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 350.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z"
}
EOF

python3 scripts/score_transaction.py test_r1.json
```

**Résultat attendu** :
```
🚫 TRANSACTION BLOQUÉE par les règles (tx_id: tx_test_r1)

📊 Résultat final (tx_id: tx_test_r1):
   Transaction ID: tx_test_r1
   Risk score: 1.000
   Decision: BLOCK
   Reasons: RULE_MAX_AMOUNT
   Model version: v1.0.0
```

#### R2 — Solde insuffisant

**Description** : Bloque si le wallet source n'a pas assez de fonds.

**Test** :

```bash
# Créer une transaction avec montant > balance (1000 PYC par défaut dans les mocks)
cat > test_r2.json << EOF
{
  "transaction_id": "tx_test_r2",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 1500.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z"
}
EOF

python3 scripts/score_transaction.py test_r2.json
```

**Résultat attendu** : `Decision: BLOCK`, `Reasons: RULE_INSUFFICIENT_FUNDS`

#### R3 — Wallet bloqué ou utilisateur suspendu

**Description** : Bloque si le wallet ou l'utilisateur est bloqué.

**Note** : Cette règle utilise les mocks. Le wallet/user est considéré comme "active" par défaut. Pour tester, il faudrait modifier les mocks dans `historique_store.py`.

#### R4 — Auto-virement interdit

**Description** : Bloque si source_wallet_id = destination_wallet_id.

**Test** :

```bash
cat > test_r4.json << EOF
{
  "transaction_id": "tx_test_r4",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_001",
  "amount": 100.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z"
}
EOF

python3 scripts/score_transaction.py test_r4.json
```

**Résultat attendu** : `Decision: BLOCK`, `Reasons: RULE_SELF_TRANSFER`

#### R5 — Montant nul ou négatif

**Description** : Bloque les transactions avec montant ≤ 0.

**Test** :

```bash
cat > test_r5.json << EOF
{
  "transaction_id": "tx_test_r5",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": -10.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z"
}
EOF

python3 scripts/score_transaction.py test_r5.json
```

**Résultat attendu** : `Decision: BLOCK`, `Reasons: RULE_INVALID_AMOUNT`

#### R6 — Pays interdit (blacklist)

**Description** : Bloque les transactions depuis pays KP (Corée du Nord).

**Test** :

```bash
# Utiliser le fichier existant
python3 scripts/score_transaction.py tests/fixtures/transaction_blocked_r2.json

# Ou créer manuellement
cat > test_r6.json << EOF
{
  "transaction_id": "tx_test_r6",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 100.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z",
  "country": "KP"
}
EOF

python3 scripts/score_transaction.py test_r6.json
```

**Résultat attendu** : `Decision: BLOCK`, `Reasons: RULE_COUNTRY_BLOCKED`

#### R7 — Destination interdite

**Description** : Bloque si le wallet destination est bloqué.

**Note** : Nécessite que le wallet destination soit marqué comme non-actif dans les mocks.

### 4.2 Règles BOOST_SCORE

Ces règles ajoutent une pénalité au score mais laissent passer la transaction.

#### R8 — Montant inhabituel

**Description** : Détecte les montants extrêmement supérieurs aux habitudes.

**Condition** : `amount > avg_amount_30d * 10` ou `amount > avg_amount_30d * 5`

**Note** : Nécessite la feature `avg_amount_30d` (non implémentée pour l'instant).

#### R9 — Rafale de transactions

**Description** : Détecte les pics de fréquence extrêmes.

**Condition** : `tx_last_10min >= 20` ou `tx_last_10min >= 10`

**Note** : Nécessite la feature `tx_last_10min` (non implémentée pour l'instant).

#### R10 — Compte trop récent

**Description** : Détecte les transactions importantes juste après création du compte.

**Condition** : 
- `account_age_minutes < 5 ET amount > 100` → BOOST_SCORE
- `account_age_minutes < 60 ET amount > 50` → BOOST_SCORE

**Note** : Cette règle fonctionne car `account_age_minutes` est calculé dans le context.

### 4.3 Règles mixtes (BLOCK ou BOOST_SCORE)

Ces règles peuvent être bloquantes ou boost selon les conditions.

#### R11 — Nouveau bénéficiaire + montant élevé

**Description** : Détecte un premier paiement important vers un nouveau wallet.

**Conditions** :
- `is_new_beneficiary = true ET amount > 200` → **BLOCK**
- `is_new_beneficiary = true ET amount > 80` → **BOOST_SCORE**

**Note** : Nécessite la feature `is_new_beneficiary` (non implémentée pour l'instant).

#### R12 — Pays inhabituel

**Description** : Détecte un changement brutal de pays + montant élevé.

**Condition** : `country NOT IN user_country_history ET amount > 150` → **BLOCK**

**Note** : Nécessite la feature `user_country_history` (non implémentée pour l'instant).

#### R13 — Horaire interdit

**Description** : Détecte les transactions à heures très atypiques (01:00-05:00 UTC).

**Test** :

```bash
# Créer une transaction à 2h du matin UTC avec montant > 60
cat > test_r13.json << EOF
{
  "transaction_id": "tx_test_r13",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 100.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T02:30:00Z"
}
EOF

python3 scripts/score_transaction.py test_r13.json
```

**Résultats attendus** :
- Si `amount > 120` : `Decision: BLOCK`, `Reasons: RULE_ODD_HOUR`
- Si `amount > 60` : `Decision: BOOST_SCORE`, `Reasons: RULE_ODD_HOUR`

#### R14 — Profil à risque connu

**Description** : Renforce la sévérité pour les profils déjà à risque.

**Conditions** :
- `risk_level = 'high' ET amount > 150` → **BLOCK**
- `risk_level = 'high' ET amount > 50` → **BOOST_SCORE**

**Note** : Utilise les mocks. Par défaut, `risk_level = 'low'`. Pour tester, il faudrait modifier les mocks.

#### R15 — Récidive récente

**Description** : Détecte si trop d'incidents récents.

**Conditions** :
- `blocked_tx_last_24h >= 3` → **BLOCK**
- `blocked_tx_last_24h >= 1` → **BOOST_SCORE**

**Note** : Nécessite la feature `blocked_tx_last_24h` (non implémentée pour l'instant).

---

## 5. Cas d'usage avancés

### 5.1 Créer un historique et tester les features historiques

```bash
# 1. Ajouter plusieurs transactions pour créer un historique
python3 scripts/push_transaction.py tests/fixtures/transaction_normal.json

# 2. Ajouter une autre transaction (même wallet source)
cat > tx2.json << EOF
{
  "transaction_id": "tx_002",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_003",
  "amount": 75.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:05:00Z"
}
EOF
python3 scripts/push_transaction.py tx2.json

# 3. Scorer une nouvelle transaction (utilisera l'historique)
cat > tx3.json << EOF
{
  "transaction_id": "tx_003",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_004",
  "amount": 200.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:10:00Z"
}
EOF
python3 scripts/score_transaction.py tx3.json --save
```

### 5.2 Tester plusieurs règles en même temps

```bash
# Transaction qui déclenche plusieurs règles
cat > tx_multi_rules.json << EOF
{
  "transaction_id": "tx_multi",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 250.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T03:00:00Z",
  "country": "FR"
}
EOF

python3 scripts/score_transaction.py tx_multi_rules.json
```

Cette transaction pourrait déclencher :
- R13 (horaire interdit) si amount > 60

### 5.3 Utiliser des configurations personnalisées

```bash
# Spécifier des fichiers de configuration différents
python3 scripts/score_transaction.py transaction.json \
  --rules-config src/rules/config/rules_v1.yaml \
  --scoring-config configs/scoring_config.yaml \
  --decision-config configs/scoring_config.yaml
```

### 5.4 Workflow complet : Ajouter → Scorer → Vérifier

```bash
# 1. Créer une transaction
cat > workflow_tx.json << EOF
{
  "transaction_id": "tx_workflow",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 150.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z",
  "country": "FR"
}
EOF

# 2. Scorer la transaction
python3 scripts/score_transaction.py workflow_tx.json

# 3. Si APPROVE, ajouter à l'historique
python3 scripts/push_transaction.py workflow_tx.json

# 4. Vérifier qu'elle est dans l'historique
cat Data/historique.json | jq '.[] | select(.transaction_id == "tx_workflow")'
```

---

## 6. Débogage et troubleshooting

### 6.1 Erreurs courantes

#### Erreur : Module not found

```bash
# Solution : Installer les dépendances
cd models
pip3 install -r requirements.txt
```

#### Erreur : Fichier de configuration non trouvé

```bash
# Solution : S'assurer d'être dans le répertoire models/
cd models
python3 scripts/score_transaction.py transaction.json
```

#### Erreur : can't compare offset-naive and offset-aware datetimes

Cette erreur est normalement corrigée. Si elle apparaît, vérifiez que vous utilisez la dernière version du code.

#### Historique vide

```bash
# Solution : Ajouter des transactions d'abord
python3 scripts/push_transaction.py tests/fixtures/transaction_normal.json
```

### 6.2 Vérifier les logs

Tous les logs affichent maintenant l'ID de la transaction (`tx_id`) pour faciliter le débogage :

```
📊 Calcul des features (tx_id: tx_001)...
⚖️  Évaluation des règles métier (tx_id: tx_001)...
📊 Résultat final (tx_id: tx_001):
   Transaction ID: tx_001
   ...
```

### 6.3 Vérifier l'état du système

```bash
# Vérifier le nombre de transactions dans l'historique
cat Data/historique.json | jq 'length'

# Vérifier les transactions récentes
cat Data/historique.json | jq '.[-5:]'  # 5 dernières

# Vérifier les transactions d'un wallet
cat Data/historique.json | jq '.[] | select(.source_wallet_id == "wallet_001")'
```

### 6.4 Mode verbose (si implémenté)

Pour plus de détails, vous pouvez modifier temporairement les scripts pour ajouter des `print()` supplémentaires.

---

## 7. Référence des règles

### 7.1 Liste complète des règles

| Règle | Type | Condition | Action | Reason Code |
|-------|------|-----------|--------|-------------|
| **R1** | BLOCK | `amount > 300 PYC` | BLOCK | `RULE_MAX_AMOUNT` |
| **R2** | BLOCK | `wallet.balance < amount` | BLOCK | `RULE_INSUFFICIENT_FUNDS` |
| **R3** | BLOCK | `wallet.status ≠ 'active'` OU `user.status ≠ 'active'` | BLOCK | `RULE_ACCOUNT_LOCKED` |
| **R4** | BLOCK | `source_wallet_id = destination_wallet_id` | BLOCK | `RULE_SELF_TRANSFER` |
| **R5** | BLOCK | `amount ≤ 0` | BLOCK | `RULE_INVALID_AMOUNT` |
| **R6** | BLOCK | `country IN ['KP']` | BLOCK | `RULE_COUNTRY_BLOCKED` |
| **R7** | BLOCK | `destination_wallet.status ≠ 'active'` | BLOCK | `RULE_DESTINATION_LOCKED` |
| **R8** | BOOST | `amount > avg_amount_30d * 10` ou `* 5` | BOOST_SCORE | `RULE_AMOUNT_ANOMALY` |
| **R9** | BOOST | `tx_last_10min >= 20` ou `>= 10` | BOOST_SCORE | `RULE_FREQ_SPIKE` |
| **R10** | BOOST | `account_age < 5min ET amount > 100` ou `< 60min ET amount > 50` | BOOST_SCORE | `RULE_NEW_ACCOUNT_ACTIVITY` |
| **R11** | MIXTE | `is_new_beneficiary ET amount > 200` → BLOCK<br>`is_new_beneficiary ET amount > 80` → BOOST | BLOCK/BOOST | `RULE_NEW_BENEFICIARY` |
| **R12** | BLOCK | `country NOT IN history ET amount > 150` | BLOCK | `RULE_GEO_ANOMALY` |
| **R13** | MIXTE | `hour 01:00-05:00 ET amount > 120` → BLOCK<br>`hour 01:00-05:00 ET amount > 60` → BOOST | BLOCK/BOOST | `RULE_ODD_HOUR` |
| **R14** | MIXTE | `risk_level='high' ET amount > 150` → BLOCK<br>`risk_level='high' ET amount > 50` → BOOST | BLOCK/BOOST | `RULE_HIGH_RISK_PROFILE` |
| **R15** | MIXTE | `blocked_tx_last_24h >= 3` → BLOCK<br>`blocked_tx_last_24h >= 1` → BOOST | BLOCK/BOOST | `RULE_RECIDIVISM` |

### 7.2 Règles testables immédiatement

Ces règles fonctionnent sans features historiques :
- ✅ **R1** : Montant > 300 PYC
- ✅ **R2** : Solde insuffisant (si montant > 1000)
- ✅ **R4** : Auto-virement
- ✅ **R5** : Montant nul/négatif
- ✅ **R6** : Pays KP
- ✅ **R13** : Horaire interdit (01:00-05:00 UTC)

### 7.3 Règles nécessitant des features historiques

Ces règles nécessitent des features qui ne sont pas encore implémentées :
- ⚠️ **R8** : Nécessite `avg_amount_30d`
- ⚠️ **R9** : Nécessite `tx_last_10min`
- ⚠️ **R10** : Fonctionne (utilise `account_age_minutes` du context)
- ⚠️ **R11** : Nécessite `is_new_beneficiary`
- ⚠️ **R12** : Nécessite `user_country_history`
- ⚠️ **R15** : Nécessite `blocked_tx_last_24h`

### 7.4 Calcul du boost_factor

Le `boost_factor` est calculé ainsi :
- Base : 1.0 (pas de boost)
- Par règle BOOST_SCORE déclenchée : +0.1
- Maximum : 2.0

**Exemples** :
- 1 règle BOOST_SCORE → `boost_factor = 1.1`
- 3 règles BOOST_SCORE → `boost_factor = 1.3`
- 10+ règles BOOST_SCORE → `boost_factor = 2.0` (cap)

---

## 8. Exemples de transactions de test

### Transaction normale (devrait être APPROVE)

```json
{
  "transaction_id": "tx_normal",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 50.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z",
  "country": "FR"
}
```

### Transaction bloquée R1 (montant > 300)

```json
{
  "transaction_id": "tx_blocked_r1",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 350.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z"
}
```

### Transaction bloquée R6 (pays KP)

```json
{
  "transaction_id": "tx_blocked_r6",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 100.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T12:00:00Z",
  "country": "KP"
}
```

### Transaction avec boost R13 (horaire interdit)

```json
{
  "transaction_id": "tx_boost_r13",
  "initiator_user_id": "user_001",
  "source_wallet_id": "wallet_001",
  "destination_wallet_id": "wallet_002",
  "amount": 80.0,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "created_at": "2026-01-21T03:00:00Z"
}
```

---

## 9. Notes importantes

### 9.1 Phase de développement

- **Historique** : Stocké localement dans `Data/historique.json`
- **Mocks** : Les données wallet/user sont mockées (balance=1000, status=active, risk_level=low)
- **Scoring ML** : Les modèles sont mockés (score=0.5)
- **Features historiques** : Certaines features ne sont pas encore implémentées

### 9.2 Production

En production, ces éléments seront remplacés par :
- Base de données PostgreSQL pour l'historique
- Vraies requêtes DB pour wallet/user
- Vrais modèles ML (LightGBM + IsolationForest)
- Feature Store pour les agrégats historiques

### 9.3 Performance

- Latence cible : < 300ms (p95)
- Les règles sont évaluées dans l'ordre : bloquantes d'abord, puis BOOST_SCORE
- Si une règle bloquante est déclenchée, l'évaluation s'arrête immédiatement

---

## 10. Checklist de test

Avant de considérer le système comme fonctionnel, vérifiez :

- [ ] Installation des dépendances réussie
- [ ] Test automatique (`test_flow.py`) fonctionne
- [ ] Ajouter une transaction fonctionne (fichier + interactif)
- [ ] Scorer une transaction fonctionne
- [ ] Voir l'historique fonctionne
- [ ] R1 (montant > 300) bloque correctement
- [ ] R4 (auto-virement) bloque correctement
- [ ] R5 (montant négatif) bloque correctement
- [ ] R6 (pays KP) bloque correctement
- [ ] R13 (horaire interdit) fonctionne correctement
- [ ] Les logs affichent l'ID de transaction

---

## 11. Support et documentation

Pour plus d'informations :

- **Architecture** : `docs/00-architecture.md`
- **Règles détaillées** : `docs/03-rules-detailed.md`
- **API Contract** : `docs/02-api-contract.md`
- **Feature Engineering** : `docs/04-feature-engineering.md`

---

**Dernière mise à jour** : 2026-01-22

