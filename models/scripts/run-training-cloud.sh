#!/bin/bash
# Script pour lancer l'entraînement sur Cloud Run Jobs
# Usage: ./scripts/run-training-cloud.sh [PROJECT_ID] [JOB_NAME] [REGION] [VERSION]

set -e

PROJECT_ID=${1:-"sentinelle-485209"}
JOB_NAME=${2:-"sentinelle-training"}
REGION=${3:-"europe-west1"}
VERSION=${4:-"1.0.0"}

echo "🚀 Lancement de l'entraînement sur Cloud Run Jobs..."
echo "   Projet: $PROJECT_ID"
echo "   Job: $JOB_NAME"
echo "   Région: $REGION"
echo "   Version: $VERSION"
echo ""

# Lancer le job
EXECUTION_NAME=$(gcloud run jobs execute "$JOB_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(metadata.name)")

echo "✅ Job lancé!"
echo "   Execution: $EXECUTION_NAME"
echo ""
echo "📊 Suivre les logs en temps réel:"
echo "   gcloud run jobs executions logs tail $EXECUTION_NAME --region=$REGION --project=$PROJECT_ID"
echo ""
echo "Ou attendre la fin et récupérer les logs:"
echo "   gcloud run jobs executions logs read $EXECUTION_NAME --region=$REGION --project=$PROJECT_ID"

