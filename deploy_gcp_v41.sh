#!/bin/bash
set -e

# ============================================
# Neo-Hack: Gridlock v4.1 — GCP Deployment
# Multi-user scaling with Cloud Run + Redis
# ============================================

PROJECT_ID="webwar-490207"
REGION="europe-west1"
REPO_NAME="neohack-repo"
IMAGE_NAME="backend"
SERVICE_NAME="neohack-gridlock"
SERVICE_ACCOUNT="neohack-backend@${PROJECT_ID}.iam.gserviceaccount.com"
DB_INSTANCE="${PROJECT_ID}:${REGION}:neohack-db"

# v4.1 Multi-User Configuration
MIN_INSTANCES=2
MAX_INSTANCES=20
CONCURRENCY=100
MEMORY="1Gi"
CPU=2
SESSION_AFFINITY="true"
REDIS_INSTANCE="neohack-redis"
VPC_CONNECTOR="neohack-vpc-connector"

VERSION=$(date +v%Y%m%d-%H%M%S)
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${VERSION}"

echo "======================================================="
echo "🚀 Neo-Hack: Gridlock v4.1 — Phantom Mesh Deployment"
echo "   Target: ${SERVICE_NAME} @ ${REGION}"
echo "   Scale: ${MIN_INSTANCES}-${MAX_INSTANCES} instances"
echo "   Concurrency: ${CONCURRENCY} per instance"
echo "======================================================="

# Ensure gcloud CLI is in path
if [ -d "$HOME/google-cloud-sdk/bin" ]; then
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi

# --- Step 1: Build & Push ---
echo ""
echo "📦 1/6 Building Docker image: ${IMAGE_URL}"
docker build -t $IMAGE_URL .

echo "📤 2/6 Pushing image to Artifact Registry..."
docker push $IMAGE_URL

# --- Step 2: Ensure VPC Connector exists (for Redis) ---
echo ""
echo "🔌 3/6 Checking VPC connector for Redis..."
if ! gcloud compute networks vpc-access connectors describe $VPC_CONNECTOR \
    --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
  echo "Creating VPC connector..."
  gcloud compute networks vpc-access connectors create $VPC_CONNECTOR \
    --region=$REGION \
    --network=default \
    --range=10.8.0.0/28 \
    --min-instances=2 \
    --max-instances=3 \
    --project=$PROJECT_ID
  echo "VPC connector created."
else
  echo "VPC connector already exists."
fi

# --- Step 3: Ensure Redis Memorystore instance ---
echo ""
echo "🗄️ 3b/6 Checking Redis Memorystore..."
if ! gcloud redis instances describe $REDIS_INSTANCE \
    --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
  echo "Creating Redis Memorystore instance (BASIC, 1GB)..."
  gcloud redis instances create $REDIS_INSTANCE \
    --size=1 \
    --region=$REGION \
    --tier=BASIC \
    --project=$PROJECT_ID
  echo "Redis instance created. Waiting for ready state..."
  sleep 10
else
  echo "Redis instance already exists."
fi

# Get Redis host for env vars
REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE \
  --region=$REGION --project=$PROJECT_ID \
  --format="value(host)" 2>/dev/null || echo "")

# --- Step 4: Database Migrations ---
echo ""
echo "🔄 4/6 Running database migrations..."
if gcloud run jobs describe neohack-migrate --region=$REGION >/dev/null 2>&1; then
  gcloud run jobs update neohack-migrate \
    --image=$IMAGE_URL \
    --region=$REGION \
    --command="alembic" \
    --args="upgrade,head"
else
  gcloud run jobs create neohack-migrate \
    --image=$IMAGE_URL \
    --region=$REGION \
    --service-account=$SERVICE_ACCOUNT \
    --add-cloudsql-instances=$DB_INSTANCE \
    --set-secrets="DATABASE_URL=db-connection-string:latest" \
    --command="alembic" \
    --args="upgrade,head"
fi
gcloud run jobs execute neohack-migrate --region=$REGION --wait

# --- Step 5: Deploy to Cloud Run with scaling ---
echo ""
echo "🌐 5/6 Deploying to Cloud Run with multi-user scaling..."

DEPLOY_ENV_VARS="WEB_BUILD_DIR=/app/static"
if [ -n "$REDIS_HOST" ]; then
  DEPLOY_ENV_VARS="${DEPLOY_ENV_VARS},REDIS_HOST=${REDIS_HOST},REDIS_PORT=6379"
fi

gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_URL \
  --region=$REGION \
  --platform=managed \
  --project=$PROJECT_ID \
  --service-account=$SERVICE_ACCOUNT \
  --add-cloudsql-instances=$DB_INSTANCE \
  --vpc-connector=$VPC_CONNECTOR \
  --set-env-vars="$DEPLOY_ENV_VARS" \
  --set-secrets="DATABASE_URL=db-connection-string:latest,JWT_SECRET=jwt-secret:latest,GOOGLE_API_KEY=google-api-key:latest" \
  --min-instances=$MIN_INSTANCES \
  --max-instances=$MAX_INSTANCES \
  --concurrency=$CONCURRENCY \
  --memory=$MEMORY \
  --cpu=$CPU \
  --session-affinity \
  --allow-unauthenticated

# --- Step 6: Setup Monitoring ---
echo ""
echo "📊 6/6 Configuring monitoring alerts..."

# Create uptime check if not exists
UPTIME_CHECK="neohack-v41-health"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

if ! gcloud monitoring uptime list-configs --filter="displayName=${UPTIME_CHECK}" --project=$PROJECT_ID 2>/dev/null | grep -q "$UPTIME_CHECK"; then
  echo "Creating uptime check for ${SERVICE_URL}/api/health..."
  gcloud monitoring uptime create "$UPTIME_CHECK" \
    --resource-type="uptime-url" \
    --hostname="${SERVICE_URL#https://}" \
    --path="/api/health" \
    --period=60 \
    --project=$PROJECT_ID 2>/dev/null || echo "Note: Uptime check creation requires console or API"
fi

echo ""
echo "======================================================="
echo "✅ v4.1 Phantom Mesh deployment complete!"
echo "======================================================="
echo "🔗 Service URL: ${SERVICE_URL}"
echo "📊 Instances: ${MIN_INSTANCES}-${MAX_INSTANCES}"
echo "🔧 Concurrency: ${CONCURRENCY}/instance"
echo "💾 Redis: ${REDIS_HOST:-'not configured'}"
echo "======================================================="
