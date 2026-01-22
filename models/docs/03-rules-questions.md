# Questions de clarification — Règles métier

Document de questions pour clarifier les spécificités du projet avant l'implémentation des règles métier détaillées.

## 1. Accès aux données contextuelles

### 1.1 Wallets et utilisateurs

**Question :** Comment accéder aux informations suivantes nécessaires pour les règles ?

- **Balance du wallet source** (`wallet.balance`) — pour la règle "Solde insuffisant"
- **Status du wallet source** (`wallet.status`) — pour "Wallet bloqué"
- **Status du wallet destination** (`destination_wallet.status`) — pour "Destination interdite"
- **Status de l'utilisateur** (`profiles.status`) — pour "Utilisateur suspendu"
- **Risk level de l'utilisateur** (`profiles.risk_level`) — pour "Profil à risque connu"

**Options possibles :**
- [ ] API REST du backend (appel HTTP)
- [ ] Accès direct à la base de données PostgreSQL
- [ ] Les données sont déjà incluses dans l'objet transaction
- [ ] Service de feature store
- [ ] Autre : _______________

**Réponse :** _______________

### 1.2 Historique des transactions

**Question :** Comment calculer les features historiques nécessaires pour certaines règles ?

Exemples de features nécessaires :
- `avg_amount_30d` — moyenne des montants sur 30 jours
- `tx_last_10min` — nombre de transactions dans les 10 dernières minutes
- `account_age_minutes` — âge du compte en minutes
- `is_new_beneficiary` — est-ce un nouveau bénéficiaire ?
- `user_country_history` — historique des pays de l'utilisateur
- `blocked_tx_last_24h` — nombre de transactions bloquées dans les 24h

**Options possibles :**
- [ ] Requêtes SQL directes sur `banking.transactions`
- [ ] Service de feature store pré-calculé
- [ ] Fichier CSV/JSON local (phase dev uniquement)
- [ ] API dédiée pour les features historiques
- [ ] Autre : _______________

**Réponse :** _______________

### 1.3 Gestion des données manquantes

**Question :** Que faire si certaines données ne sont pas disponibles ?

Exemples :
- Le `country` n'est pas fourni dans la transaction
- Le wallet n'existe pas encore en base
- L'historique est vide (nouveau compte)
- Le `risk_level` n'est pas défini

**Stratégie proposée :**
- [ ] Ignorer la règle si les données sont manquantes (pas de blocage par défaut)
- [ ] Considérer comme suspect (BOOST_SCORE ou BLOCK selon la règle)
- [ ] Utiliser des valeurs par défaut conservatrices
- [ ] Autre : _______________

**Réponse :** _______________

## 2. Seuils et paramètres des règles

### 2.1 Montant maximum absolu

**Question :** Confirmation du seuil `MAX_TX_AMOUNT = 1000 PYC` ?

**Réponse :** Oui / Non → Si non, quelle valeur ? _______________

### 2.2 Montant inhabituel (BOOST_SCORE)

**Question :** Confirmation des seuils pour "Montant inhabituel" ?

- Seuil 1 : `amount > avg_amount_30d * 10` → BOOST_SCORE
- Seuil 2 : `amount > avg_amount_30d * 5` → BOOST_SCORE

**Réponse :** Oui / Non → Si non, quels seuils ? _______________

**Question :** Que faire si `avg_amount_30d` n'existe pas (nouveau compte) ?

**Réponse :** _______________

### 2.3 Rafale de transactions

**Question :** Confirmation des seuils pour "Rafale de transactions" ?

- Seuil 1 : `tx_last_10min >= 20` → BOOST_SCORE
- Seuil 2 : `tx_last_10min >= 10` → BOOST_SCORE

**Réponse :** Oui / Non → Si non, quels seuils ? _______________

**Question :** Quelle fenêtre temporelle exacte ? (10 minutes, 1 heure, autre ?)

**Réponse :** _______________

### 2.4 Compte trop récent

**Question :** Confirmation des seuils pour "Compte trop récent" ?

- Seuil 1 : `account_age_minutes < 5 ET amount > 100` → BOOST_SCORE
- Seuil 2 : `account_age_minutes < 60 ET amount > 50` → BOOST_SCORE

**Réponse :** Oui / Non → Si non, quels seuils ? _______________

### 2.5 Nouveau bénéficiaire

**Question :** Confirmation des seuils pour "Nouveau bénéficiaire" ?

- Seuil 1 : `is_new_beneficiary = true ET amount > 200` → BLOCK
- Seuil 2 : `is_new_beneficiary = true ET amount > 80` → BOOST_SCORE

**Réponse :** Oui / Non → Si non, quels seuils ? _______________

**Question :** Comment définir "nouveau bénéficiaire" ? (jamais vu, pas vu dans les 30 derniers jours, autre ?)

**Réponse :** _______________

### 2.6 Pays inhabituel

**Question :** Confirmation de la logique pour "Pays inhabituel" ?

- `country NOT IN user_country_history ET amount > 150` → BLOCK

**Réponse :** Oui / Non → Si non, quelle logique ? _______________

**Question :** Sur quelle période regarder l'historique des pays ? (30 jours, 90 jours, tout l'historique ?)

**Réponse :** _______________

### 2.7 Horaire interdit

**Question :** Confirmation des seuils pour "Horaire interdit" ?

- Seuil 1 : `hour BETWEEN 01:00 AND 05:00 ET amount > 120` → BLOCK
- Seuil 2 : `hour BETWEEN 01:00 AND 05:00 ET amount > 60` → BOOST_SCORE

**Réponse :** Oui / Non → Si non, quels seuils ? _______________

**Question :** Fuseau horaire à utiliser ? (UTC, fuseau de l'utilisateur, autre ?)

**Réponse :** _______________

### 2.8 Profil à risque connu

**Question :** Confirmation des seuils pour "Profil à risque connu" ?

- Seuil 1 : `profiles.risk_level = 'high' ET amount > 50` → BOOST_SCORE
- Seuil 2 : `profiles.risk_level = 'high' ET amount > 150` → BLOCK

**Réponse :** Oui / Non → Si non, quels seuils ? _______________

**Question :** Quelles sont les valeurs possibles de `risk_level` ? (low, medium, high, autre ?)

**Réponse :** _______________

### 2.9 Récidive récente

**Question :** Confirmation des seuils pour "Récidive récente" ?

- Seuil 1 : `blocked_tx_last_24h >= 3` → BLOCK
- Seuil 2 : `blocked_tx_last_24h >= 1` → BOOST_SCORE

**Réponse :** Oui / Non → Si non, quels seuils ? _______________

**Question :** Comment compter les transactions bloquées ? (toutes les transactions avec `status = 'BLOCKED'`, uniquement celles bloquées par les règles, autre ?)

**Réponse :** _______________

### 2.10 Pays interdit (blacklist)

**Question :** Confirmation de la liste des pays interdits ?

- Liste proposée : `['KP', 'IR', 'SY', 'RU_TEST']`

**Réponse :** Oui / Non → Si non, quelle liste ? _______________

## 3. Intégration avec le système de scoring

### 3.1 BOOST_SCORE

**Question :** Comment implémenter le mécanisme `BOOST_SCORE` ?

**Options proposées :**
- [ ] Ajouter un bonus fixe au `rule_score` (ex: +0.2)
- [ ] Multiplier le `risk_score` final par un facteur (ex: ×1.2)
- [ ] Ajouter un bonus au `risk_score` avant la décision finale
- [ ] Autre : _______________

**Réponse :** _______________

**Question :** Si plusieurs règles `BOOST_SCORE` sont déclenchées, comment les combiner ?

**Réponse :** _______________

### 3.2 Ordre d'évaluation

**Question :** Faut-il évaluer les règles dans un ordre spécifique ?

**Stratégie proposée :**
- [ ] Évaluer toutes les règles bloquantes d'abord (si BLOCK → arrêt immédiat)
- [ ] Évaluer toutes les règles en parallèle
- [ ] Ordre spécifique : _______________

**Réponse :** _______________

### 3.3 Performance et latence

**Question :** Contraintes de performance pour les règles ?

- Latence cible : 300ms pour l'ensemble du scoring (règles + ML)
- Les règles doivent-elles être optimisées pour la vitesse ?
- Faut-il mettre en cache certaines données (balance, status, etc.) ?

**Réponse :** _______________

## 4. Mapping avec le schéma de base de données

### 4.1 Correspondance wallet/account

**Question :** Comment faire le mapping entre :
- `source_wallet_id` / `destination_wallet_id` (dans la transaction ML)
- `account_id` (dans la table `banking.accounts`)

**Réponse :** _______________

### 4.2 Correspondance user/profile

**Question :** Comment faire le mapping entre :
- `initiator_user_id` (dans la transaction ML)
- `user_id` (dans la table `auth.users`)
- `profiles` (table/entité pour les profils utilisateurs)

**Réponse :** _______________

**Question :** Où sont stockées les informations de profil (`risk_level`, `status`) ?

**Réponse :** _______________

## 5. Tests et validation

### 5.1 Données de test

**Question :** Avez-vous des exemples de transactions de test pour valider chaque règle ?

**Réponse :** Oui / Non

Si oui, où sont-ils stockés ? _______________

### 5.2 Cas limites

**Question :** Y a-t-il des cas limites spécifiques à tester ?

**Réponse :** _______________

## 6. Configuration et déploiement

### 6.1 Fichier de configuration

**Question :** Préférence pour le format de configuration des règles ?

- [ ] YAML (comme `rules_v1.yaml` actuel)
- [ ] JSON
- [ ] Python (dictionnaire)
- [ ] Autre : _______________

**Réponse :** _______________

### 6.2 Paramètres modifiables

**Question :** Quels paramètres doivent être facilement modifiables sans changer le code ?

**Exemples :**
- Seuils de montants
- Liste des pays interdits
- Fenêtres temporelles
- Facteurs de boost

**Réponse :** _______________

---

## Notes additionnelles

Espace pour toute autre information pertinente :

_______________
_______________
_______________

