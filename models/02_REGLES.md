# ⚖️ Règles Métier

Guide complet des règles métier appliquées **en amont** du passage dans les modèles ML.

---

## 📋 Vue d'Ensemble

Les règles métier sont des **vérifications déterministes** qui s'exécutent **avant** le scoring ML.

**Objectif** : Détecter des cas évidents de manière **rapide**, **explicable** et **sans ML**.

**Ordre d'exécution** :
```
Transaction
  ↓
1. Règles métier (ce document)
  ├─> Si BLOCK → Arrêt immédiat
  └─> Sinon → Continue
  ↓
2. Scoring ML (si pas BLOCK)
  ↓
3. Décision finale
```

---

## 🚫 Règles Bloquantes (BLOCK)

Ces règles **bloquent immédiatement** la transaction sans passer par l'IA.

### R1 — Montant maximum absolu

**Description** : Bloque toute transaction dépassant un plafond global.

**Logique** :
```
Si amount > 300 PYC → BLOCK
```

**Reason code** : `RULE_MAX_AMOUNT`

**Configuration** : `configs/scoring_config.yaml`

---

### R2 — Solde insuffisant

**Description** : Empêche toute transaction si le wallet source n'a pas assez de fonds.

**Logique** :
```
Si wallet.balance < amount → BLOCK
```

**Reason code** : `RULE_INSUFFICIENT_FUNDS`

**Dépendances** : Accès à `context.source_wallet.balance`

---

### R3 — Wallet bloqué ou utilisateur suspendu

**Description** : Interdit toute transaction si le wallet ou l'utilisateur est bloqué.

**Logique** :
```
Si wallet.status ≠ 'active' → BLOCK
OU
Si user.status ≠ 'active' → BLOCK
```

**Reason code** : `RULE_ACCOUNT_LOCKED`

**Dépendances** : `context.source_wallet.status`, `context.user.status`

---

### R4 — Auto-virement interdit

**Description** : Un utilisateur ne peut pas s'envoyer de l'argent à lui-même.

**Logique** :
```
Si source_wallet_id = destination_wallet_id → BLOCK
```

**Reason code** : `RULE_SELF_TRANSFER`

---

### R5 — Montant nul ou négatif

**Description** : Empêche toute transaction invalide.

**Logique** :
```
Si amount ≤ 0 → BLOCK
```

**Reason code** : `RULE_INVALID_AMOUNT`

---

### R6 — Pays interdit (blacklist)

**Description** : Bloque toute transaction provenant d'un pays explicitement interdit.

**Logique** :
```
Si country IN ['KP', 'IR', 'SY'] → BLOCK
```

**Reason code** : `RULE_COUNTRY_BLOCKED`

**Note** : Si `country` est absent, la règle ne s'applique pas.

---

### R7 — Destination interdite

**Description** : Empêche l'envoi vers un wallet banni.

**Logique** :
```
Si destination_wallet.status ≠ 'active' → BLOCK
```

**Reason code** : `RULE_DESTINATION_LOCKED`

**Dépendances** : `context.destination_wallet.status`

---

## ⚠️ Règles Boost Score (BOOST_SCORE)

Ces règles **ajoutent une pénalité** au score de risque mais laissent passer la transaction à l'IA.

### R8 — Montant inhabituel

**Description** : Détecte les montants extrêmement supérieurs aux habitudes.

**Logique** :
```
Si amount > avg_amount_30d * 10 → BOOST_SCORE (boost +0.3)
Sinon si amount > avg_amount_30d * 5 → BOOST_SCORE (boost +0.2)
```

**Reason code** : `RULE_AMOUNT_ANOMALY`

**Dépendances** : `features.avg_amount_30d` (moyenne des montants sur 30 jours)

---

### R9 — Rafale de transactions

**Description** : Détecte les pics de fréquence extrêmes.

**Logique** :
```
Si tx_last_10min ≥ 20 → BOOST_SCORE (boost +0.3)
Sinon si tx_last_10min ≥ 10 → BOOST_SCORE (boost +0.2)
```

**Reason code** : `RULE_FREQ_SPIKE`

**Dépendances** : `features.tx_last_10min` (nombre de transactions dans les 10 dernières minutes)

---

### R10 — Compte trop récent

**Description** : Détecte les transactions importantes juste après création du compte.

**Logique** :
```
Si account_age_minutes < 5 ET amount > 100 → BOOST_SCORE (boost +0.3)
Sinon si account_age_minutes < 60 ET amount > 50 → BOOST_SCORE (boost +0.2)
```

**Reason code** : `RULE_NEW_ACCOUNT_ACTIVITY`

**Dépendances** : `context.source_wallet.account_age_minutes`

---

## 🔀 Règles Mixtes (BLOCK ou BOOST_SCORE)

Ces règles peuvent être **bloquantes** ou **boost** selon les conditions.

### R11 — Nouveau bénéficiaire + montant élevé

**Description** : Détecte un premier paiement important vers un nouveau wallet.

**Logique** :
```
Si is_new_beneficiary = true ET amount > 200 → BLOCK
Sinon si is_new_beneficiary = true ET amount > 80 → BOOST_SCORE (boost +0.2)
```

**Reason code** : `RULE_NEW_BENEFICIARY`

**Dépendances** : `features.is_new_beneficiary_30d`

---

### R12 — Pays inhabituel

**Description** : Détecte un changement brutal de pays + montant élevé.

**Logique** :
```
Si country NOT IN user_country_history
ET amount > 150 → BLOCK
```

**Reason code** : `RULE_GEO_ANOMALY`

**Dépendances** : `transaction.country`, `features.user_country_history`

---

### R13 — Horaire interdit

**Description** : Détecte les transactions à heures très atypiques + montant élevé.

**Logique** :
```
Si hour BETWEEN 01:00 AND 05:00
ET amount > 120 → BLOCK
Sinon si hour BETWEEN 01:00 AND 05:00
ET amount > 60 → BOOST_SCORE (boost +0.2)
```

**Reason code** : `RULE_ODD_HOUR`

**Dépendances** : Extraction de `hour` depuis `transaction.created_at`

---

### R14 — Profil à risque connu

**Description** : Renforce la sévérité pour les profils déjà à risque.

**Logique** :
```
Si user.risk_level = 'high'
ET amount > 150 → BLOCK
Sinon si user.risk_level = 'high'
ET amount > 50 → BOOST_SCORE (boost +0.2)
```

**Reason code** : `RULE_HIGH_RISK_PROFILE`

**Dépendances** : `context.user.risk_level`

---

### R15 — Récidive récente

**Description** : Détecte si trop d'incidents récents.

**Logique** :
```
Si blocked_tx_last_24h ≥ 3 → BLOCK
Sinon si blocked_tx_last_24h ≥ 1 → BOOST_SCORE (boost +0.2)
```

**Reason code** : `RULE_RECIDIVISM`

**Dépendances** : `features.blocked_tx_last_24h`

---

## ⚙️ Configuration

### Fichier de Configuration

**Fichier** : `src/rules/config/rules_v1.yaml`

**Structure** :
```yaml
rules:
  R1:
    name: "KYC light - Montant max"
    condition:
      field: "amount"
      operator: ">"
      threshold: 300
    action:
      type: "HARD_BLOCK"
      reason: "amount_over_kyc_limit"
```

### Modifier les Règles

**Option 1** : Modifier directement `rules_v1.yaml`

**Option 2** : Utiliser l'API (si disponible)

**Exemple** :
```python
from src.rules.engine import RulesEngine

engine = RulesEngine(config_path=Path("src/rules/config/rules_v1.yaml"))
```

---

## 🔧 Utilisation dans le Pipeline

### Code

**Fichier** : `src/rules/engine.py` → `RulesEngine`

**Exemple** :
```python
from src.rules.engine import RulesEngine

engine = RulesEngine()

# Évaluer les règles
rules_output = engine.evaluate(
    transaction=transaction_dict,
    features=features_dict,
    context=context_dict,
)

# Résultat
if rules_output.decision == "BLOCK":
    return {"decision": "BLOCK", "reasons": rules_output.reasons}

# Sinon, continuer avec le scoring ML
```

### Sortie

```python
@dataclass
class RulesOutput:
    rule_score: float      # [0, 1] - Score des règles
    reasons: List[str]     # Liste des reason_code déclenchés
    hard_block: bool       # True si BLOCK
    decision: str          # "ALLOW", "BOOST_SCORE", "BLOCK"
    boost_factor: float    # Facteur de boost (défaut: 1.0)
```

---

## 📊 Mécanisme BOOST_SCORE

### Comment ça fonctionne

Si une règle BOOST_SCORE est déclenchée :

1. **Calcul du boost_factor** :
   - Chaque règle BOOST ajoute un bonus (ex: +0.2)
   - Plusieurs règles peuvent s'accumuler
   - Cap à 1.0

2. **Application au score final** :
   ```python
   risk_score = (0.2 × rule_score + 0.6 × supervised_score + 0.2 × unsupervised_score) × boost_factor
   ```

**Exemple** :
- Règle R9 déclenchée → `boost_factor = 1.2`
- Score ML = 0.5
- Score final = 0.5 × 1.2 = **0.6** (augmenté)

---

## 📋 Liste Complète des Règles

| Règle | Type | Action | Reason Code |
|-------|------|--------|-------------|
| R1 | BLOCK | Montant > 300 | `RULE_MAX_AMOUNT` |
| R2 | BLOCK | Solde insuffisant | `RULE_INSUFFICIENT_FUNDS` |
| R3 | BLOCK | Wallet/user bloqué | `RULE_ACCOUNT_LOCKED` |
| R4 | BLOCK | Auto-virement | `RULE_SELF_TRANSFER` |
| R5 | BLOCK | Montant ≤ 0 | `RULE_INVALID_AMOUNT` |
| R6 | BLOCK | Pays interdit | `RULE_COUNTRY_BLOCKED` |
| R7 | BLOCK | Destination bloquée | `RULE_DESTINATION_LOCKED` |
| R8 | BOOST | Montant inhabituel | `RULE_AMOUNT_ANOMALY` |
| R9 | BOOST | Rafale transactions | `RULE_FREQ_SPIKE` |
| R10 | BOOST | Compte récent | `RULE_NEW_ACCOUNT_ACTIVITY` |
| R11 | MIXTE | Nouveau bénéficiaire | `RULE_NEW_BENEFICIARY` |
| R12 | MIXTE | Pays inhabituel | `RULE_GEO_ANOMALY` |
| R13 | MIXTE | Horaire interdit | `RULE_ODD_HOUR` |
| R14 | MIXTE | Profil à risque | `RULE_HIGH_RISK_PROFILE` |
| R15 | MIXTE | Récidive | `RULE_RECIDIVISM` |

---

## 🎯 Exemples

### Exemple 1 : Transaction Bloquée (R1)

```json
{
  "transaction": {
    "amount": 500,
    "source_wallet_id": "wallet_001",
    ...
  }
}
```

**Résultat** :
```json
{
  "decision": "BLOCK",
  "reasons": ["RULE_MAX_AMOUNT"],
  "rule_score": 1.0
}
```

**Explication** : Montant (500) > seuil (300) → BLOCK immédiat

---

### Exemple 2 : Transaction avec Boost (R9)

```json
{
  "transaction": {
    "amount": 50,
    "source_wallet_id": "wallet_001",
    ...
  },
  "features": {
    "tx_last_10min": 15
  }
}
```

**Résultat** :
```json
{
  "decision": "ALLOW",
  "reasons": ["RULE_FREQ_SPIKE"],
  "rule_score": 0.3,
  "boost_factor": 1.2
}
```

**Explication** : Rafale détectée (15 tx/10min) → Boost appliqué au score final

---

## 🔍 Pour Aller Plus Loin

### Ordre d'Évaluation

1. **Règles bloquantes** (R1-R7) évaluées en premier
2. Si aucune règle bloquante → **Règles BOOST** (R8-R10)
3. Si aucune règle bloquante → **Règles mixtes** (R11-R15)

**Optimisation** : Arrêt immédiat si une règle bloquante est déclenchée.

### Tests

**Fichier** : `tests/test_rules.py`

**Exécuter** :
```bash
pytest tests/test_rules.py -v
```

---

## ✅ Checklist

- [ ] Comprendre les 15 règles
- [ ] Configurer les seuils dans `rules_v1.yaml`
- [ ] Tester les règles avec des exemples
- [ ] Vérifier les dépendances (features, context)

---

**Besoin de modifier une règle ?** Éditez `src/rules/config/rules_v1.yaml` et redéployez le ML Engine.

