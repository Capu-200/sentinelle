# 01 — Requirements & décisions (v1)

## But

Construire un moteur de scoring de fraude bancaire qui, pour **1 transaction**, retourne :

- `risk_score` \(\[0,1\]\)
- `decision` ∈ {`APPROVE`, `REVIEW`, `BLOCK`}
- `reasons` : explications minimales (règles / signaux)
- `model_version` : version de modèle (SemVer)

La décision est prise **avant exécution finale** de la transaction.

## Périmètre

- **Inclut**
  - Feature engineering (profil comportemental “à l’instant T”)
  - Règles métier R1→R4 (explicables)
  - Modèle supervisé (PaySim fraud 0/1)
  - Modèle non supervisé (anomalies)
  - Score global & décision
  - Évaluation (Recall, Precision, PR-AUC, % bloquées, % review)
  - Service ML prêt à être branché plus tard via API (Cloud Run)
- **Exclut**
  - Front
  - Gestion Kafka (mais compatible event-driven)
  - DB métier (mais connexion possible plus tard)

## Contraintes non fonctionnelles

- **Latence max** : 300 ms / transaction (objectif p95)
- **Débit cible** : 500 transactions / seconde
- **Modèles** : tabulaire, légers (pas de DL lourd)
- **Logs** : conservés 7 jours (Cloud Logging)
- **Données** : pas de données personnelles directes (focus transactionnel)

## Décisions déjà actées

- **Devise v1** : unique fictive `PYC` (Payon Coin)
- **Idempotence** : gérée en amont (bus / API), **pas** dans le moteur ML
- **Type v1** : opérationnellement, tout est **P2P** en v1 (on garde `transaction_type` pour compat future)
- **Explications** : raisons **fixes** (liste finie, stable) pour audit
- **Logs** : “log tout ce que tu peux” → logs structurés JSON (voir `docs/08-logging-observability.md`)

## État & historique (phases)

Le scoring a besoin de features comportementales basées sur l’historique.

### Phase 0 (local / démo)

- Historique stocké en **fichier** `Data/fdata.(json|csv)` (simple, dev-only).
- ⚠️ Non adapté à Cloud Run à grande échelle (filesystem éphémère / concurrence).

### Phase 1 (prod)

- Historique et agrégats fournis par une source persistante.
- Option recommandée : **Cloud SQL for PostgreSQL** (ou service PostgreSQL managé) accessible depuis Cloud Run.
- Le moteur ML reste **indépendant** : il ne “dépend” pas du back, mais peut consommer un store technique (read-only / feature store) si nécessaire.

## ML — logique globale

Le score global combine 3 briques :

1. **Règles métier** → `rule_score` + `reasons`
2. **Supervisé** (PaySim) → `S_sup`
3. **Non supervisé** (anomalies) → `S_unsup`

Formule cible :

\[
S\_{global} = 0.2 \times rule\_score + 0.6 \times S\_{sup} + 0.2 \times S\_{unsup}
\]

Décision :

- `BLOCK` si très suspect
- `REVIEW` si doute
- `APPROVE` sinon

Les seuils sont réglés par volume (ex: top 0,1% bloqués).

