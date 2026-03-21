#!/bin/bash
set -e

# =============================================================================
# NeoHack Gridlock v3 — Production Deploy Script
# Deploys backend to Cloud Run + frontend to Firebase Hosting
# =============================================================================

PROJECT_ID="webwar-490207"
REGION="europe-west1"
REPO_NAME="neohack-repo"
IMAGE_NAME="backend"
SERVICE_NAME="neohack-v3"
SITE_ID="neohack-v3"
SERVICE_ACCOUNT="neohack-backend@${PROJECT_ID}.iam.gserviceaccount.com"
DB_INSTANCE="${PROJECT_ID}:${REGION}:neohack-db"

SHORT_SHA=$(git rev-parse --short HEAD)
VERSION="v3-${SHORT_SHA}-$(date +%Y%m%d%H%M%S)"
IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${VERSION}"

echo "======================================================="
echo "  NeoHack Gridlock v3 — Production Deploy"
echo "  Branch: $(git branch --show-current)"
echo "  Commit: ${SHORT_SHA}"
echo "  Image:  ${VERSION}"
echo "======================================================="

# Ensure gcloud CLI is in path
if [ -d "$HOME/google-cloud-sdk/bin" ]; then
    export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi

# --- STEP 1: Build frontend ---
echo ""
echo "1/5  Building frontend..."
(cd build/web && npm install --silent && npm run build) 2>&1 | tail -5

# --- STEP 2: Build & push backend via Cloud Build ---
echo ""
echo "2/5  Building backend via Cloud Build..."
gcloud builds submit \
  --config=infrastructure/cloudbuild-v3.yaml \
  --project=$PROJECT_ID \
  --substitutions=SHORT_SHA=$SHORT_SHA \
  --quiet 2>&1 | tail -10

# --- STEP 3: Ensure Cloud Run IAM allows unauthenticated ---
echo ""
echo "3/5  Verifying Cloud Run IAM..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region=$REGION \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --quiet 2>/dev/null || true

# --- STEP 4: Deploy frontend to Firebase Hosting via REST API ---
echo ""
echo "4/5  Deploying frontend to Firebase Hosting..."
bash scripts/deploy-firebase-hosting.sh

# --- STEP 5: Verify ---
echo ""
echo "5/5  Verifying deployment..."
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
FIREBASE_URL="https://${SITE_ID}.web.app"

CR_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CLOUD_RUN_URL")
FB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FIREBASE_URL")

echo ""
echo "======================================================="
echo "  Deployment Complete!"
echo "-------------------------------------------------------"
echo "  Firebase Hosting : ${FIREBASE_URL} (HTTP ${FB_STATUS})"
echo "  Cloud Run Backend: ${CLOUD_RUN_URL} (HTTP ${CR_STATUS})"
echo "-------------------------------------------------------"
echo "  To add a custom domain later:"
echo "    firebase hosting:channel:deploy <channel>"
echo "    or visit: https://console.firebase.google.com/project/${PROJECT_ID}/hosting/sites/${SITE_ID}"
echo "======================================================="
