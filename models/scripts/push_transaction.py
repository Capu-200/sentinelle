#!/usr/bin/env python3
"""
Script pour ajouter manuellement une transaction à l'historique.

Usage:
    python scripts/push_transaction.py <transaction.json>
    python scripts/push_transaction.py --interactive
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.historique_store import HistoriqueStore


def load_transaction_from_file(file_path: Path) -> dict:
    """Charge une transaction depuis un fichier JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_transaction_interactive() -> dict:
    """Crée une transaction de manière interactive."""
    print("Création d'une transaction (appuyez sur Entrée pour valeurs par défaut)")

    transaction = {}

    # Identifiants
    transaction["transaction_id"] = input("transaction_id: ").strip() or "tx_manual_001"
    transaction["initiator_user_id"] = input("initiator_user_id: ").strip() or "user_001"
    transaction["source_wallet_id"] = input("source_wallet_id: ").strip() or "wallet_src_001"
    transaction["destination_wallet_id"] = (
        input("destination_wallet_id: ").strip() or "wallet_dst_001"
    )

    # Montant
    amount_str = input("amount: ").strip()
    transaction["amount"] = float(amount_str) if amount_str else 100.0

    # Devise
    transaction["currency"] = input("currency (PYC): ").strip() or "PYC"

    # Type et direction
    transaction["transaction_type"] = input("transaction_type (P2P): ").strip() or "P2P"
    transaction["direction"] = input("direction (outgoing/incoming): ").strip() or "outgoing"

    # Timestamp
    from datetime import datetime, timezone

    transaction["created_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Optionnel
    country = input("country (optionnel): ").strip()
    if country:
        transaction["country"] = country

    city = input("city (optionnel): ").strip()
    if city:
        transaction["city"] = city

    description = input("description (optionnel): ").strip()
    if description:
        transaction["description"] = description

    return transaction


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Ajoute une transaction à l'historique manuellement"
    )
    parser.add_argument(
        "transaction_file",
        nargs="?",
        type=Path,
        help="Chemin vers le fichier JSON contenant la transaction",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Créer une transaction de manière interactive",
    )
    parser.add_argument(
        "--storage",
        "-s",
        type=Path,
        default="Data/historique.json",
        help="Chemin vers le fichier de stockage (défaut: Data/historique.json)",
    )

    args = parser.parse_args()

    # Initialiser le store
    store = HistoriqueStore(storage_path=args.storage)

    # Charger ou créer la transaction
    if args.interactive:
        transaction = create_transaction_interactive()
    elif args.transaction_file:
        if not args.transaction_file.exists():
            print(f"Erreur: Le fichier {args.transaction_file} n'existe pas", file=sys.stderr)
            sys.exit(1)
        transaction = load_transaction_from_file(args.transaction_file)
    else:
        parser.print_help()
        sys.exit(1)

    # Valider la transaction (champs requis)
    required_fields = [
        "transaction_id",
        "initiator_user_id",
        "source_wallet_id",
        "destination_wallet_id",
        "amount",
        "currency",
        "transaction_type",
        "direction",
        "created_at",
    ]

    missing_fields = [field for field in required_fields if field not in transaction]
    if missing_fields:
        print(f"Erreur: Champs manquants: {', '.join(missing_fields)}", file=sys.stderr)
        sys.exit(1)

    # Ajouter la transaction
    try:
        store.add_transaction(transaction)
        print(f"✅ Transaction {transaction['transaction_id']} ajoutée avec succès!")
        print(f"📊 Historique total: {store.count()} transactions")
    except Exception as e:
        print(f"Erreur lors de l'ajout: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

