# 07 — Déploiement Cloud Run (principes)

## Cible

Déployer le moteur de scoring en service HTTP (ex: `POST /score`) sur **Google Cloud Run**.

## Contraintes perf (cibles)

- 500 tx/s (global)
- 300 ms / transaction (objectif p95)

## Stateless vs stateful (important)

Cloud Run scale horizontalement et redémarre des instances :

- le **filesystem** est éphémère (ok pour `/tmp`, pas pour persister l’historique)
- si le moteur dépend d’un historique, il faut :
  - soit recevoir des agrégats en entrée (stateless)
  - soit lire un store externe (ex: PostgreSQL via Cloud SQL) (state externalisé)

> Phase 0 (dev) : historique via `Data/fdata.*` ok en local seulement.

## Chargement des modèles

Pour tenir la latence :

- charger les modèles **au démarrage** du conteneur (pas par requête)
- garder les artefacts dans l’image (ou télécharger au startup depuis un bucket)

## Concurrence

Cloud Run permet plusieurs requêtes simultanées par instance.

Guideline v1 :

- commencer avec une concurrence modérée (ex: 10–50) et mesurer
- ajuster workers/process (selon techno retenue) pour éviter la saturation CPU

## Logs & audit

- logs structurés JSON (Cloud Logging)
- inclure `transaction_id`, `decision`, `risk_score`, `reasons`, `model_version`
- conserver 7 jours (policy à régler côté GCP)

## CI/CD

- build container
- run tests (unit + sanity perf)
- déployer Cloud Run avec un tag de version (aligné avec `model_version`)

