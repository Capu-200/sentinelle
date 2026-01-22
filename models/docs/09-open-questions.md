# 09 — Points à trancher (open questions)

Cette liste est volontairement courte : ce sont les seuls points où tu as répondu “je sais pas / on verra”.

## Produit

- **Types de transaction** : v1 opérationnellement P2P uniquement, ou réellement “tous les types” ?
- **Priorité KPI** : tu préfères optimiser **Recall fraude** ou **Precision sur BLOCK** si on doit choisir ?

## Règles R1→R4 (définitives)

- Fournir la version finale des règles (conditions + seuils + reason ids).
- Valider si certaines règles doivent forcer `BLOCK` (hard rules) — v1 : oui (KYC light, pays interdit).

## Historique / features comportementales

- **Fenêtres exactes** : on part sur `5m`, `1h`, `24h`, `7d` (et `30d` pour nouveauté destinataire) — OK ?
- **Clés exactes** : profil sur `source_wallet_id` seulement, ou aussi `destination_wallet_id` + paire source→dest ?
- **Stockage prod** : Cloud Run + PostgreSQL : confirmer l’option **Cloud SQL for PostgreSQL** (recommandée) vs autre.
- **Mode stateless** : veut-on accepter un champ `context` (agrégats déjà calculés en amont) pour scaler plus facilement ?

## Modèles & entraînement

- **Choix final** : LightGBM vs XGBoost (v1 recommandé : LightGBM).
- **Calibration** : veut-on calibrer le score final en proba (isotonic / Platt) ou rester sur la somme pondérée ?

## Data “interdite”

- Liste précise des champs / sources interdites à ingérer ou logger (ex: IP brute, GPS précis, device fingerprint, etc.)

