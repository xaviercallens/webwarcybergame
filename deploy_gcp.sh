#!/bin/bash
set -e

# Configuration
PROJECT_ID="webwar-490207"
REGION="europe-west1"
REPO_NAME="neohack-repo"
IMAGE_NAME="backend"
SERVICE_NAME="neohack-gridlock"
SERVICE_ACCOUNT="neohack-backend@${PROJECT_ID}.iam.gserviceaccount.com"
DB_INSTANCE="${PROJECT_ID}:${REGION}:neohack-db"

# Format version tag with date and time to ensure uniqueness
VERSION=$(date +v%Y%m%d-%H%M%S)
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${VERSION}"

echo "======================================================="
echo "🚀 Starting deployment for ${SERVICE_NAME}"
echo "======================================================="

# Ensure gcloud CLI is in path (useful if run from scripts without profile loaded)
if [ -d "$HOME/google-cloud-sdk/bin" ]; then
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi

echo "📦 1. Building Docker image: ${IMAGE_URL}"
docker build -t $IMAGE_URL .

echo "📤 2. Pushing image to Artifact Registry..."
docker push $IMAGE_URL

echo "🔄 3. Running database migrations via Cloud Run Job..."
# Create or update the Cloud Run Job for migrations
# We suppress the error if it already exists, and we update it to use the new image
if gcloud run jobs describe neohack-migrate --region=$REGION >/dev/null 2>&1; then
  echo "Updating existing migration job..."
  gcloud run jobs update neohack-migrate \
    --image=$IMAGE_URL \
    --region=$REGION \
    --command="alembic" \
    --args="upgrade,head"
else
  echo "Creating new migration job..."
  gcloud run jobs create neohack-migrate \
    --image=$IMAGE_URL \
    --region=$REGION \
    --service-account=$SERVICE_ACCOUNT \
    --add-cloudsql-instances=$DB_INSTANCE \
    --set-secrets="DATABASE_URL=db-connection-string:latest" \
    --command="alembic" \
    --args="upgrade,head"
fi

# Execute the migration job
gcloud run jobs execute neohack-migrate --region=$REGION --wait

echo "🌐 4. Deploying to Cloud Run Service..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_URL \
  --region=$REGION \
  --platform=managed \
  --project=$PROJECT_ID \
  --service-account=$SERVICE_ACCOUNT \
  --add-cloudsql-instances=$DB_INSTANCE \
  --set-env-vars="WEB_BUILD_DIR=/app/static" \
  --set-secrets="DATABASE_URL=db-connection-string:latest,JWT_SECRET=jwt-secret:latest" \
  --allow-unauthenticated

echo "======================================================="
echo "✅ Deployment complete!"
echo "🔗 Service URL:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
echo "======================================================="
