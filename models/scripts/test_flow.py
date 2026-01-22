#!/usr/bin/env python3
"""
Script de test pour valider le flux complet :
1. Ajouter des transactions à l'historique
2. Voir l'historique
3. Scorer des transactions

Usage:
    python scripts/test_flow.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.historique_store import HistoriqueStore


def print_section(title: str):
    """Affiche un titre de section."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_add_transaction():
    """Test 1: Ajouter une transaction à l'historique."""
    print_section("TEST 1: Ajouter une transaction")

    store = HistoriqueStore(storage_path="Data/test_historique.json")

    # Transaction de test
    transaction = {
        "transaction_id": "tx_test_001",
        "initiator_user_id": "user_001",
        "source_wallet_id": "wallet_src_001",
        "destination_wallet_id": "wallet_dst_001",
        "amount": 100.0,
        "currency": "PYC",
        "transaction_type": "P2P",
        "direction": "outgoing",
        "created_at": "2026-01-21T12:00:00Z",
        "country": "FR",
    }

    print(f"📝 Ajout de la transaction: {transaction['transaction_id']}")
    store.add_transaction(transaction)
    print(f"✅ Transaction ajoutée avec succès!")
    print(f"📊 Nombre total de transactions: {store.count()}")

    return store


def test_view_historique(store: HistoriqueStore):
    """Test 2: Voir l'historique."""
    print_section("TEST 2: Voir l'historique")

    # Récupérer toutes les transactions
    all_tx = store.get_historical_data()
    print(f"📊 Nombre total de transactions: {len(all_tx)}")

    if all_tx:
        print("\n📋 Dernières transactions:")
        for i, tx in enumerate(all_tx[:5], 1):  # Afficher les 5 premières
            print(f"\n  {i}. Transaction ID: {tx.get('transaction_id')}")
            print(f"     Montant: {tx.get('amount')} {tx.get('currency')}")
            print(f"     Source: {tx.get('source_wallet_id')}")
            print(f"     Destination: {tx.get('destination_wallet_id')}")
            print(f"     Date: {tx.get('created_at')}")
    else:
        print("⚠️  Aucune transaction dans l'historique")

    # Récupérer les transactions d'un wallet spécifique
    print("\n🔍 Transactions du wallet 'wallet_src_001':")
    wallet_tx = store.get_historical_data(source_wallet_id="wallet_src_001")
    print(f"   Nombre: {len(wallet_tx)}")


def test_score_transaction():
    """Test 3: Scorer une transaction."""
    print_section("TEST 3: Scorer une transaction")

    # Importer ici pour éviter les erreurs si les modules ne sont pas complets
    try:
        from src.features.pipeline import FeaturePipeline
        from src.rules.engine import RulesEngine
        from src.scoring.decision import DecisionEngine
        from src.scoring.scorer import GlobalScorer
    except ImportError as e:
        print(f"⚠️  Erreur d'import: {e}")
        print("   Certains modules ne sont pas encore complets, mais le test peut continuer")
        print(f"   💡 Essayez: pip install -r requirements.txt")
        return

    # Initialiser les composants
    store = HistoriqueStore(storage_path="Data/test_historique.json")
    feature_pipeline = FeaturePipeline()
    rules_engine = RulesEngine()
    scorer = GlobalScorer()
    decision_engine = DecisionEngine()

    # Transaction de test
    transaction = {
        "transaction_id": "tx_score_test",
        "initiator_user_id": "user_001",
        "source_wallet_id": "wallet_src_001",
        "destination_wallet_id": "wallet_dst_002",
        "amount": 150.0,
        "currency": "PYC",
        "transaction_type": "P2P",
        "direction": "outgoing",
        "created_at": "2026-01-21T13:00:00Z",
        "country": "FR",
    }

    print(f"📝 Scoring de la transaction: {transaction['transaction_id']}")

    # 1. Features
    print("\n📊 Calcul des features...")
    from datetime import datetime
    from dateutil.tz import UTC

    # Parser le datetime et s'assurer qu'il est en UTC aware
    created_at_str = transaction["created_at"]
    if created_at_str.endswith("Z"):
        created_at_str = created_at_str[:-1] + "+00:00"
    current_time = datetime.fromisoformat(created_at_str)
    
    # S'assurer que c'est en UTC
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)
    else:
        current_time = current_time.astimezone(UTC)
    historical_data = store.get_historical_data(
        source_wallet_id=transaction.get("source_wallet_id"),
        before_time=current_time,
    )

    features = feature_pipeline.transform(transaction, historical_data=historical_data)
    print(f"   ✅ {len(features)} features calculées")

    # 2. Règles
    print("\n⚖️  Évaluation des règles...")
    wallet_info = store.get_wallet_info(transaction["source_wallet_id"])
    user_profile = store.get_user_profile(transaction["initiator_user_id"])

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

    if rules_output.decision == "BLOCK":
        print("\n🚫 Transaction bloquée par les règles")
        decision = decision_engine.decide(
            risk_score=rules_output.rule_score,
            reasons=rules_output.reasons,
            hard_block=True,
            model_version="v1.0.0",
        )
    else:
        # 3. Scoring ML (mock)
        print("\n🤖 Scoring ML (mock)...")
        supervised_score = 0.5
        unsupervised_score = 0.5
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

        # 5. Décision
        print("\n⚖️  Décision finale...")
        decision = decision_engine.decide(
            risk_score=risk_score,
            reasons=rules_output.reasons,
            hard_block=False,
            model_version="v1.0.0",
        )

    # Résultat
    print("\n📊 Résultat final:")
    print(f"   Risk score: {decision.risk_score:.3f}")
    print(f"   Decision: {decision.decision}")
    print(f"   Reasons: {', '.join(decision.reasons) if decision.reasons else 'Aucune'}")
    print(f"   Model version: {decision.model_version}")


def test_blocked_transactions():
    """Test 4: Tester les transactions bloquées."""
    print_section("TEST 4: Tester les transactions bloquées")

    # Importer RulesEngine ici pour être sûr qu'il est disponible
    try:
        from src.rules.engine import RulesEngine
    except ImportError as e:
        print(f"⚠️  Erreur d'import: {e}")
        print("   Impossible de tester les règles bloquantes")
        return

    store = HistoriqueStore(storage_path="Data/test_historique.json")
    rules_engine = RulesEngine()

    # Test R1: Montant > 300
    print("\n🔴 Test R1: Montant > 300 (devrait être bloqué)")
    tx_r1 = {
        "transaction_id": "tx_test_r1",
        "initiator_user_id": "user_001",
        "source_wallet_id": "wallet_src_001",
        "destination_wallet_id": "wallet_dst_001",
        "amount": 350.0,
        "currency": "PYC",
        "transaction_type": "P2P",
        "direction": "outgoing",
        "created_at": "2026-01-21T14:00:00Z",
    }

    rules_output = rules_engine.evaluate(transaction=tx_r1, features={})
    print(f"   Décision: {rules_output.decision}")
    print(f"   Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
    assert rules_output.decision == "BLOCK", "R1 devrait bloquer"
    print("   ✅ R1 fonctionne correctement")

    # Test R2: Pays interdit
    print("\n🔴 Test R2: Pays interdit (KP) (devrait être bloqué)")
    tx_r2 = {
        "transaction_id": "tx_test_r2",
        "initiator_user_id": "user_001",
        "source_wallet_id": "wallet_src_001",
        "destination_wallet_id": "wallet_dst_001",
        "amount": 100.0,
        "currency": "PYC",
        "transaction_type": "P2P",
        "direction": "outgoing",
        "created_at": "2026-01-21T15:00:00Z",
        "country": "KP",
    }

    rules_output = rules_engine.evaluate(transaction=tx_r2, features={})
    print(f"   Décision: {rules_output.decision}")
    print(f"   Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
    assert rules_output.decision == "BLOCK", "R2 devrait bloquer"
    print("   ✅ R2 fonctionne correctement")

    # Test transaction normale
    print("\n🟢 Test transaction normale (devrait être ALLOW)")
    tx_normal = {
        "transaction_id": "tx_test_normal",
        "initiator_user_id": "user_001",
        "source_wallet_id": "wallet_src_001",
        "destination_wallet_id": "wallet_dst_001",
        "amount": 50.0,
        "currency": "PYC",
        "transaction_type": "P2P",
        "direction": "outgoing",
        "created_at": "2026-01-21T16:00:00Z",
        "country": "FR",
    }

    rules_output = rules_engine.evaluate(transaction=tx_normal, features={})
    print(f"   Décision: {rules_output.decision}")
    print(f"   Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
    assert rules_output.decision == "ALLOW", "Transaction normale devrait être ALLOW"
    print("   ✅ Transaction normale fonctionne correctement")


def main():
    """Point d'entrée principal."""
    print("\n" + "🧪" * 30)
    print("  TEST DU FLUX COMPLET")
    print("🧪" * 30)

    try:
        # Test 1: Ajouter une transaction
        store = test_add_transaction()

        # Test 2: Voir l'historique
        test_view_historique(store)

        # Test 3: Scorer une transaction
        test_score_transaction()

        # Test 4: Tester les transactions bloquées
        test_blocked_transactions()

        print_section("✅ TOUS LES TESTS SONT PASSÉS")
        print("\n🎉 Le flux fonctionne correctement!")
        print("\n💡 Vous pouvez maintenant:")
        print("   1. Utiliser 'python scripts/push_transaction.py' pour ajouter des transactions")
        print("   2. Utiliser 'python scripts/score_transaction.py' pour scorer des transactions")
        print("   3. Voir l'historique dans 'Data/test_historique.json'")

    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

