# 02 — Contrat API (entrée / sortie)

## Objectif

Définir un contrat stable pour appeler le moteur de scoring (Cloud Run plus tard).

## Endpoint cible (proposé)

- `POST /score`
- 1 requête = 1 transaction
- Idempotence gérée en amont (API/bus), donc pas de `idempotency_key` ici.

## Entrée — `Transaction`

### Champs (v1)

#### Identifiants & interconnexion
- `transaction_id` (string, requis) : id unique interne
- `provider` (string, optionnel) : système de paiement
- `provider_tx_id` (string|null, optionnel) : id transaction fournisseur (peut être null)

#### Acteurs & wallets
- `initiator_user_id` (string, requis)
- `source_wallet_id` (string, requis)
- `destination_wallet_id` (string, requis)

#### Données financières
- `amount` (number, requis) : valeur positive
- `currency` (string, requis) : v1 attend `PYC`

#### Type & sens
- `transaction_type` (string, requis) : `P2P` \(`MERCHANT`, `CASHIN`, `CASHOUT` conservés pour futur\)
- `direction` (string, requis) : `outgoing` | `incoming`

#### Statut & erreurs (optionnels pour scoring “pré-exécution”)
- `status` (string, optionnel) : `PENDING` | `SUCCESS` | `FAILED` | `CANCELED`
- `reason_code` (string, optionnel)

#### Timestamps
- `created_at` (string datetime ISO-8601, requis) : timestamp événement (action utilisateur)
- `provider_created_at` (string datetime ISO-8601|null, optionnel)
- `executed_at` (string datetime ISO-8601|null, optionnel)

#### Localisation
- `country` (string, optionnel) : code ISO (ex: `FR`)
- `city` (string, optionnel)

#### Confort
- `description` (string, optionnel)

#### Métadonnées techniques
- `metadata` (object, optionnel)
  - `raw_provider_payload` (object, optionnel) : payload brut fournisseur

### Exemple de requête

```json
{
  "transaction_id": "tx_01JASQ5NQ0Z2H1",
  "provider": "payon_wallet",
  "provider_tx_id": null,
  "initiator_user_id": "user_123",
  "source_wallet_id": "w_src_456",
  "destination_wallet_id": "w_dst_789",
  "amount": 42.5,
  "currency": "PYC",
  "transaction_type": "P2P",
  "direction": "outgoing",
  "status": "PENDING",
  "reason_code": null,
  "created_at": "2026-01-21T12:34:56Z",
  "provider_created_at": null,
  "executed_at": null,
  "country": "FR",
  "city": "Paris",
  "description": "remboursement",
  "metadata": {
    "raw_provider_payload": {
      "foo": "bar"
    }
  }
}
```

## Sortie — `FraudDecision`

### Champs (v1)

- `risk_score` (number) : \[0,1\]
- `decision` (string) : `APPROVE` | `REVIEW` | `BLOCK`
- `reasons` (array[string]) : liste de raisons **stables** (ids techniques)
- `model_version` (string) : ex `v1.0.0`

> Option debug (recommandé, contrôlé par config/env) : retourner aussi `rule_score`, `S_sup`, `S_unsup`.

### Exemple de réponse

```json
{
  "risk_score": 0.83,
  "decision": "BLOCK",
  "reasons": [
    "amount_over_kyc_limit",
    "sanctioned_country",
    "high_velocity"
  ],
  "model_version": "v1.0.0"
}
```

## Schémas

- Schéma d’entrée : `schemas/transaction.schema.json`
- Schéma de sortie : `schemas/decision.schema.json`

