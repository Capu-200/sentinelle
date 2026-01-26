# 🎯 Explication des Seuils de Décision

## 📖 Qu'est-ce qu'un Seuil ?

Un **seuil** est un **score minimum** que doit atteindre une transaction pour être classée dans une catégorie.

### Exemple Simple

Imaginez que vous avez un système de notation de 0 à 100 :

- **Score < 50** → ✅ **APPROVE** (transaction approuvée)
- **Score ≥ 50 et < 80** → ⚠️ **REVIEW** (nécessite une revue humaine)
- **Score ≥ 80** → 🚫 **BLOCK** (transaction bloquée)

Ici, les seuils sont :
- `REVIEW threshold = 50`
- `BLOCK threshold = 80`

---

## 🎯 Dans Notre Système

### Les 3 Décisions Possibles

1. **APPROVE** : Transaction normale, approuvée automatiquement
2. **REVIEW** : Transaction suspecte, nécessite une revue humaine
3. **BLOCK** : Transaction très suspecte, bloquée automatiquement

### Comment ça Marche ?

Quand une transaction arrive :

1. **On calcule le score global** (combinaison de règles + ML supervisé + ML non supervisé)
2. **On compare le score aux seuils** :
   - Si `score ≥ BLOCK threshold` → **BLOCK** 🚫
   - Sinon si `score ≥ REVIEW threshold` → **REVIEW** ⚠️
   - Sinon → **APPROVE** ✅

---

## 📊 Calcul des Seuils (Politique)

Les seuils ne sont **pas fixés arbitrairement**. Ils sont calculés pour **contrôler le volume** :

### Politique Recommandée

- **BLOCK** = Top **0.1%** des scores les plus élevés
- **REVIEW** = Top **1%** des scores les plus élevés (incluant les BLOCK)

### Pourquoi ?

- Si on bloque trop → Beaucoup de faux positifs (transactions normales bloquées)
- Si on bloque trop peu → Des fraudes passent
- On ajuste selon la charge opérationnelle (combien de transactions peuvent être reviewées)

### Exemple avec 10 000 Transactions

- **BLOCK** = Top 0.1% = **10 transactions** les plus suspectes
- **REVIEW** = Top 1% = **100 transactions** les plus suspectes (incluant les 10 BLOCK)

---

## ⚠️ Problème Actuel : Seuils Identiques

### Pourquoi BLOCK et REVIEW sont Identiques ?

Avec un **dataset de validation très petit** (30k transactions) :

- **BLOCK threshold** = quantile 0.999 = transaction #29970 (environ)
- **REVIEW threshold** = quantile 0.99 = transaction #29700 (environ)

Si les scores sont **très similaires** dans cette zone (ex: beaucoup de transactions avec le même score), les deux quantiles peuvent donner **la même valeur**.

### Exemple Concret

```
Scores sur validation set (triés du plus élevé au plus bas) :
- Transaction #1 : score = 0.95
- Transaction #2 : score = 0.92
- ...
- Transaction #29700 : score = 0.5907  ← REVIEW threshold
- Transaction #29701 : score = 0.5907
- ...
- Transaction #29970 : score = 0.5907  ← BLOCK threshold
- Transaction #29971 : score = 0.5906
```

Si beaucoup de transactions ont le même score (0.5907), les quantiles 0.99 et 0.999 peuvent pointer vers la même valeur.

---

## 🔧 Solutions

### Solution 1 : Calculer sur le Score Global (Recommandé)

Actuellement, on calcule les seuils sur le **score supervisé uniquement**, alors qu'en production on utilise un **score global** qui combine :
- Règles (20%)
- Supervisé (60%)
- Non supervisé (20%)

**Correction** : Calculer les seuils sur le **score global** pour être cohérent avec la production.

### Solution 2 : Ajuster les Quantiles

Si le dataset est très petit, on peut :
- Utiliser des quantiles plus espacés (ex: 0.995 pour BLOCK, 0.99 pour REVIEW)
- Ou utiliser des valeurs absolues (ex: top 10 transactions pour BLOCK)

### Solution 3 : Utiliser un Dataset Plus Grand

Avec plus de données, les quantiles seront plus précis et différenciés.

---

## 💡 Résumé

**Seuil = Score minimum pour une décision**

- **BLOCK threshold** : Score minimum pour bloquer (top 0.1%)
- **REVIEW threshold** : Score minimum pour revue (top 1%)

**Problème actuel** : Avec un dataset petit (30k), les quantiles 0.999 et 0.99 peuvent donner la même valeur si les scores sont similaires.

**Solution** : Calculer les seuils sur le score global (comme en production) plutôt que sur le score supervisé uniquement.

