# 17 — Architecture de production et gestion de la concurrence

## Utilité de `historique.json` en production

### ❌ En production : **PAS UTILE**

Avec le **format enrichi**, le fichier `historique.json` n'est **plus nécessaire** en production car :

1. **Features pré-calculées** : Les features historiques sont calculées côté backend et incluses dans la transaction enrichie
2. **Stateless** : Le ML Engine est stateless (pas de stockage local)
3. **Performance** : Pas de lecture fichier/DB côté ML (latence < 300ms)

### ✅ En développement : **UTILE**

Le fichier `historique.json` reste utile **uniquement** pour :
- Tests locaux sans backend
- Développement des features
- Validation du pipeline

**Conclusion** : `historique.json` est **dev-only**, pas utilisé en production.

---

## Gestion de la concurrence : plusieurs transactions simultanées

### Architecture Cloud Run (stateless)

**Principe** : Chaque transaction est traitée **indépendamment** et de manière **stateless**.

```
┌─────────────────────────────────────────────────────────┐
│                    Event Bus (Kafka)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Event 1 │  │  Event 2 │  │  Event 3 │  ...         │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (API Gateway)                      │
│  - Enrichit chaque transaction                          │
│  - Calcule les features historiques (SQL)               │
│  - Envoie transaction enrichie au ML Engine            │
└─────────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│              Google Cloud Run (ML Engine)               │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Instance 1  │  │  Instance 2  │  │  Instance 3  │ │
│  │              │  │              │  │              │ │
│  │  Req 1 ──────┼──┼──> Req 4     │  │              │ │
│  │  Req 2       │  │  Req 5       │  │  Req 7       │ │
│  │  Req 3       │  │  Req 6       │  │  Req 8       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  Chaque instance peut traiter plusieurs requêtes        │
│  simultanément (concurrence configurable)               │
└─────────────────────────────────────────────────────────┘
```

### Comment ça fonctionne

#### 1. Kafka / Event Bus

**Rôle** : Distribuer les événements de transaction

- **Pas de batch** : Chaque transaction = 1 événement Kafka
- **Partitioning** : Peut partitionner par `wallet_id` pour garantir l'ordre si nécessaire
- **Découpage** : Kafka gère automatiquement la distribution aux consumers

**Exemple** :
```
Topic: transactions
Partition 0: [tx_001, tx_004, tx_007] (wallet_001)
Partition 1: [tx_002, tx_005, tx_008] (wallet_002)
Partition 2: [tx_003, tx_006, tx_009] (wallet_003)
```

#### 2. Backend (API Gateway)

**Rôle** : Enrichir chaque transaction

- **Reçoit** : 1 événement Kafka = 1 transaction simple
- **Enrichit** : 
  - Récupère contexte (wallet, user) depuis DB
  - Calcule features historiques (requêtes SQL)
  - Construit transaction enrichie
- **Envoie** : 1 requête HTTP au ML Engine (Cloud Run)

**Important** : Le backend peut traiter plusieurs transactions en parallèle (threads/async)

#### 3. Cloud Run (ML Engine)

**Rôle** : Scorer chaque transaction enrichie

- **Stateless** : Chaque requête est indépendante
- **Auto-scaling** : Cloud Run crée/supprime des instances selon la charge
- **Concurrence par instance** : Chaque instance peut traiter plusieurs requêtes simultanément

**Configuration Cloud Run** :
```yaml
concurrency: 10  # 10 requêtes simultanées par instance
min_instances: 1
max_instances: 100
cpu: 2
memory: 2Gi
```

### Exemple concret : 100 transactions simultanées

```
Kafka → 100 événements distribués
  ↓
Backend → 100 requêtes HTTP parallèles au ML Engine
  ↓
Cloud Run → Auto-scale à 10 instances
  ↓
Chaque instance traite 10 requêtes en parallèle
  ↓
100 transactions scorées en ~300ms (p95)
```

### Pas besoin de batch

**Pourquoi pas de batch ?**

1. **Latence** : Chaque transaction doit être scorée en < 300ms
2. **Indépendance** : Chaque transaction est indépendante (pas de dépendance entre elles)
3. **Stateless** : Le ML Engine ne garde pas d'état entre transactions
4. **Auto-scaling** : Cloud Run gère automatiquement la montée en charge

**Quand utiliser des batches ?**

- **Entraînement** : Pour traiter de grandes quantités de données
- **Batch scoring** : Pour scorer des datasets historiques
- **Pas pour l'inference en temps réel** : Chaque transaction doit être traitée individuellement

---

## Architecture recommandée

### Flux de production

```
1. Transaction créée → Event Kafka
2. Backend consomme l'event
3. Backend enrichit (DB queries pour features historiques)
4. Backend envoie transaction enrichie → Cloud Run ML Engine
5. ML Engine score et retourne la décision
6. Backend reçoit la décision et continue le workflow
```

### Points clés

1. **Stateless ML Engine** : Pas de stockage local, pas de `historique.json`
2. **Features pré-calculées** : Tout est dans la transaction enrichie
3. **Auto-scaling** : Cloud Run gère la montée en charge
4. **Concurrence** : Gérée par Cloud Run (plusieurs instances + plusieurs requêtes/instance)
5. **Pas de batch** : Chaque transaction est traitée individuellement

---

## Gestion des cas limites

### Cas 1 : Transactions simultanées du même wallet

**Problème potentiel** : Deux transactions du même wallet en même temps

**Solution** :
- Les features historiques sont calculées **avant** l'envoi au ML Engine
- Le backend utilise un **snapshot** de l'historique au moment T
- Les transactions sont traitées indépendamment (pas de race condition)

**Exemple** :
```
T0: Transaction A créée → Backend calcule features (historique jusqu'à T0)
T0+1ms: Transaction B créée → Backend calcule features (historique jusqu'à T0+1ms)
→ Les deux transactions sont scorées avec leur propre snapshot
```

### Cas 2 : Pic de charge (1000 tx/s)

**Solution** :
- Cloud Run auto-scale jusqu'à `max_instances`
- Backend peut utiliser un pool de connexions DB
- Features historiques peuvent être mises en cache (Redis) si nécessaire

### Cas 3 : Latence DB (calcul features historiques)

**Solution** :
- Backend peut mettre en cache les features historiques (Redis)
- Cache avec TTL court (ex: 1 minute)
- Invalidation à chaque nouvelle transaction

---

## Résumé

| Aspect | Réponse |
|--------|---------|
| **`historique.json` en prod** | ❌ Pas utile (features pré-calculées) |
| **`historique.json` en dev** | ✅ Utile (tests locaux) |
| **Gestion concurrence** | Cloud Run auto-scaling + concurrence par instance |
| **Batches nécessaires ?** | ❌ Non, chaque transaction individuellement |
| **Kafka batches ?** | ❌ Non, 1 event = 1 transaction |
| **Stateless** | ✅ Oui, pas de stockage local |
| **Features historiques** | ✅ Pré-calculées côté backend |

---

## Prochaines étapes

1. ✅ Format enrichi implémenté (stateless)
2. ⏳ Backend à implémenter (enrichissement + calcul features)
3. ⏳ API Cloud Run à créer (FastAPI endpoint `/score`)
4. ⏳ Configuration Cloud Run (concurrence, scaling)

