# ML Payon — Fraud Scoring Engine (Cloud Run-ready)

Ce dépôt contient la **documentation de référence** et (à terme) le code du moteur de scoring de fraude bancaire Payon.

## Objectif

Analyser **chaque transaction intra-wallet** en temps quasi réel et produire :

- un **score de risque** \(0 → 1\)
- une **décision** : `APPROVE`, `REVIEW`, `BLOCK`
- une **explication minimale** : liste de règles / signaux déclenchés

Le moteur est conçu pour être :

- **indépendant du back** et **indépendant de la DB métier**
- **consommable via API** (déploiement cible : **Google Cloud Run**)
- **compatible event-driven** (ex : Kafka) — *sans gérer Kafka dans ce repo*

## Sortie attendue (contrat)

Exemple :

```json
{
  "risk_score": 0.83,
  "decision": "BLOCK",
  "reasons": ["amount_over_kyc_limit", "sanctioned_country", "high_velocity"],
  "model_version": "v1.0.0"
}
```

## Documentation (source de vérité)

- `docs/01-requirements-and-decisions.md` — périmètre, contraintes, hypothèses v1
- `docs/02-api-contract.md` — contrat JSON (entrée / sortie) + exemples
- `docs/03-rules.md` — règles R1→R4 (v1 proposées, à ajuster)
- `docs/04-feature-engineering.md` — features comportementales + fenêtres temporelles
- `docs/05-models.md` — modèles supervisé / non supervisé (choix & entraînement)
- `docs/06-scoring-thresholds.md` — score global, décisions, calibration, tuning
- `docs/07-cloud-run.md` — principes de déploiement Cloud Run & contraintes perf
- `docs/08-logging-observability.md` — logs (7 jours), audit, traçabilité
- `docs/09-open-questions.md` — points restant à trancher (liste courte)
- `docs/10-data-training-evaluation.md` — données, split temporel, KPI, seuils
- `docs/11-security-privacy.md` — baseline sécurité & données interdites
- `docs/12-data-preparation.md` — cleaning, anti-leakage, préparation entraînement

## Schémas JSON

- `schemas/transaction.schema.json` — schéma d’entrée (transaction)
- `schemas/decision.schema.json` — schéma de sortie (décision de scoring)

## Données locales (dev)

- `Data/README.md` — datasets présents (`Data/raw/*.csv`) + conventions

