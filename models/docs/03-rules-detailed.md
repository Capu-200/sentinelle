# 03 — Règles métier détaillées

## Objectif

Détecter des cas évidents de manière **déterministe**, **rapide** et **explicable**, même sans ML.

Chaque transaction passe par :
1. un moteur de règles "hard"
2. puis l'IA (si elle n'a pas été bloquée)

## Résultats possibles des règles

- `ALLOW` → passe à l'IA
- `BOOST_SCORE` → passe à l'IA avec pénalité (ex : boost score trust_score)
- `BLOCK` → refus immédiat

## Convention "reason_code"

- **Format** : `RULE_*` en UPPER_SNAKE_CASE, stable dans le temps
- **Exemples** : `RULE_MAX_AMOUNT`, `RULE_INSUFFICIENT_FUNDS`, `RULE_AMOUNT_ANOMALY`

---

## Règles bloquantes (BLOCK)

Ces règles bloquent immédiatement la transaction sans passer par l'IA.

### R1 — Montant maximum absolu

**Description**

Bloque toute transaction dépassant un plafond global.

**Logique**

```
Si amount > MAX_TX_AMOUNT → BLOCK
```

**Seuil**

- `MAX_TX_AMOUNT = 300 PYC`

**Reason_code**

- `RULE_MAX_AMOUNT`

**Notes**

🎯 Empêche les abus grossiers et les erreurs utilisateurs.

---

### R2 — Solde insuffisant

**Description**

Empêche toute transaction si le wallet source n'a pas assez de fonds.

**Logique**

```
Si wallet.balance < amount → BLOCK
```

**Reason_code**

- `RULE_INSUFFICIENT_FUNDS`

**Dépendances**

- Accès à `wallet.balance` (wallet source)

---

### R3 — Wallet bloqué ou utilisateur suspendu

**Description**

Interdire toute transaction si le wallet ou l'utilisateur est bloqué.

**Logique**

```
Si wallets.status ≠ 'active' → BLOCK
OU
Si profiles.status ≠ 'active' → BLOCK
```

**Reason_code**

- `RULE_ACCOUNT_LOCKED`

**Dépendances**

- Accès à `wallets.status` (wallet source)
- Accès à `profiles.status` (utilisateur initiateur)

**Valeurs de status attendues**

- `'active'` → autorisé
- Autre valeur → bloqué

---

### R4 — Auto-virement interdit

**Description**

Un utilisateur ne peut pas s'envoyer de l'argent à lui-même.

**Logique**

```
Si source_wallet_id = destination_wallet_id → BLOCK
```

**Reason_code**

- `RULE_SELF_TRANSFER`

**Dépendances**

- Aucune (données dans la transaction)

---

### R5 — Montant nul ou négatif

**Description**

Empêche toute transaction invalide.

**Logique**

```
Si amount ≤ 0 → BLOCK
```

**Reason_code**

- `RULE_INVALID_AMOUNT`

**Dépendances**

- Aucune (données dans la transaction)

---

### R6 — Pays interdit (blacklist)

**Description**

Bloque toute transaction provenant d'un pays explicitement interdit.

**Exemples**

- pays sous sanctions
- pays "test" interdits dans le MVP
- pays non supportés

**Logique**

```
Si country IN ['KP','IR','SY','RU_TEST'] → BLOCK
```

**Reason_code**

- `RULE_COUNTRY_BLOCKED`

**Dépendances**

- Champ `country` dans la transaction (optionnel)

**Note**

Si `country` est absent, la règle ne s'applique pas (pas de blocage par défaut).

---

### R7 — Destination interdite

**Description**

Empêche l'envoi vers un wallet banni.

**Logique**

```
Si destination_wallet.status ≠ 'active' → BLOCK
```

**Reason_code**

- `RULE_DESTINATION_LOCKED`

**Dépendances**

- Accès à `destination_wallet.status`

---

## Règles Boost score (BOOST_SCORE)

Ces règles ajoutent une pénalité au score de risque mais laissent passer la transaction à l'IA.

### R8 — Montant inhabituel (hard seuil)

**Description**

Détecte les montants extrêmement supérieurs aux habitudes.

**Logique**

```
Si amount > avg_amount_30d * 10 → BOOST_SCORE
Sinon si amount > avg_amount_30d * 5 → BOOST_SCORE
```

**Reason_code**

- `RULE_AMOUNT_ANOMALY`

**Dépendances**

- Calcul de `avg_amount_30d` (moyenne des montants sur 30 jours pour le wallet source)

**Note**

Si `avg_amount_30d` n'existe pas (nouveau compte), à définir (ignorer la règle ou utiliser un seuil par défaut).

---

### R9 — Rafale de transactions

**Description**

Détecte les pics de fréquence extrêmes.

**Logique**

```
Si tx_last_10min ≥ 20 → BOOST_SCORE
Sinon si tx_last_10min ≥ 10 → BOOST_SCORE
```

**Reason_code**

- `RULE_FREQ_SPIKE`

**Dépendances**

- Calcul de `tx_last_10min` (nombre de transactions sortantes du wallet source dans les 10 dernières minutes)

---

### R10 — Compte trop récent

**Description**

Détecte les transactions importantes juste après création du compte.

**Logique**

```
Si account_age_minutes < 5 ET amount > 100 → BOOST_SCORE
Sinon si account_age_minutes < 60 ET amount > 50 → BOOST_SCORE
```

**Reason_code**

- `RULE_NEW_ACCOUNT_ACTIVITY`

**Dépendances**

- Calcul de `account_age_minutes` (différence entre `created_at` de la transaction et `created_at` du wallet/compte)

---

### R11 — Nouveau bénéficiaire + montant élevé

**Description**

Détecte un premier paiement important vers un nouveau wallet.

**Logique**

```
Si is_new_beneficiary = true ET amount > 200 → BLOCK
Sinon si is_new_beneficiary = true ET amount > 80 → BOOST_SCORE
```

**Reason_code**

- `RULE_NEW_BENEFICIARY`

**Dépendances**

- Calcul de `is_new_beneficiary` (le wallet destination n'a jamais été utilisé par le wallet source, ou pas dans les X derniers jours)

**Note**

Cette règle peut être bloquante (BLOCK) ou boost (BOOST_SCORE) selon le montant.

---

### R12 — Pays inhabituel (hard)

**Description**

Détecte un changement brutal de pays + montant élevé.

**Logique**

```
Si country NOT IN user_country_history
ET amount > 150 → BLOCK
```

**Reason_code**

- `RULE_GEO_ANOMALY`

**Dépendances**

- Champ `country` dans la transaction
- Calcul de `user_country_history` (liste des pays utilisés par l'utilisateur/wallet source sur une période donnée)

**Note**

Cette règle est bloquante (BLOCK) si le montant est élevé.

---

### R13 — Horaire interdit

**Description**

Détecte les transactions à heures très atypiques + montant élevé.

**Logique**

```
Si hour BETWEEN 01:00 AND 05:00
ET amount > 120 → BLOCK
Sinon si hour BETWEEN 01:00 AND 05:00
ET amount > 60 → BOOST_SCORE
```

**Reason_code**

- `RULE_ODD_HOUR`

**Dépendances**

- Extraction de `hour` depuis `created_at` (fuseau horaire à définir)

**Note**

Cette règle peut être bloquante (BLOCK) ou boost (BOOST_SCORE) selon le montant.

---

### R14 — Profil à risque connu

**Description**

Renforce la sévérité pour les profils déjà à risque.

**Logique**

```
Si profiles.risk_level = 'high'
ET amount > 50 → BOOST_SCORE
Si profiles.risk_level = 'high'
ET amount > 150 → BLOCK
```

**Reason_code**

- `RULE_HIGH_RISK_PROFILE`

**Dépendances**

- Accès à `profiles.risk_level` (utilisateur initiateur)

**Valeurs de risk_level attendues**

- `'high'` → déclenche la règle
- Autres valeurs (`'low'`, `'medium'`, etc.) → pas de déclenchement

**Note**

Cette règle peut être bloquante (BLOCK) ou boost (BOOST_SCORE) selon le montant.

---

### R15 — Récidive récente

**Description**

Détecte si trop d'incidents récents.

**Logique**

```
Si blocked_tx_last_24h ≥ 3 → BLOCK
Sinon si blocked_tx_last_24h ≥ 1 → BOOST_SCORE
```

**Reason_code**

- `RULE_RECIDIVISM`

**Dépendances**

- Calcul de `blocked_tx_last_24h` (nombre de transactions bloquées dans les 24 dernières heures pour le wallet source)

**Note**

Cette règle peut être bloquante (BLOCK) ou boost (BOOST_SCORE) selon le nombre d'incidents.

---

## Implémentation technique

### Ordre d'évaluation

**Recommandation :**

1. Évaluer d'abord toutes les règles bloquantes (R1-R7, R11-BLOCK, R12-BLOCK, R13-BLOCK, R14-BLOCK, R15-BLOCK)
2. Si aucune règle bloquante n'est déclenchée, évaluer les règles BOOST_SCORE (R8-R10, R11-BOOST, R13-BOOST, R14-BOOST, R15-BOOST)
3. Si une règle bloquante est déclenchée, retourner immédiatement `BLOCK` sans évaluer les autres règles

### Mécanisme BOOST_SCORE

**À définir :**

- Comment appliquer le boost au score final ?
- Comment combiner plusieurs boosts si plusieurs règles sont déclenchées ?

**Options proposées :**

1. Ajouter un bonus fixe au `rule_score` (ex: +0.2 par règle, cap à 1.0)
2. Multiplier le `risk_score` final par un facteur (ex: ×1.2)
3. Ajouter un bonus au `risk_score` avant la décision finale

### Sortie du moteur de règles

Le moteur de règles retourne :

```python
@dataclass
class RulesOutput:
    decision: str  # ALLOW, BOOST_SCORE, BLOCK
    reason_codes: List[str]  # Liste des reason_code déclenchés
    rule_score: float  # [0, 1] - score des règles
    boost_factor: float  # Facteur de boost si BOOST_SCORE (défaut: 1.0)
```

---

## Questions ouvertes

Voir le document `03-rules-questions.md` pour les questions de clarification nécessaires avant l'implémentation.

