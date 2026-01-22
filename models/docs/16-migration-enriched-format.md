# 16 — Migration vers le format enrichi

## Vue d'ensemble

Le système a migré vers un format de **transaction enrichie** où toutes les features sont pré-calculées côté backend. Ce document explique les changements et comment migrer.

## Changements principaux

### Avant (format legacy)

```json
{
  "transaction_id": "tx_001",
  "amount": 150.0,
  ...
}
```

- Features calculées côté ML Engine
- Historique récupéré depuis `HistoriqueStore` (fichier local)
- Context calculé dans le script

### Après (format enrichi)

```json
{
  "schema_version": "1.0.0",
  "transaction": { ... },
  "context": { ... },
  "features": {
    "transactional": { ... },
    "historical": { ... }
  }
}
```

- Features pré-calculées côté backend
- Pas de calcul côté ML Engine
- Context inclus dans la transaction

## Scripts mis à jour

### ✅ `score_transaction.py`

- **Détection automatique** : Accepte format enrichi ou simple (legacy)
- **Format enrichi** : Extraction des features pré-calculées
- **Format legacy** : Calcul des features (fallback pour dev)

### ✅ `test_flow.py`

- Utilise uniquement le format enrichi
- Tests avec `enriched_transaction_*.json`

### ⚠️ `push_transaction.py` (LEGACY)

- Conservé pour développement uniquement
- Ne pas utiliser en production

### ⚠️ `historique_store.py` (LEGACY)

- Conservé pour développement uniquement
- Ne pas utiliser en production

## Migration des tests

### Anciens fichiers de test

Les anciens fichiers dans `tests/fixtures/` :
- `test_r1.json`, `test_r2.json`, etc. (format simple)

### Nouveaux fichiers de test

Les nouveaux fichiers dans `tests/fixtures/` :
- `enriched_transaction_example.json` (transaction normale)
- `enriched_transaction_blocked_r1.json` (R1 bloquée)
- `enriched_transaction_boost_r13.json` (R13 boost)
- `enriched_transaction_no_history.json` (0 transaction historique)

## Utilisation

### Format enrichi (recommandé)

```bash
python scripts/score_transaction.py tests/fixtures/enriched_transaction_example.json
```

### Format legacy (dev uniquement)

```bash
python scripts/score_transaction.py tests/fixtures/test_normal.json
```

## Pipeline de features

Le `FeaturePipeline` détecte automatiquement le format :

```python
# Format enrichi
features = pipeline.transform(enriched_transaction, historical_data=None)

# Format legacy
features = pipeline.transform(simple_transaction, historical_data=historical_data)
```

## Règles métier

Les règles fonctionnent avec les deux formats :

- **Format enrichi** : Context extrait depuis `enriched_transaction["context"]`
- **Format legacy** : Context calculé depuis `HistoriqueStore`

## Prochaines étapes

1. ✅ Adapter les scripts pour le format enrichi
2. ✅ Créer les exemples de transactions enrichies
3. ⏳ Mettre à jour la documentation utilisateur
4. ⏳ Supprimer les anciens fichiers de test (optionnel)

