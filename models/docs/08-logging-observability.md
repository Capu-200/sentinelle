# 08 — Logs, observabilité, audit

## Objectifs

- Débogage et monitoring
- Audit minimal : expliquer pourquoi une transaction a été bloquée / revue
- Conservation : 7 jours

## Format de logs (recommandé)

Logs **structurés JSON** par transaction, par exemple :

- `transaction_id`
- `created_at`
- `source_wallet_id`, `destination_wallet_id` (si autorisé)
- `amount`, `currency`, `country`
- `decision`, `risk_score`, `reasons`
- `model_version`
- (optionnel debug) `rule_score`, `s_sup`, `s_unsup`
- `latency_ms`

## Attention aux données sensibles

Tu as indiqué qu’il y aura des données interdites (pas encore listées).

Règle de base v1 :

- ne jamais logger de données personnelles directes
- ne pas logger le payload brut si il peut contenir des PII
- si `metadata.raw_provider_payload` est loggé : le faire **en mode debug** et avec **redaction** (à définir)

## Corrélation

Guideline :

- accepter un `correlation_id` via header/API gateway (plus tard)
- le répercuter dans tous les logs

## Suivi KPI (offline)

Mesures attendues :

- Recall fraude
- Precision sur `BLOCK`
- PR-AUC
- % `BLOCK` / % `REVIEW`
- stabilité des seuils (dérive)

