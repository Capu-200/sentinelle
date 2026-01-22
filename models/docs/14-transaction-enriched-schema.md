# 14 — Schéma de transaction enrichie

## Principe

La transaction enrichie est la structure JSON complète reçue par le moteur ML. Elle contient :
1. **Transaction de base** : données brutes de la transaction
2. **Contexte enrichi** : informations wallet/user nécessaires pour les règles
3. **Features pré-calculées** : agrégats historiques et features comportementales

**Objectif** : Minimiser la logique côté ML, tout est pré-calculé en amont.

---

## Structure proposée

```json
{
  // ========== TRANSACTION DE BASE ==========
  "transaction": {
    "transaction_id": "tx_001",
    "provider": "wallet_provider_1",
    "provider_tx_id": "wp_tx_12345",
    "initiator_user_id": "user_123",
    "source_wallet_id": "wallet_src_456",
    "destination_wallet_id": "wallet_dst_789",
    "amount": 150.0,
    "currency": "PYC",
    "transaction_type": "P2P",
    "direction": "outgoing",
    "status": "PENDING",
    "reason_code": null,
    "created_at": "2026-01-21T12:00:00Z",
    "provider_created_at": "2026-01-21T12:00:01Z",
    "executed_at": null,
    "country": "FR",
    "city": "Paris",
    "description": "Paiement restaurant",
    "metadata": {
      "raw_provider_payload": { ... }
    }
  },

  // ========== CONTEXTE ENRICHI (pour les règles) ==========
  "context": {
    // Wallet source
    "source_wallet": {
      "wallet_id": "wallet_src_456",
      "balance": 1000.0,
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z",
      "account_age_minutes": 525600.0  // Calculé : temps depuis created_at
    },

    // Wallet destination
    "destination_wallet": {
      "wallet_id": "wallet_dst_789",
      "status": "active",
      "created_at": "2025-06-01T00:00:00Z"
    },

    // Utilisateur initiateur
    "user": {
      "user_id": "user_123",
      "status": "active",
      "risk_level": "low",  // "low", "medium", "high"
      "created_at": "2024-12-01T00:00:00Z"
    }
  },

  // ========== FEATURES PRÉ-CALCULÉES ==========
  "features": {
    // Features transactionnelles (calculées depuis la transaction)
    "transactional": {
      "amount": 150.0,
      "log_amount": 5.01,
      "currency_is_pyc": true,
      "direction_outgoing": 1,
      "direction_incoming": 0,
      "transaction_type_p2p": 1,
      "transaction_type_merchant": 0,
      "transaction_type_cashin": 0,
      "transaction_type_cashout": 0,
      "hour_of_day": 12,
      "day_of_week": 2,  // 0=lundi, 6=dimanche
      "country_fr": 1,
      "country_be": 0
    },

    // Features historiques (agrégats pré-calculés)
    "historical": {
      // Pour les règles R8, R9, R11, R12, R15
      "avg_amount_30d": 85.5,  // R8
      "tx_last_10min": 3,      // R9
      "is_new_beneficiary": false,  // R11 (nouveau bénéficiaire dans les 30 derniers jours)
      "user_country_history": ["FR", "BE", "DE"],  // R12 (pays utilisés dans les 30 derniers jours)
      "blocked_tx_last_24h": 0,  // R15 (transactions bloquées dans les 24h)

      // Profil wallet source (fenêtres temporelles)
      "src_tx_count_out_5m": 0,
      "src_tx_count_out_1h": 2,
      "src_tx_count_out_24h": 15,
      "src_tx_count_out_7d": 45,
      "src_tx_amount_sum_out_1h": 200.0,
      "src_tx_amount_mean_out_1h": 100.0,
      "src_tx_amount_max_out_1h": 150.0,
      "src_unique_destinations_7d": 8,

      // Relation source → destination
      "is_new_destination_24h": false,
      "is_new_destination_7d": false,
      "is_new_destination_30d": true,
      "src_to_dst_tx_count_30d": 0,
      "days_since_last_src_to_dst": null,

      // Dispersion/concentration
      "src_destination_concentration_7d": 0.35,  // Part du top-1 destinataire
      "src_destination_entropy_7d": 2.1,

      // Localisation
      "is_new_country_30d": false,
      "country_mismatch": false,

      // Statuts/échecs
      "src_failed_count_24h": 0,
      "src_failed_ratio_7d": 0.02
    }
  }
}
```

---

## Détails des sections

### 1. `transaction` (transaction de base)

Structure identique à la transaction de base fournie. Pas de modification.

### 2. `context` (contexte enrichi)

**Objectif** : Fournir les données nécessaires pour les règles R2, R3, R7, R10, R14.

**Champs requis** :
- `source_wallet.balance` → R2 (solde insuffisant)
- `source_wallet.status` → R3 (wallet bloqué)
- `user.status` → R3 (utilisateur suspendu)
- `destination_wallet.status` → R7 (destination interdite)
- `source_wallet.account_age_minutes` → R10 (compte trop récent)
- `user.risk_level` → R14 (profil à risque)

**Calcul côté backend** :
- `account_age_minutes` = `(transaction.created_at - source_wallet.created_at).total_seconds() / 60`

### 3. `features` (features pré-calculées)

#### 3.1 `features.transactional`

**Objectif** : Features directement extraites de la transaction (pas d'historique).

**Calcul côté backend** :
- `log_amount = log(1 + amount)`
- `currency_is_pyc = (currency == "PYC")`
- `direction_outgoing = (direction == "outgoing") ? 1 : 0`
- `hour_of_day = extract_hour(created_at)`
- `day_of_week = extract_day_of_week(created_at)`
- Encodage one-hot pour `transaction_type` et `country`

#### 3.2 `features.historical`

**Objectif** : Agrégats historiques pré-calculés pour les règles et les modèles ML.

**Features pour les règles** :
- `avg_amount_30d` : Moyenne des montants sur 30 jours (R8)
- `tx_last_10min` : Nombre de transactions dans les 10 dernières minutes (R9)
- `is_new_beneficiary` : Nouveau bénéficiaire dans les 30 derniers jours (R11)
- `user_country_history` : Liste des pays utilisés dans les 30 derniers jours (R12)
- `blocked_tx_last_24h` : Nombre de transactions bloquées dans les 24h (R15)

**Features pour les modèles ML** :
- Profil wallet source (fenêtres 5m, 1h, 24h, 7d)
- Relation source → destination
- Dispersion/concentration
- Localisation
- Statuts/échecs

**Calcul côté backend** :
- Requêtes SQL sur `banking.transactions`
- Agrégats calculés AVANT l'envoi au moteur ML
- Fenêtres temporelles basées sur `created_at` (event-time)

---

## Avantages de cette structure

### ✅ Minimise la logique côté ML

Le moteur ML reçoit tout pré-calculé :
- Pas de requêtes SQL
- Pas de calculs d'agrégats
- Pas de parsing de dates
- Juste extraction et scoring

### ✅ Performance optimale

- Latence < 300ms garantie (pas de calculs lourds)
- Débit élevé (500 tx/s)
- Cache possible côté backend

### ✅ Séparation des responsabilités

- **Backend** : Enrichissement, agrégats, contexte
- **ML Engine** : Scoring uniquement

### ✅ Évolutivité

- Ajout de nouvelles features sans modifier le code ML
- Versioning des features via schémas JSON
- Compatible avec Feature Store

---

## Exemple complet

```json
{
  "transaction": {
    "transaction_id": "tx_001",
    "initiator_user_id": "user_123",
    "source_wallet_id": "wallet_src_456",
    "destination_wallet_id": "wallet_dst_789",
    "amount": 350.0,
    "currency": "PYC",
    "transaction_type": "P2P",
    "direction": "outgoing",
    "created_at": "2026-01-21T12:00:00Z",
    "country": "KP"
  },
  "context": {
    "source_wallet": {
      "wallet_id": "wallet_src_456",
      "balance": 1000.0,
      "status": "active",
      "created_at": "2025-01-01T00:00:00Z",
      "account_age_minutes": 525600.0
    },
    "destination_wallet": {
      "wallet_id": "wallet_dst_789",
      "status": "active"
    },
    "user": {
      "user_id": "user_123",
      "status": "active",
      "risk_level": "low"
    }
  },
  "features": {
    "transactional": {
      "amount": 350.0,
      "log_amount": 5.86,
      "currency_is_pyc": true,
      "direction_outgoing": 1,
      "hour_of_day": 12,
      "day_of_week": 2
    },
    "historical": {
      "avg_amount_30d": 85.5,
      "tx_last_10min": 3,
      "is_new_beneficiary": false,
      "user_country_history": ["FR", "BE"],
      "blocked_tx_last_24h": 0,
      "src_tx_count_out_1h": 2,
      "src_tx_amount_mean_out_1h": 100.0
    }
  }
}
```

---

## Migration depuis l'architecture actuelle

### Phase actuelle (dev)

Le script `score_transaction.py` :
1. Reçoit transaction de base
2. Récupère historique depuis `HistoriqueStore`
3. Calcule features dans `aggregator.py`
4. Calcule contexte dans le script

### Phase future (prod)

Le backend :
1. Reçoit transaction de base
2. Enrichit avec contexte (wallet/user)
3. Calcule features historiques (SQL)
4. Envoie transaction enrichie au ML Engine

**Modification du ML Engine** :
- `aggregator.py` : Extraire `features.historical` au lieu de calculer
- `extractor.py` : Extraire `features.transactional` au lieu de calculer
- `score_transaction.py` : Extraire `context` au lieu de récupérer depuis store

---

## Gestion du cas 0 transaction historique

**Important** : La transaction enrichie peut avoir **0, 1, 2 ou plus** de transactions dans l'historique côté DB.

### Cas 0 transaction (nouveau compte)

Quand il n'y a **aucune transaction historique** :
- Toutes les features historiques doivent être `null`
- Le backend doit retourner `null` pour toutes les features historiques
- Le ML Engine doit gérer ces `null` avec des valeurs par défaut

**Exemple** :
```json
{
  "features": {
    "historical": {
      "avg_amount_30d": null,
      "tx_last_10min": null,
      "is_new_beneficiary": null,
      "user_country_history": null,
      "blocked_tx_last_24h": null,
      "src_tx_count_out_1h": null,
      ...
    }
  }
}
```

### Cas 1+ transactions

Quand il y a des transactions historiques :
- Les features sont calculées normalement
- Les valeurs peuvent être 0 (ex: `tx_last_10min: 0` si aucune transaction dans les 10 dernières minutes)
- Les listes peuvent être vides (ex: `user_country_history: []`)

**Distinction importante** :
- `null` = pas d'historique disponible (nouveau compte)
- `0` ou `[]` = historique disponible mais valeur nulle (pas de transactions dans la fenêtre)

## Questions à trancher

1. **Historique brut** : Inclure `historical_transactions` (liste brute) ou seulement les features pré-calculées ?
   - **Recommandation** : Seulement les features (plus léger, plus rapide)

2. **Fenêtres temporelles** : Quelles fenêtres exactes sont nécessaires ?
   - **Recommandation** : `5m`, `1h`, `24h`, `7d`, `30d` (comme dans la doc)

3. **Features optionnelles** : Que faire si certaines features ne sont pas disponibles ?
   - **Recommandation** : `null` pour nouveau compte, `0`/`false`/`[]` pour fenêtre vide

4. **Versioning** : Comment versionner la structure enrichie ?
   - **Recommandation** : Champ `schema_version` à la racine

---

## Prochaines étapes

1. ✅ Valider cette structure avec l'équipe backend
2. ✅ Créer le schéma JSON (`schemas/enriched_transaction.schema.json`)
3. ✅ Adapter `aggregator.py` pour extraire au lieu de calculer
4. ✅ Adapter `extractor.py` pour extraire au lieu de calculer
5. ✅ Tester avec des transactions enrichies mockées

