# 15 — Utilisation de la transaction enrichie

## Vue d'ensemble

La transaction enrichie est le format JSON standardisé reçu par le moteur ML. Elle contient :
- La transaction de base
- Le contexte enrichi (wallet/user)
- Les features pré-calculées

## Schéma JSON

Le schéma formel est disponible dans :
- `schemas/enriched_transaction.schema.json`

## Exemples

### Transaction normale

```bash
# Voir l'exemple complet
cat tests/fixtures/enriched_transaction_example.json
```

### Transaction bloquée (R1)

```bash
# Transaction avec montant > 300 PYC
cat tests/fixtures/enriched_transaction_blocked_r1.json
```

### Transaction avec boost (R13)

```bash
# Transaction à heure interdite (03:00 UTC) avec montant > 60
cat tests/fixtures/enriched_transaction_boost_r13.json
```

## Structure

### 1. `transaction` (obligatoire)

Transaction de base conforme à `schemas/transaction.schema.json`.

### 2. `context` (obligatoire)

Contexte enrichi pour les règles :
- `source_wallet` : balance, status, account_age_minutes
- `destination_wallet` : status
- `user` : status, risk_level

### 3. `features` (obligatoire)

Features pré-calculées :
- `transactional` : Features extraites de la transaction
- `historical` : Agrégats historiques pré-calculés

### 4. `schema_version` (obligatoire)

Version du schéma (ex: "1.0.0")

## Validation

Pour valider une transaction enrichie contre le schéma :

```python
import json
import jsonschema

# Charger le schéma
with open('schemas/enriched_transaction.schema.json') as f:
    schema = json.load(f)

# Charger la transaction
with open('tests/fixtures/enriched_transaction_example.json') as f:
    transaction = json.load(f)

# Valider
jsonschema.validate(transaction, schema)
```

## Migration depuis transaction simple

### Avant (transaction simple)

```json
{
  "transaction_id": "tx_001",
  "amount": 150.0,
  ...
}
```

### Après (transaction enrichie)

```json
{
  "schema_version": "1.0.0",
  "transaction": {
    "transaction_id": "tx_001",
    "amount": 150.0,
    ...
  },
  "context": { ... },
  "features": { ... }
}
```

## Calcul des features (côté backend)

Les features doivent être calculées côté backend avant l'envoi au ML Engine :

### Features transactionnelles

```python
features["transactional"] = {
    "amount": transaction["amount"],
    "log_amount": math.log(1 + transaction["amount"]),
    "currency_is_pyc": transaction["currency"] == "PYC",
    "direction_outgoing": 1 if transaction["direction"] == "outgoing" else 0,
    "hour_of_day": datetime.fromisoformat(transaction["created_at"]).hour,
    "day_of_week": datetime.fromisoformat(transaction["created_at"]).weekday(),
    # ... encodage one-hot pour transaction_type et country
}
```

### Features historiques

```sql
-- Exemple SQL pour avg_amount_30d
SELECT AVG(amount) as avg_amount_30d
FROM banking.transactions
WHERE source_wallet_id = :source_wallet_id
  AND created_at >= NOW() - INTERVAL '30 days'
  AND created_at < :transaction_created_at
  AND status = 'SUCCESS';
```

## Utilisation dans le ML Engine

Le ML Engine extrait simplement les features :

```python
# Dans aggregator.py (futur)
def extract_historical_features(enriched_transaction):
    return enriched_transaction["features"]["historical"]

# Dans extractor.py (futur)
def extract_transactional_features(enriched_transaction):
    return enriched_transaction["features"]["transactional"]
```

## Gestion des valeurs manquantes

Les features historiques peuvent être `null` si :
- Pas d'historique disponible (nouveau compte)
- Fenêtre temporelle vide
- Données non disponibles

Le ML Engine doit gérer ces cas :
- `null` → valeur par défaut (0, false, [])
- Ignorer la feature si nécessaire

## Performance

- **Taille typique** : ~2-5 KB par transaction enrichie
- **Latence backend** : < 100ms pour calculer les features
- **Latence ML** : < 200ms pour scorer (objectif total < 300ms)

## Versioning

Le champ `schema_version` permet :
- Évolution du schéma sans casser la compatibilité
- Support de plusieurs versions en parallèle
- Migration progressive

Format : SemVer (ex: "1.0.0", "1.1.0", "2.0.0")

