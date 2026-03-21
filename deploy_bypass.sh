#!/bin/bash
set -e

PROJECT_ID="webwar-490207"
REGION="europe-west1"
SERVICE_NAME="neohack-gridlock-v2"
SERVICE_ACCOUNT="neohack-backend@${PROJECT_ID}.iam.gserviceaccount.com"
DB_INSTANCE="${PROJECT_ID}:${REGION}:neohack-db"

# 1. Build Docker image
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/neohack-repo/backend:v${TIMESTAMP}"

echo "📦 1. Building Docker image: $IMAGE_URL"
sudo docker build -t $IMAGE_URL .

# 2. Push Docker image
echo "📤 2. Pushing image to Artifact Registry..."
sudo docker push $IMAGE_URL

# 3. Deploy (Skipping migrations)
echo "🌐 3. Deploying to Cloud Run Service..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_URL \
  --region=$REGION \
  --platform=managed \
  --project=$PROJECT_ID \
  --service-account=$SERVICE_ACCOUNT \
  --add-cloudsql-instances=$DB_INSTANCE \
  --set-env-vars="WEB_BUILD_DIR=/app/static" \
  --set-secrets="DATABASE_URL=db-connection-string:latest,JWT_SECRET=jwt-secret:latest,GOOGLE_API_KEY=google-api-key:latest" \
  --allow-unauthenticated

echo "======================================================="
echo "✅ Bypass Deployment complete!"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
echo "======================================================="
