# 13 — Historique et scoring manuel

## Vue d'ensemble

Ce document décrit le système de stockage d'historique et les scripts pour scorer des transactions manuellement (phase de développement).

## Stockage d'historique

### Module `src/data/historique_store.py`

Le module `HistoriqueStore` gère le stockage local des transactions pour la phase de développement.

**Fonctionnalités** :
- Stockage des transactions dans un fichier JSON/CSV
- Récupération de l'historique selon des critères (wallet, utilisateur, fenêtre temporelle)
- Calcul des fenêtres temporelles (5m, 1h, 24h, 7d, 30d)
- Mock des données wallet/user (à remplacer par vraie DB en production)

**Utilisation** :

```python
from src.data.historique_store import HistoriqueStore

# Initialiser le store
store = HistoriqueStore(storage_path="Data/historique.json")

# Ajouter une transaction
store.add_transaction(transaction)

# Récupérer l'historique
historical_data = store.get_historical_data(
    source_wallet_id="wallet_123",
    before_time=datetime.now(),
)

# Récupérer les transactions dans une fenêtre
tx_in_window = store.get_transactions_in_window(
    source_wallet_id="wallet_123",
    window="1h",
    current_time=datetime.now(),
)
```

## Scripts

### 1. `scripts/push_transaction.py`

Script pour ajouter manuellement une transaction à l'historique.

**Usage** :

```bash
# Depuis un fichier JSON
python scripts/push_transaction.py tests/fixtures/example_transaction.json

# Mode interactif
python scripts/push_transaction.py --interactive

# Spécifier le fichier de stockage
python scripts/push_transaction.py transaction.json --storage Data/custom_historique.json
```

**Fichier JSON de transaction** :

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
  "created_at": "2026-01-21T12:00:00Z",
  "country": "FR"
}
```

### 2. `scripts/score_transaction.py`

Script principal pour scorer une transaction. Orchestre tout le pipeline de scoring.

**Usage** :

```bash
# Depuis un fichier JSON
python scripts/score_transaction.py tests/fixtures/example_transaction.json

# Mode interactif
python scripts/score_transaction.py --interactive

# Sauvegarder la transaction après scoring
python scripts/score_transaction.py transaction.json --save

# Spécifier les fichiers de configuration
python scripts/score_transaction.py transaction.json \
  --rules-config src/rules/config/rules_v1.yaml \
  --scoring-config configs/scoring_config.yaml
```

**Flux d'exécution** :

1. Charge la transaction depuis le fichier ou mode interactif
2. Initialise les composants (store, feature pipeline, rules engine, scorer, decision engine)
3. Récupère l'historique depuis le store
4. Calcule les features (transactionnelles + historiques)
5. Évalue les règles métier
   - Si `BLOCK` → arrêt immédiat, affiche le résultat
   - Sinon → continue avec le scoring ML
6. Score ML (supervisé + non supervisé) - mock pour l'instant
7. Calcule le score global avec `boost_factor`
8. Prend la décision finale (BLOCK/REVIEW/APPROVE)
9. Affiche le résultat et sauvegarde si `--save`

**Exemple de sortie** :

```
🔧 Initialisation des composants...
📊 Calcul des features...
   ✅ 15 features calculées
⚖️  Évaluation des règles métier...
   ✅ Décision règles: BOOST_SCORE
   📋 Raisons: high_velocity, new_destination_wallet
   📈 Rule score: 0.600
   🚀 Boost factor: 1.20
🤖 Scoring ML...
   ✅ Supervisé: 0.500
   ✅ Non supervisé: 0.500
🎯 Calcul du score global...
   ✅ Risk score: 0.600
⚖️  Décision finale...
📊 Résultat final:
   Risk score: 0.600
   Decision: REVIEW
   Reasons: high_velocity, new_destination_wallet
   Model version: v1.0.0
```

## Transmission du boost_factor

Le `boost_factor` est calculé par les règles métier et transmis à travers toute la pipeline :

1. **Règles métier** (`src/rules/engine.py`) :
   - Calcule `boost_factor` basé sur le nombre de règles BOOST_SCORE déclenchées
   - Retourne `RulesOutput` avec `boost_factor` et `decision`

2. **Scorer global** (`src/scoring/scorer.py`) :
   - Reçoit `boost_factor` en paramètre
   - Applique le boost : `risk_score = (formule) × boost_factor`

3. **Décision finale** (`src/scoring/decision.py`) :
   - Utilise le `risk_score` boosté pour prendre la décision

**Formule du boost_factor** :
- Base : 1.0 (pas de boost)
- Par règle BOOST_SCORE déclenchée : +0.1
- Maximum : 2.0

Exemple :
- 1 règle BOOST_SCORE → `boost_factor = 1.1`
- 3 règles BOOST_SCORE → `boost_factor = 1.3`
- 10+ règles BOOST_SCORE → `boost_factor = 2.0` (cap)

## Migration vers production

En production, le `HistoriqueStore` sera remplacé par :

1. **Base de données PostgreSQL** :
   - Requêtes SQL pour récupérer l'historique
   - Tables `banking.transactions`, `banking.accounts`, `auth.users`

2. **Feature Store** :
   - Pré-calcul des agrégats historiques
   - Cache pour performance

3. **API REST** :
   - Endpoint `/score` pour scorer une transaction
   - Intégration avec le backend

**Points d'attention** :
- Le `HistoriqueStore` actuel utilise des mocks pour `get_wallet_info()` et `get_user_profile()`
- En production, ces méthodes feront des requêtes à la DB
- Les performances doivent rester < 300ms (p95)

## Exemples

### Exemple 1 : Ajouter plusieurs transactions

```bash
# Transaction 1
python scripts/push_transaction.py transaction1.json

# Transaction 2 (même wallet source)
python scripts/push_transaction.py transaction2.json

# Transaction 3 (scorer avec historique)
python scripts/score_transaction.py transaction3.json --save
```

### Exemple 2 : Tester une règle bloquante

```json
{
  "transaction_id": "tx_blocked",
  "amount": 1500.0,
  "currency": "PYC",
  ...
}
```

Cette transaction sera bloquée par la règle R1 (montant > 1000 PYC).

### Exemple 3 : Tester le boost_score

```json
{
  "transaction_id": "tx_boost",
  "amount": 500.0,
  "country": "KP",
  ...
}
```

Cette transaction sera boostée car elle vient d'un pays interdit (mais pas bloquée si le montant est < 1000).

