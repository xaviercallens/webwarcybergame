#!/bin/bash
set -e

# =============================================================================
# Neo-Hack RL Training — Launch on GCP Cloud Run Job
# =============================================================================

PROJECT_ID="webwar-490207"
REGION="europe-west1"
REPO="neohack-repo"
IMAGE="rl-train"
JOB_NAME="neohack-rl-train"
BUCKET="gs://neohack-rl-models"
SERVICE_ACCOUNT="neohack-backend@${PROJECT_ID}.iam.gserviceaccount.com"

# Training parameters (override via CLI args)
DIFFICULTY="${1:-all}"
TIMESTEPS="${2:-500000}"
N_ENVS="${3:-4}"

echo "======================================================="
echo "  Neo-Hack RL Training Pipeline"
echo "  Difficulty:  ${DIFFICULTY}"
echo "  Timesteps:   ${TIMESTEPS} per role"
echo "  Parallel:    ${N_ENVS} environments"
echo "======================================================="

# 1. Build training image via Cloud Build
echo ""
echo "1/4  Building training image..."
gcloud builds submit \
  --config=infrastructure/cloudbuild-rl-train.yaml \
  --project=$PROJECT_ID \
  --substitutions=SHORT_SHA=$(git rev-parse --short HEAD) \
  --quiet 2>&1 | tail -5

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:latest"

# 2. Ensure GCS bucket exists
echo ""
echo "2/4  Ensuring GCS bucket..."
gcloud storage buckets describe $BUCKET > /dev/null 2>&1 || \
  gcloud storage buckets create $BUCKET --location=$REGION --project=$PROJECT_ID

# 3. Upload pretrained models to GCS
echo ""
echo "3/4  Uploading pretrained models to GCS..."
gcloud storage cp -r backend/src/rl/models/* "${BUCKET}/pretrained/" --project=$PROJECT_ID 2>&1 | tail -5

# 4. Create or update Cloud Run Job
echo ""
echo "4/4  Launching Cloud Run Job..."
if gcloud run jobs describe $JOB_NAME --region=$REGION --project=$PROJECT_ID > /dev/null 2>&1; then
  gcloud run jobs update $JOB_NAME \
    --region=$REGION \
    --image=$IMAGE_URL \
    --set-env-vars="DIFFICULTY=${DIFFICULTY},TOTAL_TIMESTEPS=${TIMESTEPS},N_ENVS=${N_ENVS},MODEL_INPUT_GCS=${BUCKET}/pretrained,MODEL_OUTPUT_GCS=${BUCKET}/trained" \
    --cpu=4 \
    --memory=16Gi \
    --task-timeout=7200 \
    --max-retries=0 \
    --service-account=$SERVICE_ACCOUNT \
    --quiet
else
  gcloud run jobs create $JOB_NAME \
    --region=$REGION \
    --image=$IMAGE_URL \
    --set-env-vars="DIFFICULTY=${DIFFICULTY},TOTAL_TIMESTEPS=${TIMESTEPS},N_ENVS=${N_ENVS},MODEL_INPUT_GCS=${BUCKET}/pretrained,MODEL_OUTPUT_GCS=${BUCKET}/trained" \
    --cpu=4 \
    --memory=16Gi \
    --task-timeout=7200 \
    --max-retries=0 \
    --service-account=$SERVICE_ACCOUNT \
    --project=$PROJECT_ID \
    --quiet
fi

echo ""
echo "Executing training job..."
gcloud run jobs execute $JOB_NAME --region=$REGION --wait 2>&1 | tail -20

echo ""
echo "======================================================="
echo "  Training complete!"
echo "  Models saved to: ${BUCKET}/trained/"
echo "  Download with: gcloud storage cp -r ${BUCKET}/trained/ ./models/"
echo "======================================================="
