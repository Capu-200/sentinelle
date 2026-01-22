# 06 — Score global, seuils & décision

## Score global

On combine 3 signaux :

- `rule_score` : score des règles (explicable, déterministe)
- `s_sup` : proba fraude supervisée
- `s_unsup` : anomalie calibrée

Formule v1 :

\[
risk\_score = clamp\_{0,1}\big(0.2 \times rule\_score + 0.6 \times s\_{sup} + 0.2 \times s\_{unsup}\big)
\]

## Priorité aux règles (hard block)

Certaines règles sont “hard” et **forcent** `BLOCK` même si le ML est bas :

- ex: `amount_over_kyc_limit`
- ex: `sanctioned_country`

Dans ce cas :

- `decision = BLOCK`
- `risk_score` peut rester calculé normalement (ou forcé à 1.0 selon choix d’implémentation)

## Seuils de décision

### Politique (recommandée)

Les seuils ne sont pas “au feeling”.  
Ils sont fixés pour contrôler le **volume** :

- `BLOCK` = top **0,1%** des scores
- `REVIEW` = top **1%** (incluant les `BLOCK`)
- le reste `APPROVE`

Ces pourcentages sont ajustables (selon charge ops).

### Comment calculer les seuils (offline)

Sur un set de validation (split temporel) :

- `threshold_block = quantile(risk_score, 0.999)`
- `threshold_review = quantile(risk_score, 0.990)`

Puis on vérifie :

- Recall fraude
- Precision sur `BLOCK`
- PR-AUC
- % `BLOCK` / % `REVIEW`

Les seuils calculés deviennent une **config** versionnée avec `model_version`.

## Raisons (reasons)

La réponse `reasons` est l’union :

- des règles déclenchées (ids stables)
- de quelques signaux ML simples si disponibles (ex: `amount_unusual`, `high_velocity`)

> v1 : priorité aux raisons “règles”, car 100% explicables.

