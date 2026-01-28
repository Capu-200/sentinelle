@echo off
set PROJECT_ID=sentinelle-485209
set REGION=europe-west1
set SERVICE_NAME=sentinelle-api-backend
set DB_INSTANCE=sentinelle-db
set DB_USER=fraud_user
set DB_PASS=MaSuperBase2024!Secure
set DB_NAME=fraud_db
set CONNECTION_NAME=sentinelle-485209:europe-west1:sentinelle-db

echo 🚀 Starting Deployment for %SERVICE_NAME%...

echo 📦 Building Container Image...
call gcloud builds submit --tag gcr.io/%PROJECT_ID%/%SERVICE_NAME% . --project %PROJECT_ID%

echo 🚀 Deploying to Cloud Run...
call gcloud run deploy %SERVICE_NAME% ^
  --image gcr.io/%PROJECT_ID%/%SERVICE_NAME% ^
  --platform managed ^
  --region %REGION% ^
  --project %PROJECT_ID% ^
  --allow-unauthenticated ^
  --add-cloudsql-instances %CONNECTION_NAME% ^
  --set-env-vars "DATABASE_URL=postgresql+psycopg2://%DB_USER%:%DB_PASS%@/%DB_NAME%?host=/cloudsql/%CONNECTION_NAME%" ^
  --set-env-vars "ML_ENGINE_URL=https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app"

echo ✨ Deployment Complete!
