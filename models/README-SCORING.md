# Guide rapide - Scoring de transactions

Ce guide explique comment utiliser les scripts pour scorer des transactions manuellement (phase de développement).

## Prérequis

```bash
# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation rapide

### 1. Ajouter une transaction à l'historique

```bash
# Depuis un fichier JSON
python scripts/push_transaction.py tests/fixtures/example_transaction.json

# Mode interactif
python scripts/push_transaction.py --interactive
```

### 2. Scorer une transaction

```bash
# Depuis un fichier JSON
python scripts/score_transaction.py tests/fixtures/example_transaction.json

# Mode interactif
python scripts/score_transaction.py --interactive

# Sauvegarder la transaction après scoring
python scripts/score_transaction.py transaction.json --save
```

## Format de transaction

Un fichier JSON de transaction doit contenir au minimum :

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

Champs optionnels :
- `country` : Code pays ISO (ex: "FR")
- `city` : Ville
- `description` : Description de la transaction

## Exemples

### Exemple 1 : Transaction normale

```bash
# Créer une transaction simple
cat > transaction.json << EOF
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
EOF

# Scorer la transaction
python scripts/score_transaction.py transaction.json
```

### Exemple 2 : Transaction bloquée (montant trop élevé)

```bash
# Créer une transaction avec montant > 1000 PYC
cat > transaction_blocked.json << EOF
{
  "transaction_id": "tx_blocked",
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

# Scorer - sera bloquée par la règle R1
python scripts/score_transaction.py transaction_blocked.json
```

### Exemple 3 : Créer un historique et scorer

```bash
# Ajouter plusieurs transactions pour créer un historique
python scripts/push_transaction.py tests/fixtures/example_transaction.json

# Scorer une nouvelle transaction (utilisera l'historique)
python scripts/score_transaction.py new_transaction.json --save
```

## Fichiers générés

- `Data/historique.json` : Stockage de l'historique des transactions (créé automatiquement)

## Options avancées

### Spécifier le fichier de stockage

```bash
python scripts/push_transaction.py transaction.json --storage Data/custom_historique.json
python scripts/score_transaction.py transaction.json --storage Data/custom_historique.json
```

### Spécifier les fichiers de configuration

```bash
python scripts/score_transaction.py transaction.json \
  --rules-config src/rules/config/rules_v1.yaml \
  --scoring-config configs/scoring_config.yaml \
  --decision-config configs/scoring_config.yaml
```

## Pipeline de scoring

Le script `score_transaction.py` exécute le pipeline complet :

1. ✅ Charge la transaction
2. ✅ Récupère l'historique depuis le store
3. ✅ Calcule les features (transactionnelles + historiques)
4. ✅ Évalue les règles métier
   - Si `BLOCK` → arrêt immédiat
   - Sinon → continue
5. ✅ Score ML (supervisé + non supervisé) - mock pour l'instant
6. ✅ Calcule le score global avec `boost_factor`
7. ✅ Prend la décision finale (BLOCK/REVIEW/APPROVE)
8. ✅ Affiche le résultat

## Transmission du boost_factor

Le `boost_factor` est calculé par les règles et transmis à travers la pipeline :

- **Règles métier** : Calcule `boost_factor` (1.0 à 2.0)
- **Scorer global** : Applique le boost : `risk_score = (formule) × boost_factor`
- **Décision finale** : Utilise le score boosté

## Documentation complète

Pour plus de détails, voir :
- `docs/13-historique-et-scoring.md` : Documentation complète
- `docs/00-architecture.md` : Architecture du projet
- `docs/03-rules-detailed.md` : Règles métier détaillées

