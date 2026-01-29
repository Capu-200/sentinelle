# 📱 Guide Utilisateur - Virements Enrichis

## 🎯 Nouvelles Fonctionnalités

Votre application Payon dispose maintenant de **virements enrichis** avec :
- 🌍 **Informations géographiques** : Visualisez le trajet de vos virements (ex: 🇫🇷 → 🇪🇸)
- 💬 **Commentaires personnels** : Ajoutez des notes à vos transactions pour mieux les organiser
- ⚡ **Modification instantanée** : Éditez vos commentaires à tout moment sans délai

---

## 📖 Mode d'Emploi

### 1️⃣ Créer un Virement avec Commentaire

#### Étape 1 : Accéder au formulaire
1. Depuis le **Dashboard**, cliquez sur **"Envoyer"**
2. Ou utilisez le bouton **"Transfert"** dans la navigation

#### Étape 2 : Remplir les informations
```
┌─────────────────────────────────────┐
│  Pour qui ?                         │
│  ┌───────────────────────────────┐  │
│  │ marie@example.com             │  │
│  └───────────────────────────────┘  │
│                                     │
│  Commentaire (optionnel)            │
│  ┌───────────────────────────────┐  │
│  │ Remboursement restaurant      │  │
│  │ Madrid                        │  │
│  └───────────────────────────────┘  │
│                                     │
│  Montant à envoyer                  │
│         150 PYC                     │
│                                     │
│  [Confirmer l'envoi]                │
└─────────────────────────────────────┘
```

#### Étape 3 : Confirmer
- Cliquez sur **"Confirmer l'envoi"**
- Votre virement est créé avec le commentaire
- Vous êtes redirigé vers l'**Historique**

---

### 2️⃣ Ajouter un Commentaire à une Transaction Existante

#### Étape 1 : Accéder à l'historique
1. Depuis le **Dashboard**, cliquez sur **"Historique"**
2. Ou naviguez vers **"Activité"** dans le menu

#### Étape 2 : Sélectionner une transaction
```
┌─────────────────────────────────────┐
│  Marie Dubois                       │
│  28 Jan 2026 • 🇫🇷 → 🇪🇸            │
│                    +150 PYC         │
│                    [VALIDATED]      │
│                                     │
│  [Ajouter note]                     │
└─────────────────────────────────────┘
```

#### Étape 3 : Cliquer sur "Ajouter note"
Un modal s'ouvre :

```
┌─────────────────────────────────────┐
│  Ajouter un commentaire        [X]  │
├─────────────────────────────────────┤
│                                     │
│  Votre note personnelle             │
│  ┌───────────────────────────────┐  │
│  │ Ex: Remboursement dîner,      │  │
│  │ Cadeau anniversaire...        │  │
│  │                               │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│  0/500 caractères                   │
│                                     │
│  [Annuler]  [Enregistrer]           │
└─────────────────────────────────────┘
```

#### Étape 4 : Saisir et enregistrer
- Tapez votre commentaire (max 500 caractères)
- Cliquez sur **"Enregistrer"**
- Le commentaire apparaît instantanément

---

### 3️⃣ Modifier un Commentaire Existant

#### Même processus que l'ajout
1. Cliquez sur **"Modifier note"** (au lieu de "Ajouter note")
2. Le texte actuel est pré-rempli
3. Modifiez le texte
4. Cliquez sur **"Enregistrer"**

---

## 💡 Exemples d'Utilisation

### Cas d'usage 1 : Organisation Personnelle
```
Transaction : 150 PYC → Marie Dubois
Commentaire : "Remboursement restaurant Madrid - 27 janvier"
```
→ Vous retrouvez facilement le contexte de ce virement

### Cas d'usage 2 : Suivi des Dépenses
```
Transaction : 250 PYC → Thomas Martin
Commentaire : "Loyer Janvier 2026 - Appartement Berlin"
```
→ Vous pouvez suivre vos paiements récurrents

### Cas d'usage 3 : Cadeaux et Événements
```
Transaction : 75 PYC → Sophie Bernard
Commentaire : "Cadeau anniversaire 🎂"
```
→ Vous vous souvenez de vos cadeaux offerts

### Cas d'usage 4 : Transactions Professionnelles
```
Transaction : 500 PYC → Lucas Petit
Commentaire : "Facture #2026-001 - Services de consulting"
```
→ Vous liez vos virements à vos factures

---

## 🌍 Informations Géographiques

### Affichage des Drapeaux
Les virements affichent automatiquement le trajet géographique :

```
🇫🇷 → 🇪🇸  France vers Espagne
🇫🇷 → 🇩🇪  France vers Allemagne
🇧🇪 → 🇫🇷  Belgique vers France
🇨🇭 → 🇫🇷  Suisse vers France
```

### Pays Supportés
- 🇫🇷 France
- 🇪🇸 Espagne
- 🇩🇪 Allemagne
- 🇮🇹 Italie
- 🇧🇪 Belgique
- 🇳🇱 Pays-Bas
- 🇵🇹 Portugal
- 🇨🇭 Suisse
- 🇬🇧 Royaume-Uni
- Et bien d'autres...

---

## ✅ Bonnes Pratiques

### 📝 Rédaction de Commentaires

**✅ Bon**
```
"Remboursement dîner restaurant - 27/01"
"Loyer Janvier 2026"
"Cadeau anniversaire Marie"
"Facture #2026-001"
```

**❌ À éviter**
```
"aaa"                    (Trop court, pas informatif)
"Transaction"            (Trop générique)
[Texte de 600 chars]     (Trop long, sera refusé)
```

### 🎯 Conseils

1. **Soyez concis** : 1-2 lignes suffisent
2. **Ajoutez des dates** : Utile pour les paiements récurrents
3. **Utilisez des émojis** : 🎂 🏠 💼 pour identifier rapidement
4. **Numérotez vos factures** : Pour la comptabilité

---

## 🔒 Confidentialité et Sécurité

### Qui peut voir mes commentaires ?
- ✅ **Vous uniquement** : Les commentaires sont privés
- ❌ **Pas le destinataire** : Il ne voit pas votre note
- ❌ **Pas les autres utilisateurs** : Vos notes sont personnelles

### Puis-je supprimer un commentaire ?
- Oui, modifiez-le et laissez le champ vide
- Ou remplacez-le par un nouveau texte

### Les commentaires sont-ils analysés par l'IA ?
- ❌ **Non** : Les commentaires ne passent pas par l'analyse ML
- ⚡ **Instantané** : Les modifications sont immédiates
- 🔒 **Privé** : Stockés uniquement dans votre historique

---

## 📊 Visualisation dans l'Historique

### Avant (Sans enrichissement)
```
┌─────────────────────────────────────┐
│  Marie Dubois                       │
│  28 Jan 2026                        │
│                    +150 PYC         │
│                    [VALIDATED]      │
└─────────────────────────────────────┘
```

### Après (Avec enrichissement)
```
┌─────────────────────────────────────┐
│  Marie Dubois                       │
│  28 Jan 2026 • 🇫🇷 → 🇪🇸            │
│                    +150 PYC         │
│                    [VALIDATED]      │
│                                     │
│  💬 Remboursement restaurant Madrid │
│                                     │
│  [Modifier note]                    │
└─────────────────────────────────────┘
```

---

## ❓ FAQ

### Q: Puis-je ajouter un commentaire après avoir envoyé le virement ?
**R:** Oui ! Cliquez sur "Ajouter note" dans l'historique à tout moment.

### Q: Y a-t-il une limite de caractères ?
**R:** Oui, 500 caractères maximum. Un compteur s'affiche pendant la saisie.

### Q: Le commentaire change-t-il le statut de la transaction ?
**R:** Non, l'ajout/modification d'un commentaire ne déclenche pas de nouvelle analyse de sécurité.

### Q: Puis-je rechercher dans mes commentaires ?
**R:** Pas encore, mais cette fonctionnalité est prévue dans une future mise à jour.

### Q: Les drapeaux s'affichent-ils automatiquement ?
**R:** Oui, si le système détecte le pays du destinataire (via IBAN ou profil).

### Q: Que se passe-t-il si je ne mets pas de commentaire ?
**R:** Rien ! Le commentaire est optionnel. Vous pouvez toujours l'ajouter plus tard.

---

## 🎉 Profitez de vos Virements Enrichis !

Vos transactions sont maintenant plus **riches**, plus **organisées** et plus **faciles à retrouver**.

**Bonne utilisation de Payon ! 🚀**

---

**Date de mise à jour** : 29 janvier 2026  
**Version** : 1.0.0
