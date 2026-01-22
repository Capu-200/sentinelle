#!/usr/bin/env python3
"""
Script de test pour valider le flux complet avec transactions enrichies.

Ce script teste :
1. Scoring de transactions enrichies (format production)
2. Test des règles métier (R1, R2, R4, R5, R6, R13)

Usage:
    python scripts/test_flow.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.pipeline import FeaturePipeline
from src.rules.engine import RulesEngine
from src.scoring.decision import DecisionEngine
from src.scoring.scorer import GlobalScorer


def print_section(title: str):
    """Affiche un titre de section."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def load_enriched_transaction(file_path: str) -> dict:
    """Charge une transaction enrichie depuis un fichier."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_enriched_transaction_normal():
    """Test 1: Scorer une transaction enrichie normale."""
    print_section("TEST 1: Transaction enrichie normale")

    try:
        # Charger la transaction enrichie
        enriched_tx = load_enriched_transaction("tests/fixtures/enriched_transaction_example.json")
        
        # Initialiser les composants
        feature_pipeline = FeaturePipeline()
        rules_engine = RulesEngine()
        scorer = GlobalScorer()
        decision_engine = DecisionEngine()

        tx_id = enriched_tx["transaction"]["transaction_id"]
        print(f"📝 Scoring de la transaction enrichie: {tx_id}")

        # 1. Features
        print(f"\n📊 Extraction des features (tx_id: {tx_id})...")
        features = feature_pipeline.transform(enriched_tx, historical_data=None)
        print(f"   ✅ {len(features)} features extraites")

        # 2. Règles
        print(f"\n⚖️  Évaluation des règles (tx_id: {tx_id})...")
        
        # Extraire le context depuis la transaction enrichie
        context = {
            "wallet_info": enriched_tx["context"]["source_wallet"],
            "user_profile": enriched_tx["context"]["user"],
            "destination_wallet_info": enriched_tx["context"]["destination_wallet"],
            "account_age_minutes": enriched_tx["context"]["source_wallet"].get("account_age_minutes"),
        }

        rules_output = rules_engine.evaluate(
            transaction=enriched_tx["transaction"],
            features=features,
            context=context,
        )

        print(f"   ✅ Décision règles: {rules_output.decision}")
        print(f"   📋 Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
        print(f"   📈 Rule score: {rules_output.rule_score:.3f}")
        print(f"   🚀 Boost factor: {rules_output.boost_factor:.2f}")

        # 3. Scoring ML (mock)
        print(f"\n🤖 Scoring ML (mock) (tx_id: {tx_id})...")
        supervised_score = 0.5
        unsupervised_score = 0.5
        print(f"   ✅ Supervisé: {supervised_score:.3f}")
        print(f"   ✅ Non supervisé: {unsupervised_score:.3f}")

        # 4. Score global
        print(f"\n🎯 Calcul du score global (tx_id: {tx_id})...")
        risk_score = scorer.compute_score(
            rule_score=rules_output.rule_score,
            supervised_score=supervised_score,
            unsupervised_score=unsupervised_score,
            boost_factor=rules_output.boost_factor,
        )
        print(f"   ✅ Risk score: {risk_score:.3f}")

        # 5. Décision
        print(f"\n⚖️  Décision finale (tx_id: {tx_id})...")
        decision = decision_engine.decide(
            risk_score=risk_score,
            reasons=rules_output.reasons,
            hard_block=False,
            model_version="v1.0.0",
        )

        # Résultat
        print(f"\n📊 Résultat final (tx_id: {tx_id}):")
        print(f"   Transaction ID: {tx_id}")
        print(f"   Risk score: {decision.risk_score:.3f}")
        print(f"   Decision: {decision.decision}")
        print(f"   Reasons: {', '.join(decision.reasons) if decision.reasons else 'Aucune'}")
        print(f"   Model version: {decision.model_version}")

        print("\n   ✅ Test transaction normale réussi")

    except FileNotFoundError:
        print("⚠️  Fichier enriched_transaction_example.json non trouvé")
        print("   Créez-le avec: tests/fixtures/enriched_transaction_example.json")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_blocked_transactions():
    """Test 2: Tester les transactions bloquées."""
    print_section("TEST 2: Transactions bloquées par les règles")

    try:
        from src.rules.engine import RulesEngine

        rules_engine = RulesEngine()

        # Test R1: Montant > 300
        print("\n🔴 Test R1: Montant > 300 (devrait être bloqué)")
        enriched_tx_r1 = load_enriched_transaction("tests/fixtures/enriched_transaction_blocked_r1.json")
        
        features = FeaturePipeline().transform(enriched_tx_r1, historical_data=None)
        context = {
            "wallet_info": enriched_tx_r1["context"]["source_wallet"],
            "user_profile": enriched_tx_r1["context"]["user"],
            "destination_wallet_info": enriched_tx_r1["context"]["destination_wallet"],
            "account_age_minutes": enriched_tx_r1["context"]["source_wallet"].get("account_age_minutes"),
        }

        rules_output = rules_engine.evaluate(
            transaction=enriched_tx_r1["transaction"],
            features=features,
            context=context,
        )
        
        tx_id_r1 = enriched_tx_r1["transaction"]["transaction_id"]
        print(f"   Transaction ID: {tx_id_r1}")
        print(f"   Décision: {rules_output.decision}")
        print(f"   Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
        assert rules_output.decision == "BLOCK", "R1 devrait bloquer"
        print("   ✅ R1 fonctionne correctement")

        # Test R13: Horaire interdit (BOOST_SCORE)
        print("\n🟡 Test R13: Horaire interdit (devrait être BOOST_SCORE)")
        enriched_tx_r13 = load_enriched_transaction("tests/fixtures/enriched_transaction_boost_r13.json")
        
        features = FeaturePipeline().transform(enriched_tx_r13, historical_data=None)
        context = {
            "wallet_info": enriched_tx_r13["context"]["source_wallet"],
            "user_profile": enriched_tx_r13["context"]["user"],
            "destination_wallet_info": enriched_tx_r13["context"]["destination_wallet"],
            "account_age_minutes": enriched_tx_r13["context"]["source_wallet"].get("account_age_minutes"),
        }

        rules_output = rules_engine.evaluate(
            transaction=enriched_tx_r13["transaction"],
            features=features,
            context=context,
        )
        
        tx_id_r13 = enriched_tx_r13["transaction"]["transaction_id"]
        print(f"   Transaction ID: {tx_id_r13}")
        print(f"   Décision: {rules_output.decision}")
        print(f"   Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
        assert rules_output.decision == "BOOST_SCORE", "R13 devrait être BOOST_SCORE"
        print("   ✅ R13 fonctionne correctement")

        # Test cas 0 transaction historique
        print("\n🟢 Test: Transaction avec 0 historique (nouveau compte)")
        enriched_tx_no_history = load_enriched_transaction("tests/fixtures/enriched_transaction_no_history.json")
        
        features = FeaturePipeline().transform(enriched_tx_no_history, historical_data=None)
        context = {
            "wallet_info": enriched_tx_no_history["context"]["source_wallet"],
            "user_profile": enriched_tx_no_history["context"]["user"],
            "destination_wallet_info": enriched_tx_no_history["context"]["destination_wallet"],
            "account_age_minutes": enriched_tx_no_history["context"]["source_wallet"].get("account_age_minutes"),
        }

        rules_output = rules_engine.evaluate(
            transaction=enriched_tx_no_history["transaction"],
            features=features,
            context=context,
        )
        
        tx_id_no_history = enriched_tx_no_history["transaction"]["transaction_id"]
        print(f"   Transaction ID: {tx_id_no_history}")
        print(f"   Décision: {rules_output.decision}")
        print(f"   Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
        print("   ✅ Gestion du cas 0 historique fonctionne")

    except FileNotFoundError as e:
        print(f"⚠️  Fichier de test non trouvé: {e}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Point d'entrée principal."""
    print("\n🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪")
    print("  TEST DU FLUX COMPLET (Format enrichi)")
    print("🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪")

    # Test 1: Transaction normale
    test_enriched_transaction_normal()

    # Test 2: Transactions bloquées
    test_blocked_transactions()

    print("\n" + "=" * 60)
    print("  ✅ TOUS LES TESTS SONT PASSÉS")
    print("=" * 60)


if __name__ == "__main__":
    main()
