# 🧪 Exemples JSON avec Historique pour Tests Postman

Le ML Engine n’accepte **qu’un seul format** : la **transaction enrichie** avec `features.transactional` et `features.historical`.

---

## 📋 Format accepté (obligatoire)

Toute requête POST /score doit avoir la forme :

```json
{
  "transaction": {
    "transaction_id": "...",
    "amount": 150.0,
    ...
    "features": {
      "transactional": { ... },
      "historical": { ... }
    }
  },
  "context": { ... }
}
```

- **`transaction.features.transactional`** : montant, log_amount, direction, heure, type, pays, etc.
- **`transaction.features.historical`** : agrégats (counts, montants, is_new_destination, days_since, etc.).
- Pour un **nouveau compte** (sans historique), mettez les champs historiques à 0 / -1.0 / 1 (voir exemples « new user » ci‑dessous).

Sans `features.transactional` et `features.historical`, le service répond **400 Bad Request**.

---

## 🎯 Exemple 1 : Transaction Normale avec Historique

### JSON à Envoyer

```json
{
  "transaction": {
    "transaction_id": "test_normal_hist_001",
    "amount": 75.50,
    "currency": "PYC",
    "source_wallet_id": "wallet_user_123",
    "destination_wallet_id": "wallet_merchant_456",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "description": "Achat en ligne",
    "features": {
      "transactional": {
        "amount": 75.50,
        "log_amount": 4.32,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1,
        "transaction_type_TRANSFER": 1
      },
      "historical": {
        "src_tx_count_out_5m": 0,
        "src_tx_amount_sum_out_5m": 0.0,
        "src_tx_amount_mean_out_5m": 0.0,
        "src_tx_amount_max_out_5m": 0.0,
        "src_unique_destinations_5m": 0,
        "src_tx_count_out_1h": 2,
        "src_tx_amount_sum_out_1h": 150.0,
        "src_tx_amount_mean_out_1h": 75.0,
        "src_tx_amount_max_out_1h": 100.0,
        "src_unique_destinations_1h": 2,
        "src_tx_count_out_24h": 8,
        "src_tx_amount_sum_out_24h": 600.0,
        "src_tx_amount_mean_out_24h": 75.0,
        "src_tx_amount_max_out_24h": 120.0,
        "src_unique_destinations_24h": 3,
        "src_tx_count_out_7d": 45,
        "src_tx_amount_sum_out_7d": 2925.0,
        "src_tx_amount_mean_out_7d": 65.0,
        "src_tx_amount_max_out_7d": 120.0,
        "src_unique_destinations_7d": 8,
        "src_tx_count_out_30d": 180,
        "src_tx_amount_sum_out_30d": 11700.0,
        "src_tx_amount_mean_out_30d": 65.0,
        "src_tx_amount_max_out_30d": 120.0,
        "src_unique_destinations_30d": 15,
        "is_new_destination_24h": 0,
        "is_new_destination_7d": 0,
        "is_new_destination_30d": 0,
        "src_to_dst_tx_count_30d": 5,
        "days_since_last_src_to_dst": 2.5,
        "src_destination_concentration_7d": 0.15,
        "src_destination_entropy_7d": 2.8,
        "is_new_country_30d": 0,
        "country_mismatch": 0,
        "src_failed_count_24h": 0,
        "src_failed_ratio_7d": 0.0
      }
    }
  },
  "context": {
    "source_wallet": {
      "balance": 500.0,
      "status": "active"
    },
    "user": {
      "status": "active",
      "risk_level": "low"
    }
  }
}
```

### Réponse Attendue

```json
{
  "risk_score": 0.15,
  "decision": "APPROVE",
  "reasons": [],
  "model_version": "1.0.0-test"
}
```

**Interprétation** :
- ✅ Historique normal (2 transactions/heure, moyenne 65€)
- ✅ Bénéficiaire connu (5 transactions précédentes)
- ✅ Score faible → APPROVE

---

## ⚠️ Exemple 2 : Transaction Suspecte avec Historique

### JSON à Envoyer

```json
{
  "transaction": {
    "transaction_id": "test_suspect_hist_001",
    "amount": 250.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_suspect_001",
    "destination_wallet_id": "wallet_new_999",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "description": "Transaction suspecte",
    "features": {
      "transactional": {
        "amount": 250.0,
        "log_amount": 5.52,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1,
        "transaction_type_TRANSFER": 1
      },
      "historical": {
        "src_tx_count_out_5m": 5,
        "src_tx_count_out_1h": 25,
        "src_tx_count_out_24h": 120,
        "src_tx_count_out_7d": 350,
        "src_tx_amount_sum_out_1h": 5000.0,
        "src_tx_amount_mean_out_7d": 50.0,
        "src_tx_amount_max_out_7d": 100.0,
        "src_unique_destinations_24h": 50,
        "is_new_destination_30d": 1,
        "src_to_dst_tx_count_30d": 0,
        "days_since_last_src_to_dst": -1.0,
        "src_destination_concentration_7d": 0.02,
        "src_destination_entropy_7d": 5.2,
        "is_new_country_30d": 0,
        "country_mismatch": 0,
        "src_failed_count_24h": 5,
        "src_failed_ratio_7d": 0.15
      }
    }
  },
  "context": {
    "source_wallet": {
      "balance": 500.0,
      "status": "active"
    },
    "user": {
      "status": "active",
      "risk_level": "medium"
    }
  }
}
```

### Réponse Attendue

```json
{
  "risk_score": 0.72,
  "decision": "REVIEW",
  "reasons": ["RULE_HIGH_VELOCITY"],
  "model_version": "1.0.0-test"
}
```

**Interprétation** :
- ⚠️ **Vélocité très élevée** : 25 transactions/heure, 5 dans les 5 dernières minutes
- ⚠️ **Nouveau bénéficiaire** : `is_new_destination_30d: 1`
- ⚠️ **Montant inhabituel** : 250€ vs moyenne de 50€
- ⚠️ **Score élevé** → REVIEW

---

## 🚫 Exemple 3 : Transaction Bloquée (Règle + Historique Suspect)

### JSON à Envoyer

```json
{
  "transaction": {
    "transaction_id": "test_blocked_hist_001",
    "amount": 350.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_blocked_001",
    "destination_wallet_id": "wallet_dest_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "description": "Transaction bloquée",
    "features": {
      "transactional": {
        "amount": 350.0,
        "log_amount": 5.86,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1,
        "transaction_type_TRANSFER": 1
      },
      "historical": {
        "src_tx_count_out_5m": 10,
        "src_tx_count_out_1h": 50,
        "src_tx_count_out_24h": 200,
        "src_tx_count_out_7d": 800,
        "src_tx_amount_sum_out_1h": 15000.0,
        "src_tx_amount_mean_out_7d": 30.0,
        "src_tx_amount_max_out_7d": 80.0,
        "src_unique_destinations_24h": 100,
        "is_new_destination_30d": 1,
        "src_to_dst_tx_count_30d": 0,
        "days_since_last_src_to_dst": -1.0,
        "src_destination_concentration_7d": 0.01,
        "src_destination_entropy_7d": 6.5,
        "is_new_country_30d": 1,
        "country_mismatch": 1,
        "src_failed_count_24h": 20,
        "src_failed_ratio_7d": 0.25
      }
    }
  },
  "context": {
    "source_wallet": {
      "balance": 100.0,
      "status": "active"
    },
    "user": {
      "status": "active",
      "risk_level": "high"
    }
  }
}
```

### Réponse Attendue

```json
{
  "risk_score": 1.0,
  "decision": "BLOCK",
  "reasons": ["RULE_MAX_AMOUNT"],
  "model_version": "1.0.0-test"
}
```

**Interprétation** :
- 🚫 **Montant > 300** → Règle R1 déclenchée
- 🚫 **BLOCK immédiat** (même avec historique suspect)
- 🚫 **Score = 1.0** (hard block)

---

## 📊 Liste Complète des Features Historiques

### Features Temporelles (par fenêtre)

| Feature | Description | Exemple Valeur |
|---------|-------------|----------------|
| `src_tx_count_out_5m` | Nombre de transactions sortantes (5 min) | 0-10 |
| `src_tx_count_out_1h` | Nombre de transactions sortantes (1h) | 0-50 |
| `src_tx_count_out_24h` | Nombre de transactions sortantes (24h) | 0-200 |
| `src_tx_count_out_7d` | Nombre de transactions sortantes (7j) | 0-1000 |
| `src_tx_amount_sum_out_1h` | Somme des montants sortants (1h) | 0.0-10000.0 |
| `src_tx_amount_mean_out_7d` | Moyenne des montants sortants (7j) | 0.0-500.0 |
| `src_tx_amount_max_out_7d` | Maximum des montants sortants (7j) | 0.0-1000.0 |
| `src_unique_destinations_24h` | Nombre de destinataires uniques (24h) | 0-100 |

### Features Relationnelles

| Feature | Description | Exemple Valeur |
|---------|-------------|----------------|
| `is_new_destination_30d` | Nouveau bénéficiaire (30j) | 0 ou 1 |
| `src_to_dst_tx_count_30d` | Nombre de transactions vers ce bénéficiaire (30j) | 0-100 |
| `days_since_last_src_to_dst` | Jours depuis dernière transaction vers ce bénéficiaire | -1.0 (jamais) ou 0.0-30.0 |

### Features de Dispersion

| Feature | Description | Exemple Valeur |
|---------|-------------|----------------|
| `src_destination_concentration_7d` | Concentration des destinataires (7j) | 0.0-1.0 |
| `src_destination_entropy_7d` | Entropie des destinataires (7j) | 0.0-7.0 |

### Features de Localisation

| Feature | Description | Exemple Valeur |
|---------|-------------|----------------|
| `is_new_country_30d` | Nouveau pays (30j) | 0 ou 1 |
| `country_mismatch` | Pays différent de l'habitude | 0 ou 1 |

### Features de Statut

| Feature | Description | Exemple Valeur |
|---------|-------------|----------------|
| `src_failed_count_24h` | Nombre de transactions échouées (24h) | 0-50 |
| `src_failed_ratio_7d` | Ratio de transactions échouées (7j) | 0.0-1.0 |

---

## 🎯 Exemple 4 : Transaction avec Historique Vide (Nouveau Compte)

### JSON à Envoyer

```json
{
  "transaction": {
    "transaction_id": "test_new_account_001",
    "amount": 100.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_new_001",
    "destination_wallet_id": "wallet_dest_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "features": {
      "transactional": {
        "amount": 100.0,
        "log_amount": 4.61,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1
      },
      "historical": {
        "src_tx_count_out_5m": 0,
        "src_tx_count_out_1h": 0,
        "src_tx_count_out_24h": 0,
        "src_tx_count_out_7d": 0,
        "src_tx_amount_sum_out_1h": 0.0,
        "src_tx_amount_mean_out_7d": 0.0,
        "src_tx_amount_max_out_7d": 0.0,
        "src_unique_destinations_24h": 0,
        "is_new_destination_30d": 1,
        "src_to_dst_tx_count_30d": 0,
        "days_since_last_src_to_dst": -1.0,
        "src_destination_concentration_7d": 0.0,
        "src_destination_entropy_7d": 0.0,
        "is_new_country_30d": 1,
        "country_mismatch": 0,
        "src_failed_count_24h": 0,
        "src_failed_ratio_7d": 0.0
      }
    }
  }
}
```

### Réponse Attendue

```json
{
  "risk_score": 0.35,
  "decision": "APPROVE",
  "reasons": [],
  "model_version": "1.0.0-test"
}
```

**Interprétation** :
- ⚠️ **Nouveau compte** : Pas d'historique
- ⚠️ **Score modéré** : Nouveau compte = risque modéré
- ✅ **APPROVE** : Mais pourrait être REVIEW selon le montant

---

## ✅ Checklist pour Tester

Avant d'envoyer la requête :

- [ ] ✅ Format JSON valide
- [ ] ✅ `features.transactional` présent
- [ ] ✅ `features.historical` présent
- [ ] ✅ Toutes les features historiques incluses (ou null si pas d'historique)
- [ ] ✅ Valeurs cohérentes (ex: `src_tx_count_out_1h` ≥ `src_tx_count_out_5m`)

---

## 🎯 Scénarios de Test Recommandés

1. ✅ **Transaction normale** : Historique régulier, bénéficiaire connu
2. ⚠️ **Transaction suspecte** : Vélocité élevée, nouveau bénéficiaire
3. 🚫 **Transaction bloquée** : Montant > 300 (règle)
4. 📊 **Nouveau compte** : Historique vide
5. 🔍 **Montant inhabituel** : 250€ vs moyenne 50€

---

## 💡 Notes Importantes

1. **Le ML Engine détecte automatiquement** le format enrichi (ligne 70 de `pipeline.py`)
2. **Si `features` présent** → Extrait les features pré-calculées
3. **Si `features` absent** → Calcule depuis transaction uniquement (legacy)
4. **Valeurs null** : Utilisez `-1.0` pour "jamais" (ex: `days_since_last_src_to_dst`)
5. **Valeurs par défaut** : `0` pour counts, `0.0` pour amounts, `false` pour booléens

---

## 🚀 C'est Prêt !

Copiez les exemples ci-dessus dans Postman et testez ! Les scores devraient être **beaucoup plus réalistes** avec l'historique. 🎉

