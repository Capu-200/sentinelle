#!/usr/bin/env python3
"""
Script principal pour scorer une transaction.

Ce script orchestre tout le pipeline de scoring :
1. Feature Engineering (depuis transaction enrichie ou simple)
2. Règles métier
3. Scoring ML (supervisé + non supervisé)
4. Score global
5. Décision finale

Usage:
    python scripts/score_transaction.py <transaction.json>
    python scripts/score_transaction.py <enriched_transaction.json>
    
Le script détecte automatiquement le format (enrichi ou simple).
Pour le format enrichi, les features sont pré-calculées côté backend.
Pour le format simple (legacy), les features sont calculées localement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.pipeline import FeaturePipeline
from src.rules.engine import RulesEngine
from src.scoring.decision import DecisionEngine
from src.scoring.scorer import GlobalScorer

# Import conditionnel pour le format legacy
try:
    from src.data.historique_store import HistoriqueStore
    HAS_LEGACY_SUPPORT = True
except ImportError:
    HAS_LEGACY_SUPPORT = False


def load_transaction_from_file(file_path: Path) -> dict:
    """Charge une transaction depuis un fichier JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_enriched_transaction(transaction: dict) -> bool:
    """
    Détecte si la transaction est au format enrichi.
    
    Format enrichi : contient "features" et "context"
    Format simple : transaction de base uniquement
    """
    return "features" in transaction and "context" in transaction


def extract_context_from_enriched(enriched_transaction: dict) -> dict:
    """
    Extrait le contexte depuis une transaction enrichie.
    
    Args:
        enriched_transaction: Transaction enrichie
        
    Returns:
        Context pour les règles
    """
    context_data = enriched_transaction.get("context", {})
    
    return {
        "wallet_info": context_data.get("source_wallet", {}),
        "user_profile": context_data.get("user", {}),
        "destination_wallet_info": context_data.get("destination_wallet", {}),
        "account_age_minutes": context_data.get("source_wallet", {}).get("account_age_minutes"),
    }


def extract_transaction_from_enriched(enriched_transaction: dict) -> dict:
    """
    Extrait la transaction de base depuis une transaction enrichie.
    
    Args:
        enriched_transaction: Transaction enrichie
        
    Returns:
        Transaction de base
    """
    return enriched_transaction.get("transaction", enriched_transaction)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Score une transaction")
    parser.add_argument(
        "transaction_file",
        nargs="?",
        type=Path,
        help="Chemin vers le fichier JSON contenant la transaction (enrichie ou simple)",
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

    args = parser.parse_args()

    # Charger la transaction
    if not args.transaction_file:
        parser.print_help()
        sys.exit(1)
    
    if not args.transaction_file.exists():
        print(f"Erreur: Le fichier {args.transaction_file} n'existe pas", file=sys.stderr)
        sys.exit(1)
    
    transaction_data = load_transaction_from_file(args.transaction_file)

    # Détecter le format
    is_enriched = is_enriched_transaction(transaction_data)
    
    if is_enriched:
        print("📦 Format détecté: Transaction enrichie (features pré-calculées)")
        transaction = extract_transaction_from_enriched(transaction_data)
        context = extract_context_from_enriched(transaction_data)
    else:
        print("⚠️  Format détecté: Transaction simple (legacy - features calculées localement)")
        print("   Note: Utilisez le format enrichi pour la production")
        transaction = transaction_data
        context = None  # Sera calculé si nécessaire (legacy)

    # Valider la transaction de base
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
        print("\n🔧 Initialisation des composants...")
        feature_pipeline = FeaturePipeline()
        rules_engine = RulesEngine(config_path=args.rules_config)
        scorer = GlobalScorer(config_path=args.scoring_config)
        decision_engine = DecisionEngine(config_path=args.decision_config)

        tx_id = transaction.get("transaction_id", "N/A")
        
        # 1. Feature Engineering
        print(f"\n📊 Extraction/Calcul des features (tx_id: {tx_id})...")
        
        if is_enriched:
            # Format enrichi : le pipeline extrait depuis transaction_data
            features = feature_pipeline.transform(transaction_data, historical_data=None)
        else:
            # Format legacy : calculer les features (nécessite historique_store)
            if not HAS_LEGACY_SUPPORT:
                print("Erreur: Format legacy nécessite historique_store (non disponible)", file=sys.stderr)
                sys.exit(1)
            
            from datetime import datetime
            from dateutil.tz import UTC
            
            store = HistoriqueStore(storage_path="Data/historique.json")
            
            # Parser le datetime
            created_at_str = transaction["created_at"]
            if created_at_str.endswith("Z"):
                created_at_str = created_at_str[:-1] + "+00:00"
            current_time = datetime.fromisoformat(created_at_str)
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=UTC)
            else:
                current_time = current_time.astimezone(UTC)
            
            # Récupérer l'historique
            historical_data = store.get_historical_data(
                source_wallet_id=transaction.get("source_wallet_id"),
                before_time=current_time,
            )
            
            features = feature_pipeline.transform(transaction, historical_data=historical_data)
            
            # Calculer le context pour les règles (legacy)
            wallet_info = store.get_wallet_info(transaction["source_wallet_id"])
            user_profile = store.get_user_profile(transaction["initiator_user_id"])
            destination_wallet_info = store.get_wallet_info(transaction.get("destination_wallet_id", ""))
            
            # Calculer account_age_minutes
            account_age_minutes = None
            try:
                from dateutil import parser
                tx_time = parser.parse(transaction["created_at"])
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=UTC)
                else:
                    tx_time = tx_time.astimezone(UTC)
                
                wallet_created_str = wallet_info.get("created_at")
                if wallet_created_str:
                    wallet_created = parser.parse(wallet_created_str)
                    if wallet_created.tzinfo is None:
                        wallet_created = wallet_created.replace(tzinfo=UTC)
                    else:
                        wallet_created = wallet_created.astimezone(UTC)
                    delta = tx_time - wallet_created
                    account_age_minutes = delta.total_seconds() / 60
            except Exception:
                pass
            
            context = {
                "wallet_info": wallet_info,
                "user_profile": user_profile,
                "destination_wallet_info": destination_wallet_info,
                "account_age_minutes": account_age_minutes,
            }
        
        print(f"   ✅ {len(features)} features extraites/calculées")

        # 2. Règles métier
        print(f"\n⚖️  Évaluation des règles métier (tx_id: {tx_id})...")

        rules_output = rules_engine.evaluate(
            transaction=transaction,
            features=features,
            context=context,
        )

        print(f"   ✅ Décision règles: {rules_output.decision}")
        print(f"   📋 Raisons: {', '.join(rules_output.reasons) if rules_output.reasons else 'Aucune'}")
        print(f"   📈 Rule score: {rules_output.rule_score:.3f}")
        print(f"   🚀 Boost factor: {rules_output.boost_factor:.2f}")

        # Si BLOCK, arrêter ici
        if rules_output.decision == "BLOCK":
            print(f"\n🚫 TRANSACTION BLOQUÉE par les règles (tx_id: {tx_id})")
            decision = decision_engine.decide(
                risk_score=rules_output.rule_score,
                reasons=rules_output.reasons,
                hard_block=True,
                model_version="v1.0.0",
            )
            print(f"\n📊 Résultat final (tx_id: {tx_id}):")
            print(f"   Transaction ID: {tx_id}")
            print(f"   Risk score: {decision.risk_score:.3f}")
            print(f"   Decision: {decision.decision}")
            print(f"   Reasons: {', '.join(decision.reasons)}")
            print(f"   Model version: {decision.model_version}")
            sys.exit(0)

        # 3. Scoring ML (mock pour l'instant - à implémenter)
        print(f"\n🤖 Scoring ML (tx_id: {tx_id})...")
        # TODO: Implémenter le scoring supervisé et non supervisé
        supervised_score = 0.5  # Mock
        unsupervised_score = 0.5  # Mock
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

        # 5. Décision finale
        print(f"\n⚖️  Décision finale (tx_id: {tx_id})...")
        decision = decision_engine.decide(
            risk_score=risk_score,
            reasons=rules_output.reasons,
            hard_block=False,
            model_version="v1.0.0",
        )

        # Afficher le résultat
        print(f"\n📊 Résultat final (tx_id: {tx_id}):")
        print(f"   Transaction ID: {tx_id}")
        print(f"   Risk score: {decision.risk_score:.3f}")
        print(f"   Decision: {decision.decision}")
        print(f"   Reasons: {', '.join(decision.reasons) if decision.reasons else 'Aucune'}")
        print(f"   Model version: {decision.model_version}")

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
