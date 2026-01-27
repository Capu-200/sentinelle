# ✅ JSON Complet avec Toutes les 50 Features

Guide pour créer un JSON avec **toutes les 50 features** attendues par le modèle.

---

## 📋 Liste Complète des 50 Features

D'après `feature_schema.json`, le modèle attend exactement **50 features** :

### Features Transactionnelles (14)

1. `amount`
2. `log_amount`
3. `currency_is_pyc`
4. `direction_outgoing`
5. `direction_incoming`
6. `transaction_type_p2p`
7. `transaction_type_merchant`
8. `transaction_type_cashin`
9. `transaction_type_cashout`
10. `hour_of_day`
11. `day_of_week`
12. `country_fr`
13. `country_be`
14. `country_kp`

### Features Historiques (36)

**Par fenêtre temporelle (5m, 1h, 24h, 7d, 30d)** :
- `src_tx_count_out_{window}`
- `src_tx_amount_sum_out_{window}` (sauf 5m, 24h, 7d, 30d - seulement 1h)
- `src_tx_amount_mean_out_{window}` (sauf 5m, 24h, 7d, 30d - seulement 1h)
- `src_tx_amount_max_out_{window}` (sauf 5m, 24h, 7d, 30d - seulement 1h)
- `src_unique_destinations_{window}`

**Relationnelles** :
- `is_new_destination_24h`
- `is_new_destination_7d`
- `is_new_destination_30d`
- `src_to_dst_tx_count_30d`
- `days_since_last_src_to_dst`

**Dispersion** :
- `src_destination_concentration_7d`
- `src_destination_entropy_7d`

**Localisation** :
- `is_new_country_30d`
- `country_mismatch`

**Statuts** :
- `src_failed_count_24h`
- `src_failed_ratio_7d`

---

## 🎯 JSON Complet (50 Features)

### Exemple à Copier-Coller

```json
{
  "transaction": {
    "transaction_id": "test_complete_001",
    "amount": 250.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_suspect_001",
    "destination_wallet_id": "wallet_new_999",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "features": {
      "transactional": {
        "amount": 250.0,
        "log_amount": 5.52,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "direction_incoming": 0,
        "transaction_type_p2p": 0,
        "transaction_type_merchant": 0,
        "transaction_type_cashin": 0,
        "transaction_type_cashout": 0,
        "hour_of_day": 14,
        "day_of_week": 1,
        "country_fr": 1,
        "country_be": 0,
        "country_kp": 0
      },
      "historical": {
        "src_tx_count_out_5m": 5,
        "src_tx_amount_sum_out_5m": 500.0,
        "src_tx_amount_mean_out_5m": 100.0,
        "src_tx_amount_max_out_5m": 150.0,
        "src_unique_destinations_5m": 3,
        "src_tx_count_out_1h": 25,
        "src_tx_amount_sum_out_1h": 5000.0,
        "src_tx_amount_mean_out_1h": 200.0,
        "src_tx_amount_max_out_1h": 300.0,
        "src_unique_destinations_1h": 10,
        "src_tx_count_out_24h": 120,
        "src_tx_amount_sum_out_24h": 24000.0,
        "src_tx_amount_mean_out_24h": 200.0,
        "src_tx_amount_max_out_24h": 300.0,
        "src_unique_destinations_24h": 50,
        "src_tx_count_out_7d": 350,
        "src_tx_amount_sum_out_7d": 70000.0,
        "src_tx_amount_mean_out_7d": 200.0,
        "src_tx_amount_max_out_7d": 300.0,
        "src_unique_destinations_7d": 100,
        "src_tx_count_out_30d": 1200,
        "src_tx_amount_sum_out_30d": 240000.0,
        "src_tx_amount_mean_out_30d": 200.0,
        "src_tx_amount_max_out_30d": 300.0,
        "src_unique_destinations_30d": 200,
        "is_new_destination_24h": 1,
        "is_new_destination_7d": 1,
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
  }
}
```

---

## ⚠️ Note Importante

**Le ML Engine complète automatiquement les features manquantes** avec des valeurs par défaut, mais il est **recommandé** d'inclure toutes les features dans le JSON pour :
- ✅ Meilleure performance
- ✅ Scores plus précis
- ✅ Éviter les erreurs

---

## 🔧 Correction Appliquée

Le ML Engine a été mis à jour pour :
1. ✅ **Détecter les features manquantes**
2. ✅ **Les compléter avec des valeurs par défaut**
3. ✅ **Réordonner selon l'ordre attendu par le modèle**

**Vous pouvez maintenant envoyer un JSON avec seulement les features disponibles**, le système complétera automatiquement les manquantes.

---

## 📝 Checklist

Avant d'envoyer le JSON :

- [ ] ✅ Toutes les features transactionnelles présentes (14)
- [ ] ✅ Toutes les features historiques présentes (36)
- [ ] ✅ Valeurs cohérentes (ex: `src_tx_count_out_1h` ≥ `src_tx_count_out_5m`)
- [ ] ✅ Features one-hot : exactement 1 à 1, les autres à 0

---

## 🚀 Test Rapide

Copiez le JSON ci-dessus dans Postman et testez ! Le système devrait maintenant fonctionner même si certaines features manquent.

