$ErrorActionPreference = "Stop"

$PROJECT_ID = "sentinelle-485209"
$REGION = "europe-west1"
$SERVICE_NAME = "sentinelle-api-backend"
$DB_INSTANCE = "sentinelle-db"
$DB_USER = "fraud_user"
$DB_PASS = "MaSuperBase2024!Secure"
$DB_NAME = "fraud_db"

# Force Connection Name directly (since previous method had a CLI parsing issue inside PowerShell)
$CONNECTION_NAME = "sentinelle-485209:europe-west1:sentinelle-db"

Write-Host "🚀 Starting Deployment for $SERVICE_NAME..." -ForegroundColor Green
Write-Host "✅ Connection Name: $CONNECTION_NAME"

# 2. Build Container
Write-Host "📦 Building Container Image (via Cloud Build)... (This will take 1-2 mins)"
# Use cmd /c to ensure arguments are passed correctly to gcloud from PowerShell
cmd /c "gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME . --project $PROJECT_ID"

# 3. Deploy
Write-Host "🚀 Deploying to Cloud Run..."
cmd /c "gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --allow-unauthenticated --add-cloudsql-instances $CONNECTION_NAME --set-env-vars ""DATABASE_URL=postgresql+psycopg2://$($DB_USER):$($DB_PASS)@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME,ML_ENGINE_URL=https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app"""

Write-Host "✨ Deployment Complete!" -ForegroundColor Green
