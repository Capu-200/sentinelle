#!/usr/bin/env python3
"""
Script principal pour scorer une transaction.

Ce script orchestre tout le pipeline de scoring :
1. Feature Engineering
2. Règles métier
3. Scoring ML (supervisé + non supervisé)
4. Score global
5. Décision finale

Usage:
    python scripts/score_transaction.py <transaction.json>
    python scripts/score_transaction.py --interactive
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.historique_store import HistoriqueStore
from src.features.pipeline import FeaturePipeline
from src.rules.engine import RulesEngine
from src.scoring.decision import DecisionEngine
from src.scoring.scorer import GlobalScorer


def load_transaction_from_file(file_path: Path) -> dict:
    """Charge une transaction depuis un fichier JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_transaction_interactive() -> dict:
    """Crée une transaction de manière interactive."""
    print("Création d'une transaction pour scoring")
    print("(appuyez sur Entrée pour valeurs par défaut)\n")

    transaction = {}

    # Identifiants
    transaction["transaction_id"] = input("transaction_id: ").strip() or "tx_test_001"
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
    from datetime import datetime

    transaction["created_at"] = datetime.utcnow().isoformat() + "Z"

    # Optionnel
    country = input("country (optionnel): ").strip()
    if country:
        transaction["country"] = country

    return transaction


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Score une transaction")
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
        help="Chemin vers le fichier de stockage historique (défaut: Data/historique.json)",
    )
    parser.add_argument(
        "--rules-config",
        type=Path,
        default="src/rules/config/rules_v1.yaml",
        help="Chemin vers la config des règles",
    )
    parser.add_argument(
        "--scoring-config",
        type=Path,
        default="configs/scoring_config.yaml",
        help="Chemin vers la config du scoring",
    )
    parser.add_argument(
        "--decision-config",
        type=Path,
        default="configs/scoring_config.yaml",
        help="Chemin vers la config de décision",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Sauvegarder la transaction dans l'historique après scoring",
    )

    args = parser.parse_args()

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

    try:
        # Initialiser les composants
        print("🔧 Initialisation des composants...")
        store = HistoriqueStore(storage_path=args.storage)
        feature_pipeline = FeaturePipeline()
        rules_engine = RulesEngine(config_path=args.rules_config)
        scorer = GlobalScorer(config_path=args.scoring_config)
        decision_engine = DecisionEngine(config_path=args.decision_config)

        # 1. Feature Engineering
        print("\n📊 Calcul des features...")
        from datetime import datetime

        current_time = datetime.fromisoformat(transaction["created_at"].replace("Z", "+00:00"))

        # Récupérer l'historique pour les features
        historical_data = store.get_historical_data(
            source_wallet_id=transaction.get("source_wallet_id"),
            before_time=current_time,
        )

        features = feature_pipeline.transform(transaction, historical_data=historical_data)
        print(f"   ✅ {len(features)} features calculées")

        # 2. Règles métier
        print("\n⚖️  Évaluation des règles métier...")

        # Récupérer les infos wallet/user pour les règles
        wallet_info = store.get_wallet_info(transaction["source_wallet_id"])
        user_profile = store.get_user_profile(transaction["initiator_user_id"])

        # Enrichir la transaction avec les infos contextuelles
        transaction_with_context = {
            **transaction,
            "_wallet_balance": wallet_info.get("balance"),
            "_wallet_status": wallet_info.get("status"),
            "_user_status": user_profile.get("status"),
            "_user_risk_level": user_profile.get("risk_level"),
        }

        rules_output = rules_engine.evaluate(
            transaction=transaction_with_context,
            features=features,
        )

        print(f"   ✅ Décision règles: {rules_output.decision}")
        print(f"   📋 Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
        print(f"   📈 Rule score: {rules_output.rule_score:.3f}")
        print(f"   🚀 Boost factor: {rules_output.boost_factor:.2f}")

        # Si BLOCK, arrêter ici
        if rules_output.decision == "BLOCK":
            print("\n🚫 TRANSACTION BLOQUÉE par les règles")
            decision = decision_engine.decide(
                risk_score=rules_output.rule_score,
                reasons=rules_output.reasons,
                hard_block=True,
                model_version="v1.0.0",
            )
            print(f"\n📊 Résultat final:")
            print(f"   Risk score: {decision.risk_score:.3f}")
            print(f"   Decision: {decision.decision}")
            print(f"   Reasons: {', '.join(decision.reasons)}")
            print(f"   Model version: {decision.model_version}")

            # Sauvegarder si demandé
            if args.save:
                store.add_transaction(transaction)
                print(f"\n💾 Transaction sauvegardée dans l'historique")

            sys.exit(0)

        # 3. Scoring ML (mock pour l'instant - à implémenter)
        print("\n🤖 Scoring ML...")
        # TODO: Implémenter le scoring supervisé et non supervisé
        supervised_score = 0.5  # Mock
        unsupervised_score = 0.5  # Mock
        print(f"   ✅ Supervisé: {supervised_score:.3f}")
        print(f"   ✅ Non supervisé: {unsupervised_score:.3f}")

        # 4. Score global
        print("\n🎯 Calcul du score global...")
        risk_score = scorer.compute_score(
            rule_score=rules_output.rule_score,
            supervised_score=supervised_score,
            unsupervised_score=unsupervised_score,
            boost_factor=rules_output.boost_factor,
        )
        print(f"   ✅ Risk score: {risk_score:.3f}")

        # 5. Décision finale
        print("\n⚖️  Décision finale...")
        decision = decision_engine.decide(
            risk_score=risk_score,
            reasons=rules_output.reasons,
            hard_block=False,
            model_version="v1.0.0",
        )

        # Afficher le résultat
        print(f"\n📊 Résultat final:")
        print(f"   Risk score: {decision.risk_score:.3f}")
        print(f"   Decision: {decision.decision}")
        print(f"   Reasons: {', '.join(decision.reasons) if decision.reasons else 'Aucune'}")
        print(f"   Model version: {decision.model_version}")

        # Sauvegarder si demandé
        if args.save:
            store.add_transaction(transaction)
            print(f"\n💾 Transaction sauvegardée dans l'historique")

        # Retourner le résultat en JSON
        result = {
            "risk_score": decision.risk_score,
            "decision": decision.decision,
            "reasons": decision.reasons,
            "model_version": decision.model_version,
        }
        print(f"\n📄 JSON résultat:")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

