# 04 — Feature engineering (profil comportemental)

## Principe

Le modèle ne score pas uniquement la transaction courante.  
On enrichit chaque transaction avec un **profil comportemental** des wallets **au moment T**.

Techniquement : **1 transaction = 1 ligne de features enrichies** (tabulaire), pas une séquence brute.

## Les 2 notions qui te manquaient

### “Fenêtres temporelles” (windows)

Ce sont des intervalles de temps servant à calculer des agrégats “récents”, par exemple :

- dernières **5 minutes** (`5m`)
- dernière **1 heure** (`1h`)
- dernières **24 heures** (`24h`)
- derniers **7 jours** (`7d`)
- (optionnel) **30 jours** (`30d`)

Exemple : `tx_count_out_1h` = nombre de transactions sortantes du wallet source dans la dernière heure.

### “Clés d’historique”

Ce sont les entités sur lesquelles on calcule ces agrégats.

En v1, on recommande au minimum :

- **Wallet source** : `source_wallet_id` (profil “émetteur”)
- **Wallet destination** : `destination_wallet_id` (profil “bénéficiaire”)
- **Paire source→dest** : (`source_wallet_id`, `destination_wallet_id`) (relation)
- **Utilisateur initiateur** : `initiator_user_id` (si utile)

> Plus tard, on pourra ajouter `device_id`, `ip_hash`, `merchant_id` si ces champs existent, mais ils ne sont pas dans le contrat v1.

## Hypothèse event-time

Les features sont calculées à partir de `created_at` (event-time) et **ne doivent pas inclure** la transaction courante.

## Features proposées (v1)

> Cette liste sert de base “cohérente” avec les règles et les modèles. Elle pourra être réduite/étendue.

### A) Features transactionnelles (1 ligne)

- `amount`
- `log_amount` = log(1 + amount)
- `currency_is_pyc` (bool) — v1 attend `PYC`
- `direction` (one-hot)
- `transaction_type` (one-hot, même si v1 opérationnellement P2P)
- `hour_of_day`, `day_of_week`
- `country` (one-hot ou hashing) si fourni

### B) Profil wallet source (agrégats)

Pour chaque fenêtre W ∈ {`5m`, `1h`, `24h`, `7d`} :

- `src_tx_count_out_W`
- `src_tx_amount_sum_out_W`
- `src_tx_amount_mean_out_W`
- `src_tx_amount_max_out_W`
- `src_unique_destinations_W`

### C) Relation source → destination (nouveauté / répétition)

- `is_new_destination_24h` / `is_new_destination_7d` / `is_new_destination_30d`
- `src_to_dst_tx_count_30d`
- `days_since_last_src_to_dst` (si historique disponible)

### D) Dispersion / concentration des destinataires

- `src_destination_concentration_7d` (ex: part du top-1 destinataire)
- `src_destination_entropy_7d` (optionnel, si on veut mesurer la dispersion)

### E) Localisation (si disponible)

- `is_new_country_30d` (pour le wallet source)
- `country_mismatch` (si on a une “country habituelle”)

### F) Statuts & échecs (si exploitable avant exécution)

Selon les événements dispo, on peut utiliser l’historique de `FAILED/CANCELED` :

- `src_failed_count_24h`
- `src_failed_ratio_7d`

## Source de données historique (phases)

### Phase 0 — fichier local (dev)

- Historique stocké dans `Data/fdata.json` ou `Data/fdata.csv` (ou dans `Data/raw/*.csv` selon les datasets)
- Rejeu simple pour construire les agrégats

### Phase 1 — PostgreSQL (prod)

- Stockage persistant des transactions/agrégats
- Le moteur ML lit les agrégats nécessaires (ou bien reçoit un “context” pré-calculé en entrée).

## Performance (guideline)

Pour tenir 300 ms :

- pré-calculer/mettre en cache des agrégats si possible
- limiter les features coûteuses (ex: entropie) si elles dégradent la latence
- garder les modèles chargés en mémoire (pas de reload par requête)

