# 🔄 Flux de Données - Enrichissement des Virements

## 📊 Diagramme de Flux

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CRÉATION D'UN VIREMENT                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Utilisateur │
│   (Frontend) │
└──────┬───────┘
       │
       │ 1. Remplit le formulaire
       │    - Destinataire
       │    - Montant
       │    - Commentaire (optionnel) ← NOUVEAU
       │
       ▼
┌──────────────────────┐
│  TransferForm.tsx    │
│  (Client Component)  │
└──────┬───────────────┘
       │
       │ 2. Soumet le formulaire (FormData)
       │    - recipient
       │    - amount
       │    - comment ← NOUVEAU
       │
       ▼
┌──────────────────────────┐
│  createTransferAction    │
│  (Server Action)         │
└──────┬───────────────────┘
       │
       │ 3. Prépare le payload
       │    {
       │      amount: 150,
       │      recipient_email: "...",
       │      comment: "Remboursement...", ← NOUVEAU
       │      country: "FR"
       │    }
       │
       ▼
┌──────────────────────────┐
│  POST /transactions      │
│  (Backend API)           │
└──────┬───────────────────┘
       │
       │ 4. Enrichit la transaction
       │    - Détermine destination_country depuis IBAN/profil
       │    - Stocke le commentaire
       │    - Envoie à Kafka pour analyse ML
       │
       ▼
┌──────────────────────────┐
│  Base de Données         │
│  (PostgreSQL)            │
└──────┬───────────────────┘
       │
       │ 5. Transaction créée avec:
       │    - source_country: "FR"
       │    - destination_country: "ES"
       │    - comment: "Remboursement..."
       │
       ▼
┌──────────────────────────┐
│  Kafka Topic             │
│  (ML Analysis)           │
└──────┬───────────────────┘
       │
       │ 6. Analyse ML (async)
       │
       ▼
┌──────────────────────────┐
│  WebSocket / Polling     │
│  (Real-time update)      │
└──────┬───────────────────┘
       │
       │ 7. Mise à jour du statut
       │    PENDING → VALIDATED
       │
       ▼
┌──────────────────────────┐
│  ActivityList.tsx        │
│  (Client Component)      │
└──────┬───────────────────┘
       │
       │ 8. Affiche la transaction enrichie
       │    - 🇫🇷 → 🇪🇸
       │    - "Remboursement..."
       │
       ▼
┌──────────────┐
│  Utilisateur │
│  voit le     │
│  résultat    │
└──────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    AJOUT/MODIFICATION DE COMMENTAIRE                    │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Utilisateur │
│   (Frontend) │
└──────┬───────┘
       │
       │ 1. Clique sur "Ajouter note" ou "Modifier note"
       │
       ▼
┌──────────────────────────┐
│  AddCommentButton.tsx    │
│  (Client Component)      │
└──────┬───────────────────┘
       │
       │ 2. Ouvre le modal
       │    - Affiche le commentaire actuel (si existant)
       │    - Permet l'édition
       │
       ▼
┌──────────────────────────┐
│  Modal de Commentaire    │
│  (Textarea + Validation) │
└──────┬───────────────────┘
       │
       │ 3. Utilisateur saisit/modifie le texte
       │    - Validation: max 500 chars
       │    - Compteur en temps réel
       │
       ▼
┌──────────────────────────────────┐
│  updateTransactionCommentAction  │
│  (Server Action)                 │
└──────┬───────────────────────────┘
       │
       │ 4. Envoie la requête
       │    PATCH /transactions/{id}/comment
       │    { comment: "Nouveau texte" }
       │
       ▼
┌──────────────────────────────────┐
│  PATCH /transactions/{id}/comment│
│  (Backend API)                   │
└──────┬───────────────────────────┘
       │
       │ 5. Vérifications
       │    - Authentification
       │    - Ownership de la transaction
       │    - Validation du commentaire
       │
       ▼
┌──────────────────────────┐
│  Base de Données         │
│  (PostgreSQL)            │
└──────┬───────────────────┘
       │
       │ 6. UPDATE transactions
       │    SET comment = "Nouveau texte",
       │        updated_at = NOW()
       │    WHERE transaction_id = "..."
       │
       │ ⚠️ PAS D'ANALYSE ML
       │
       ▼
┌──────────────────────────┐
│  Revalidation            │
│  (Next.js)               │
└──────┬───────────────────┘
       │
       │ 7. revalidatePath("/activity")
       │    revalidatePath("/history")
       │
       ▼
┌──────────────────────────┐
│  TransactionItem.tsx     │
│  (Re-render)             │
└──────┬───────────────────┘
       │
       │ 8. Affiche le commentaire mis à jour
       │
       ▼
┌──────────────┐
│  Utilisateur │
│  voit la     │
│  mise à jour │
└──────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                      AFFICHAGE DES TRANSACTIONS                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Utilisateur │
│  navigue     │
│  vers        │
│  /activity   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  ActivityPage.tsx        │
│  (Server Component)      │
└──────┬───────────────────┘
       │
       │ 1. Fetch initial data
       │    GET /transactions?limit=100
       │
       ▼
┌──────────────────────────┐
│  Backend API             │
└──────┬───────────────────┘
       │
       │ 2. Retourne les transactions enrichies
       │    [
       │      {
       │        transaction_id: "...",
       │        amount: 150,
       │        source_country: "FR",      ← NOUVEAU
       │        destination_country: "ES", ← NOUVEAU
       │        comment: "...",            ← NOUVEAU
       │        recipient_iban: "...",     ← NOUVEAU
       │        ...
       │      }
       │    ]
       │
       ▼
┌──────────────────────────┐
│  Mapping des données     │
│  (ActivityPage.tsx)      │
└──────┬───────────────────┘
       │
       │ 3. Transforme en type Transaction
       │    {
       │      id: t.transaction_id,
       │      sourceCountry: t.source_country || "FR",
       │      destinationCountry: t.destination_country,
       │      comment: t.comment || t.description,
       │      ...
       │    }
       │
       ▼
┌──────────────────────────┐
│  ActivityList.tsx        │
│  (Client Component)      │
└──────┬───────────────────┘
       │
       │ 4. Map sur les transactions
       │    transactions.map(t => <TransactionItem />)
       │
       ▼
┌──────────────────────────┐
│  TransactionItem.tsx     │
│  (Client Component)      │
└──────┬───────────────────┘
       │
       │ 5. Affiche chaque transaction
       │    - getCountryFlag(sourceCountry)
       │    - getCountryFlag(destinationCountry)
       │    - Affiche le commentaire si présent
       │    - Bouton AddCommentButton
       │
       ▼
┌──────────────────────────┐
│  Rendu Final             │
│                          │
│  Marie Dubois            │
│  28 Jan • 🇫🇷 → 🇪🇸      │
│  +150 PYC [VALIDATED]    │
│                          │
│  💬 Remboursement...     │
│  [Modifier note]         │
└──────────────────────────┘
```

## 🔑 Points Clés

### ✅ Avantages du Flux

1. **Séparation des Préoccupations**
   - Création de transaction → Passe par ML
   - Modification de commentaire → Bypass ML (rapide)

2. **Performance**
   - Commentaires modifiables instantanément
   - Pas de latence d'analyse ML pour les métadonnées

3. **Sécurité**
   - Vérification d'ownership avant modification
   - Validation côté client ET serveur
   - Rate limiting sur les endpoints sensibles

4. **UX**
   - Feedback visuel immédiat
   - Revalidation automatique des pages
   - Modal intuitif pour l'édition

### ⚠️ Points d'Attention

1. **Backend**
   - L'endpoint PATCH ne doit PAS déclencher Kafka
   - Bien vérifier l'ownership de la transaction
   - Valider la longueur du commentaire (max 500)

2. **Frontend**
   - Gérer les états de chargement
   - Afficher les erreurs de manière claire
   - Revalider les données après modification

3. **Base de Données**
   - Indexer les colonnes pays pour les filtres
   - Considérer un index full-text pour les commentaires

## 📈 Métriques à Surveiller

- **Taux d'utilisation des commentaires** : % de transactions avec commentaire
- **Corridors les plus utilisés** : FR→ES, FR→DE, etc.
- **Longueur moyenne des commentaires** : Pour ajuster la limite si nécessaire
- **Temps de réponse PATCH /comment** : Doit rester < 200ms

## 🚀 Évolutions Futures

```
Phase 1 (Actuelle)
├── Commentaires libres
├── Affichage Pays-Pays
└── Modification manuelle

Phase 2 (Future)
├── Tags prédéfinis ("Cadeau", "Loyer", etc.)
├── Auto-complétion des commentaires
├── Recherche full-text dans les commentaires
└── Statistiques par corridor

Phase 3 (Future)
├── Export CSV avec commentaires
├── Filtres avancés (par pays, par tag)
├── Graphiques de flux géographiques
└── Suggestions intelligentes de commentaires
```

---

**Date** : 29 janvier 2026  
**Version** : 1.0.0
