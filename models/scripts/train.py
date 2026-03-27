"""
Script principal d'entraînement du pipeline ML complet.

Orchestre :
1. Préparation (split temporel)
2. Feature engineering
3. Entraînement supervisé
4. Entraînement non supervisé
5. Calibration des seuils
6. Sauvegarde des artefacts
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, average_precision_score, f1_score

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.preparation import prepare_training_data
from src.features.training import compute_features_for_dataset
from src.models.supervised.train import train_supervised_model
from src.models.unsupervised.train import train_unsupervised_model
from src.utils.versioning import save_artifacts
from src.scoring.scorer import GlobalScorer


def _convert_features_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convertit toutes les colonnes du DataFrame en types numériques (int, float, bool).
    
    LightGBM n'accepte que ces types. Les colonnes object sont converties :
    - Si booléennes → bool
    - Sinon → float (avec gestion des NaN)
    """
    df_converted = df.copy()
    
    for col in df_converted.columns:
        dtype = df_converted[col].dtype
        
        if dtype == 'object':
            # Essayer de convertir en bool d'abord
            if df_converted[col].isin([True, False, 'True', 'False', 1, 0, '1', '0']).all():
                df_converted[col] = df_converted[col].astype(bool)
            else:
                # Convertir en float (les NaN resteront NaN, mais LightGBM les gère)
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce').fillna(0.0)
        elif dtype.name.startswith('datetime'):
            # Les dates doivent être converties en features numériques (ex: timestamp)
            df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce').fillna(0.0)
    
    return df_converted


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Entraînement du pipeline ML")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.getenv("DATA_DIR", "Data/processed")),
        help="Dossier contenant les données nettoyées (ou variable DATA_DIR)",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("configs"),
        help="Dossier contenant les configurations",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path(os.getenv("ARTIFACTS_DIR", "artifacts")),
        help="Dossier où sauvegarder les artefacts (ou variable ARTIFACTS_DIR)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.0.0",
        help="Version du modèle (SemVer)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Mode local: utilise tous les cores et dataset complet (pas d'échantillonnage)",
    )
    parser.add_argument(
        "--train-split-date",
        type=str,
        help="Date de fin du set d'entraînement (ISO format)",
    )
    parser.add_argument(
        "--val-split-date",
        type=str,
        help="Date de fin du set de validation (ISO format)",
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=None,
        help="Mode test: limiter PaySim aux N transactions les plus récentes (pour tests rapides)",
    )

    args = parser.parse_args()

    # MLflow : activé si MLFLOW_EXPERIMENT_NAME ou MLFLOW_TRACKING_URI est défini
    use_mlflow = bool(os.getenv("MLFLOW_EXPERIMENT_NAME") or os.getenv("MLFLOW_TRACKING_URI"))
    if use_mlflow:
        import mlflow
        exp_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "/Shared/Sentinelle Production")
        mlflow.set_experiment(exp_name)
        mlflow.start_run(run_name=f"train-v{args.version}")
        mlflow.log_params({
            "version": args.version,
            "local": str(args.local),
            "data_dir": str(args.data_dir),
            "config_dir": str(args.config_dir),
            "artifacts_dir": str(args.artifacts_dir),
        })
        if args.test_size:
            mlflow.log_param("test_size", args.test_size)
        print(f"📊 MLflow: run démarré (experiment: {exp_name})")

    print(f"🚀 Démarrage de l'entraînement (version {args.version})")
    print(f"📁 Données : {args.data_dir}")
    print(f"⚙️  Config : {args.config_dir}")
    print(f"💾 Artefacts : {args.artifacts_dir}")
    print()

    # ========== 1. PRÉPARATION DES DONNÉES ==========
    print("=" * 60)
    print("ÉTAPE 1: Préparation des données")
    print("=" * 60)
    
    # Dataset PaySim (supervisé)
    paysim_path = args.data_dir / "paysim_mapped.csv"
    if not paysim_path.exists():
        raise FileNotFoundError(f"Dataset PaySim non trouvé: {paysim_path}")
    
    print(f"📊 Chargement PaySim: {paysim_path}")
    paysim_df = pd.read_csv(paysim_path)
    paysim_df["created_at"] = pd.to_datetime(paysim_df["created_at"], utc=True)
    print(f"   ✅ {len(paysim_df)} transactions chargées")
    
    # Mode test : limiter aux N transactions les plus récentes
    if args.test_size is not None:
        print(f"\n🧪 MODE TEST: Limitation à {args.test_size:,} transactions les plus récentes")
        # Trier par date (plus récentes en dernier) et prendre les N dernières
        paysim_df = paysim_df.sort_values("created_at").tail(args.test_size).reset_index(drop=True)
        print(f"   ✅ Dataset limité à {len(paysim_df):,} transactions")
        print(f"   📅 Période: {paysim_df['created_at'].min()} → {paysim_df['created_at'].max()}")
    
    # Split temporel PaySim (utilise le DataFrame déjà chargé pour éviter le rechargement)
    print(f"\n📊 Split temporel PaySim...")
    paysim_train, paysim_val, paysim_test = prepare_training_data(
        paysim_df,  # Passe le DataFrame directement (optimisation)
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
    )
    
    # Dataset Payon Legit (non supervisé)
    payon_path = args.data_dir / "payon_legit_clean.csv"
    if not payon_path.exists():
        raise FileNotFoundError(f"Dataset Payon non trouvé: {payon_path}")
    
    print(f"\n📊 Chargement Payon Legit: {payon_path}")
    payon_df = pd.read_csv(payon_path)
    payon_df["created_at"] = pd.to_datetime(payon_df["created_at"], utc=True)
    print(f"   ✅ {len(payon_df)} transactions chargées")

    # Mode test : limiter Payon aussi (même limite que PaySim)
    if args.test_size is not None:
        payon_df = payon_df.sort_values("created_at").tail(args.test_size).reset_index(drop=True)
        print(f"   ✅ Payon limité à {len(payon_df):,} transactions (mode test)")
    
    # Split temporel Payon (utilise le DataFrame déjà chargé pour éviter le rechargement)
    print(f"\n📊 Split temporel Payon...")
    payon_train, payon_val, payon_test = prepare_training_data(
        payon_df,  # Passe le DataFrame directement (optimisation)
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
    )
    
    # ========== 2. FEATURE ENGINEERING ==========
    print("\n" + "=" * 60)
    print("ÉTAPE 2: Feature Engineering")
    print("=" * 60)
    
    # Déterminer le nombre de jobs
    import multiprocessing as mp
    n_cores = mp.cpu_count()
    
    if args.local:
        # Mode local: utiliser tous les cores disponibles (optimisé pour 10 cores / 32GB RAM)
        n_jobs = max(1, n_cores - 1)  # Laisser 1 core libre
        use_full_dataset = True
        print(f"\n⚙️  Configuration LOCAL: {n_jobs} processus parallèles (sur {n_cores} cores)")
        print(f"   💡 Mode local: dataset complet, pas d'échantillonnage")
    else:
        # Mode Cloud: réduire pour éviter OOM
        n_jobs = min(5, max(1, n_cores - 2))  # Max 5 processus, laisser 2 cores libres
        use_full_dataset = False
        print(f"\n⚙️  Configuration CLOUD: {n_jobs} processus parallèles (sur {n_cores} cores)")
        print(f"   💡 Mode Cloud: échantillonnage activé pour éviter timeout")
    
    # Features pour PaySim (supervisé)
    if use_full_dataset:
        # Mode local: utiliser le dataset complet
        paysim_train_sample = paysim_train
        print(f"\n🔧 Calcul des features PaySim (train) - DATASET COMPLET...")
        print(f"   📊 {len(paysim_train_sample):,} transactions (dataset complet)")
    else:
        # Mode Cloud: échantillonnage pour accélérer
        paysim_train_sample = paysim_train.sample(
            n=min(500000, len(paysim_train)),
            random_state=42
        ).sort_values("created_at").reset_index(drop=True)
        print(f"\n🔧 Calcul des features PaySim (train)...")
        print(f"   ⚠️  Échantillon: {len(paysim_train_sample):,} transactions (sur {len(paysim_train):,})")
        print(f"   💡 Pour l'entraînement complet, utiliser --local")
    
    paysim_train_features = compute_features_for_dataset(
        paysim_train_sample,
        verbose=True,
        n_jobs=n_jobs,
        chunk_size=1000,  # Chunks de 1000 transactions pour éviter la surcharge mémoire
    )
    paysim_train_labels = paysim_train_sample["is_fraud"] if "is_fraud" in paysim_train.columns else None
    
    print(f"\n🔧 Calcul des features PaySim (val)...")
    paysim_val_features = compute_features_for_dataset(
        paysim_val,
        verbose=True,
        n_jobs=n_jobs,
        chunk_size=1000,
    )
    paysim_val_labels = paysim_val["is_fraud"] if "is_fraud" in paysim_val.columns else None
    
    # Features pour Payon (non supervisé)
    print(f"\n🔧 Calcul des features Payon (train)...")
    payon_train_features = compute_features_for_dataset(
        payon_train,
        verbose=True,
        n_jobs=n_jobs,
        chunk_size=1000,
    )
    
    print(f"\n🔧 Calcul des features Payon (val)...")
    payon_val_features = compute_features_for_dataset(
        payon_val,
        verbose=True,
        n_jobs=n_jobs,
        chunk_size=1000,
    )
    
    print(f"\n✅ Features calculées:")
    print(f"   PaySim train: {len(paysim_train_features)} transactions, {len(paysim_train_features.columns)} features")
    print(f"   PaySim val: {len(paysim_val_features)} transactions, {len(paysim_val_features.columns)} features")
    print(f"   Payon train: {len(payon_train_features)} transactions, {len(payon_train_features.columns)} features")
    print(f"   Payon val: {len(payon_val_features)} transactions, {len(payon_val_features.columns)} features")
    
    # ========== 3. ENTRAÎNEMENT SUPERVISÉ ==========
    print("\n" + "=" * 60)
    print("ÉTAPE 3: Entraînement Modèle Supervisé (LightGBM)")
    print("=" * 60)
    
    if paysim_train_labels is None:
        print("⚠️  Pas de labels dans PaySim, skip entraînement supervisé")
        supervised_model = None
    else:
        print(f"📊 Entraînement sur {len(paysim_train_features)} transactions")
        print(f"   Fraudes: {paysim_train_labels.sum()} ({paysim_train_labels.mean()*100:.2f}%)")
        
        # Convertir toutes les colonnes en types numériques (LightGBM n'accepte que int, float, bool)
        print("🔧 Conversion des types de features pour LightGBM...")
        paysim_train_features = _convert_features_to_numeric(paysim_train_features)
        paysim_val_features = _convert_features_to_numeric(paysim_val_features)
        
        supervised_model = train_supervised_model(
            train_data=paysim_train_features,
            train_labels=paysim_train_labels,
            val_data=paysim_val_features,
            val_labels=paysim_val_labels,
        )
        
        print(f"✅ Modèle supervisé entraîné")

        # Métriques validation pour MLflow
        if use_mlflow and paysim_val_labels is not None:
            val_proba = supervised_model.predict(paysim_val_features)
            val_pred_binary = (val_proba >= 0.5).astype(int)
            mlflow.log_metric("val_accuracy", float(accuracy_score(paysim_val_labels, val_pred_binary)))
            mlflow.log_metric("val_f1", float(f1_score(paysim_val_labels, val_pred_binary, zero_division=0)))
            mlflow.log_metric("val_pr_auc", float(average_precision_score(paysim_val_labels, val_proba)))
    
    # ========== 4. ENTRAÎNEMENT NON SUPERVISÉ ==========
    print("\n" + "=" * 60)
    print("ÉTAPE 4: Entraînement Modèle Non Supervisé (IsolationForest)")
    print("=" * 60)
    
    print(f"📊 Entraînement sur {len(payon_train_features)} transactions (normales uniquement)")
    
    # Convertir toutes les colonnes en types numériques
    print("🔧 Conversion des types de features pour IsolationForest...")
    payon_train_features = _convert_features_to_numeric(payon_train_features)
    # Note: val_data n'est pas utilisé pour IsolationForest (modèle non supervisé)
    
    unsupervised_model = train_unsupervised_model(
        train_data=payon_train_features,
    )
    
    print(f"✅ Modèle non supervisé entraîné")
    
    # ========== 5. CALIBRATION DES SEUILS ==========
    print("\n" + "=" * 60)
    print("ÉTAPE 5: Calibration des Seuils")
    print("=" * 60)
    
    # Calculer les scores sur le validation set
    if supervised_model and paysim_val_labels is not None:
        supervised_scores = supervised_model.predict(paysim_val_features)
    else:
        supervised_scores = None
    
    # Pour le score non supervisé, on utilise Payon val (transactions normales)
    unsupervised_scores = unsupervised_model.predict(payon_val_features)
    
    # Calculer le SCORE GLOBAL (comme en production) pour calibrer les seuils
    # Le score global combine : règles (20%) + supervisé (60%) + non supervisé (20%)
    global_scorer = GlobalScorer()
    
    if supervised_scores is not None and len(supervised_scores) > 0:
        # Calculer le score global pour chaque transaction du validation set
        # Pour la calibration, on simule rule_score=0 (pas de règles déclenchées)
        # et on combine supervisé + non supervisé
        min_len = min(len(supervised_scores), len(unsupervised_scores))
        supervised_scores_aligned = supervised_scores.iloc[:min_len]
        unsupervised_scores_aligned = unsupervised_scores.iloc[:min_len]
        
        global_scores = []
        for i in range(min_len):
            global_score = global_scorer.compute_score(
                rule_score=0.0,  # Pas de règles pour la calibration
                supervised_score=float(supervised_scores_aligned.iloc[i]),
                unsupervised_score=float(unsupervised_scores_aligned.iloc[i]),
                boost_factor=1.0,
            )
            global_scores.append(global_score)
        
        global_scores_series = pd.Series(global_scores)
        
        # Calculer les seuils sur le score global (top 0.1% BLOCK, top 1% REVIEW)
        block_threshold = global_scores_series.quantile(0.999)  # Top 0.1%
        review_threshold = global_scores_series.quantile(0.99)  # Top 1%
        
        print(f"📊 Scores calculés sur {len(global_scores_series)} transactions")
        print(f"   Score global min: {global_scores_series.min():.4f}")
        print(f"   Score global max: {global_scores_series.max():.4f}")
        print(f"   Score global médian: {global_scores_series.median():.4f}")
    else:
        # Fallback : utiliser le score non supervisé uniquement
        print("⚠️  Pas de modèle supervisé, utilisation du score non supervisé uniquement")
        block_threshold = unsupervised_scores.quantile(0.999)
        review_threshold = unsupervised_scores.quantile(0.99)
    
    # Si les seuils sont identiques (dataset trop petit), ajuster
    if abs(block_threshold - review_threshold) < 0.001:
        print("⚠️  Seuils identiques détectés (dataset petit), ajustement...")
        # Utiliser des quantiles plus espacés
        if supervised_scores is not None and len(supervised_scores) > 0:
            review_threshold = global_scores_series.quantile(0.99)
            block_threshold = global_scores_series.quantile(0.995)  # Top 0.5% au lieu de 0.1%
        else:
            review_threshold = unsupervised_scores.quantile(0.99)
            block_threshold = unsupervised_scores.quantile(0.995)
        
        # S'assurer que BLOCK > REVIEW
        if block_threshold <= review_threshold:
            block_threshold = review_threshold + 0.01  # Ajouter un petit écart
    
    thresholds = {
        "block_threshold": float(block_threshold),
        "review_threshold": float(review_threshold),
    }
    
    print(f"✅ Seuils calculés:")
    print(f"   BLOCK threshold: {block_threshold:.4f} (top 0.1-0.5%)")
    print(f"   REVIEW threshold: {review_threshold:.4f} (top 1%)")
    print(f"   💡 En production, une transaction avec score ≥ {block_threshold:.4f} sera BLOCK")
    print(f"   💡 En production, une transaction avec score ≥ {review_threshold:.4f} sera REVIEW")

    if use_mlflow:
        mlflow.log_metric("block_threshold", float(block_threshold))
        mlflow.log_metric("review_threshold", float(review_threshold))
    
    # ========== 6. SAUVEGARDE DES ARTEFACTS ==========
    print("\n" + "=" * 60)
    print("ÉTAPE 6: Sauvegarde des Artefacts")
    print("=" * 60)
    
    # Créer le dossier de version
    version_dir = args.artifacts_dir / f"v{args.version}"
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarder les modèles
    if supervised_model:
        supervised_path = version_dir / "supervised_model.pkl"
        supervised_model.save(supervised_path)
        print(f"✅ Modèle supervisé sauvegardé: {supervised_path}")
    
    unsupervised_path = version_dir / "unsupervised_model.pkl"
    unsupervised_model.save(unsupervised_path)
    print(f"✅ Modèle non supervisé sauvegardé: {unsupervised_path}")
    
    # Sauvegarder les seuils
    thresholds_path = version_dir / "thresholds.json"
    with open(thresholds_path, "w") as f:
        json.dump(thresholds, f, indent=2)
    print(f"✅ Seuils sauvegardés: {thresholds_path}")
    
    # Sauvegarder le schéma de features (liste des colonnes)
    feature_schema = {
        "version": args.version,
        "features": list(paysim_train_features.columns) if supervised_model else list(payon_train_features.columns),
    }
    schema_path = version_dir / "feature_schema.json"
    with open(schema_path, "w") as f:
        json.dump(feature_schema, f, indent=2)
    print(f"✅ Schéma de features sauvegardé: {schema_path}")
    
    # Créer/mettre à jour le symlink latest
    latest_path = args.artifacts_dir / "latest"
    if latest_path.exists():
        latest_path.unlink()
    latest_path.symlink_to(f"v{args.version}")
    print(f"✅ Symlink 'latest' → v{args.version}")

    # MLflow : log des artefacts
    export_bucket = os.getenv("EXPORT_BASELINE_GCS_BUCKET", "").strip()
    if use_mlflow:
        mlflow.log_artifact(str(schema_path))
        mlflow.log_artifact(str(thresholds_path))
        baseline_path = version_dir / "baseline_train.jsonl"
        payon_train_features.head(1000).to_json(
            baseline_path, orient="records", lines=True, date_format="iso"
        )
        mlflow.log_artifact(str(baseline_path))

    # Export baseline Vertex (optionnel) : features d'entraînement vers GCS
    if export_bucket:
        try:
            from google.cloud import storage
            baseline_df = payon_train_features  # distribution "normale" pour drift
            buf = baseline_df.to_json(orient="records", lines=True, date_format="iso")
            prefix = "monitoring/baseline"
            blob_name = f"{prefix}/v{args.version}/train_features.jsonl"
            client = storage.Client()
            bucket = client.bucket(export_bucket)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(buf, content_type="application/json")
            print(f"✅ Baseline Vertex exportée: gs://{export_bucket}/{blob_name}")
        except Exception as e:
            print(f"⚠️  Export baseline GCS ignoré: {e}")

    # ========== RÉSUMÉ ==========
    print("\n" + "=" * 60)
    print("✅ ENTRAÎNEMENT TERMINÉ")
    print("=" * 60)
    print(f"Version: {args.version}")
    print(f"Artefacts: {version_dir}")
    print(f"\nModèles entraînés:")
    if supervised_model:
        print(f"  ✅ Supervisé (LightGBM)")
    print(f"  ✅ Non supervisé (IsolationForest)")
    print(f"\nSeuils:")
    print(f"  BLOCK: {block_threshold:.4f}")
    print(f"  REVIEW: {review_threshold:.4f}")

    if use_mlflow:
        import mlflow
        mlflow.end_run()
        print(f"📊 MLflow: run terminé")


if __name__ == "__main__":
    main()
