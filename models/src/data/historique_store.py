"""
Stockage et récupération de l'historique des transactions.

Ce module gère le stockage local des transactions pour la phase de développement.
En production, ce sera remplacé par une base de données ou un feature store.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class HistoriqueStore:
    """
    Store d'historique des transactions (phase dev - fichier local).

    Stocke les transactions dans un fichier JSON/CSV pour permettre
    le calcul des features historiques et des règles.
    """

    def __init__(self, storage_path: Path | str = "Data/historique.json"):
        """
        Initialise le store d'historique.

        Args:
            storage_path: Chemin vers le fichier de stockage (JSON ou CSV)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Charger l'historique existant
        self._transactions: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Charge l'historique depuis le fichier."""
        if not self.storage_path.exists():
            return

        if self.storage_path.suffix == ".json":
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self._transactions = json.load(f)
        elif self.storage_path.suffix == ".csv":
            df = pd.read_csv(self.storage_path)
            self._transactions = df.to_dict("records")
        else:
            raise ValueError(f"Format non supporté: {self.storage_path.suffix}")

    def _save(self) -> None:
        """Sauvegarde l'historique dans le fichier."""
        if self.storage_path.suffix == ".json":
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._transactions, f, indent=2, default=str)
        elif self.storage_path.suffix == ".csv":
            df = pd.DataFrame(self._transactions)
            df.to_csv(self.storage_path, index=False)
        else:
            raise ValueError(f"Format non supporté: {self.storage_path.suffix}")

    def add_transaction(self, transaction: Dict[str, Any]) -> None:
        """
        Ajoute une transaction à l'historique.

        Args:
            transaction: Transaction à ajouter (doit contenir created_at)
        """
        # S'assurer que created_at est présent
        if "created_at" not in transaction:
            transaction["created_at"] = datetime.utcnow().isoformat()

        # Ajouter la transaction
        self._transactions.append(transaction.copy())

        # Sauvegarder
        self._save()

    def get_historical_data(
        self,
        source_wallet_id: Optional[str] = None,
        destination_wallet_id: Optional[str] = None,
        initiator_user_id: Optional[str] = None,
        before_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des transactions selon des critères.

        Args:
            source_wallet_id: Filtrer par wallet source
            destination_wallet_id: Filtrer par wallet destination
            initiator_user_id: Filtrer par utilisateur initiateur
            before_time: Ne retourner que les transactions avant ce timestamp
            limit: Limiter le nombre de résultats

        Returns:
            Liste des transactions historiques
        """
        results = []

        for tx in self._transactions:
            # Filtrer par wallet source
            if source_wallet_id and tx.get("source_wallet_id") != source_wallet_id:
                continue

            # Filtrer par wallet destination
            if destination_wallet_id and tx.get("destination_wallet_id") != destination_wallet_id:
                continue

            # Filtrer par utilisateur
            if initiator_user_id and tx.get("initiator_user_id") != initiator_user_id:
                continue

            # Filtrer par date
            if before_time:
                # Normaliser before_time en UTC aware si nécessaire
                if before_time.tzinfo is None:
                    from dateutil.tz import UTC
                    before_time = before_time.replace(tzinfo=UTC)
                else:
                    from dateutil.tz import UTC
                    before_time = before_time.astimezone(UTC)
                
                tx_time = self._parse_datetime(tx.get("created_at"))
                if tx_time is None or tx_time >= before_time:
                    continue

            results.append(tx)

        # Trier par date (plus récent en premier)
        from dateutil.tz import UTC
        min_dt = datetime.min.replace(tzinfo=UTC)
        results.sort(
            key=lambda x: self._parse_datetime(x.get("created_at")) or min_dt,
            reverse=True,
        )

        # Limiter les résultats
        if limit:
            results = results[:limit]

        return results

    def get_transactions_in_window(
        self,
        source_wallet_id: str,
        window: str,
        current_time: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Récupère les transactions dans une fenêtre temporelle.

        Args:
            source_wallet_id: Wallet source
            window: Fenêtre temporelle (ex: "5m", "1h", "24h", "7d", "30d")
            current_time: Timestamp de référence

        Returns:
            Liste des transactions dans la fenêtre
        """
        # Convertir la fenêtre en timedelta
        delta = self._parse_window(window)
        if delta is None:
            return []

        # Normaliser current_time en UTC aware si nécessaire
        from dateutil.tz import UTC
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=UTC)
        else:
            current_time = current_time.astimezone(UTC)
        
        # Calculer le timestamp de début
        start_time = current_time - delta

        # Récupérer toutes les transactions avant current_time
        all_tx = self.get_historical_data(
            source_wallet_id=source_wallet_id,
            before_time=current_time,
        )

        # Filtrer par fenêtre temporelle
        results = []
        for tx in all_tx:
            tx_time = self._parse_datetime(tx.get("created_at"))
            if tx_time is None:
                continue

            # Ne garder que les transactions dans la fenêtre
            if start_time <= tx_time < current_time:
                results.append(tx)

        return results

    def get_wallet_info(self, wallet_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un wallet (mock pour phase dev).

        En production, cela viendrait de la base de données.

        Args:
            wallet_id: ID du wallet

        Returns:
            Dictionnaire avec balance, status, etc.
        """
        # Pour la phase dev, on simule des données
        # En production, cela viendrait de la DB
        return {
            "wallet_id": wallet_id,
            "balance": 1000.0,  # Mock - à remplacer par vraie DB
            "status": "active",  # Mock - à remplacer par vraie DB
            "created_at": "2024-01-01T00:00:00Z",  # Mock
        }

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère le profil d'un utilisateur (mock pour phase dev).

        En production, cela viendrait de la base de données.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Dictionnaire avec risk_level, status, etc.
        """
        # Pour la phase dev, on simule des données
        # En production, cela viendrait de la DB
        return {
            "user_id": user_id,
            "risk_level": "low",  # Mock - à remplacer par vraie DB
            "status": "active",  # Mock - à remplacer par vraie DB
        }

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """
        Parse une chaîne datetime en objet datetime.
        
        Retourne toujours un datetime aware (avec timezone UTC).
        """
        if dt_str is None:
            return None

        try:
            # Essayer de parser avec dateutil (gère mieux les timezones)
            from dateutil import parser
            from dateutil.tz import UTC

            dt = parser.parse(dt_str)
            
            # Si le datetime est naive, le rendre aware avec UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            else:
                # Convertir en UTC si nécessaire
                dt = dt.astimezone(UTC)
            
            return dt
        except Exception:
            # Fallback: essayer des formats manuels
            try:
                # Format ISO avec Z
                if dt_str.endswith("Z"):
                    dt_str_clean = dt_str[:-1]
                    if "." in dt_str_clean:
                        dt = datetime.strptime(dt_str_clean, "%Y-%m-%dT%H:%M:%S.%f")
                    else:
                        dt = datetime.strptime(dt_str_clean, "%Y-%m-%dT%H:%M:%S")
                    from dateutil.tz import UTC
                    return dt.replace(tzinfo=UTC)
                else:
                    # Format sans timezone - assumer UTC
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    from dateutil.tz import UTC
                    return dt.replace(tzinfo=UTC)
            except Exception:
                return None

    def _parse_window(self, window: str) -> Optional[timedelta]:
        """Parse une fenêtre temporelle en timedelta."""
        if not window:
            return None

        # Extraire le nombre et l'unité
        if len(window) < 2:
            return None

        try:
            unit = window[-1].lower()
            value = int(window[:-1])

            if unit == "m":
                return timedelta(minutes=value)
            elif unit == "h":
                return timedelta(hours=value)
            elif unit == "d":
                return timedelta(days=value)
            else:
                return None
        except (ValueError, IndexError):
            return None

    def clear(self) -> None:
        """Efface tout l'historique."""
        self._transactions = []
        self._save()

    def count(self) -> int:
        """Retourne le nombre de transactions dans l'historique."""
        return len(self._transactions)

