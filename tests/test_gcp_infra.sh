#!/bin/bash
# ============================================
# Neo-Hack: Gridlock v4.1 — GCP Infrastructure Validation
# Checks Cloud Run scaling, Cloud SQL, Redis, and monitoring.
#
# Usage:
#   ./tests/test_gcp_infra.sh [staging|production]
# ============================================

set -euo pipefail

ENV="${1:-staging}"
PROJECT_ID="webwar-490207"
REGION="europe-west1"
SERVICE_NAME="neohack-gridlock"
[ "$ENV" = "staging" ] && SERVICE_NAME="neohack-staging"
DB_INSTANCE="neohack-db"
REDIS_INSTANCE="neohack-redis"
VPC_CONNECTOR="neohack-vpc-connector"

PASS=0
FAIL=0

green() { echo -e "\033[32m✓ $1\033[0m"; PASS=$((PASS+1)); }
red()   { echo -e "\033[31m✗ $1\033[0m"; FAIL=$((FAIL+1)); }

echo "╔═══════════════════════════════════════════════╗"
echo "║  v4.1 Phantom Mesh — Infrastructure Validation ║"
echo "║  Environment: ${ENV}                            "
echo "║  Project:     ${PROJECT_ID}                     "
echo "╚═══════════════════════════════════════════════╝"
echo ""

# --- 1. Cloud Run Service ---
echo "=== 1. Cloud Run Service ==="

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(status.url)" 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
  green "Service exists: $SERVICE_URL"
else
  red "Service not found: $SERVICE_NAME"
fi

# Check scaling config
MIN_INST=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(spec.template.metadata.annotations.'autoscaling.knative.dev/minScale')" 2>/dev/null || echo "0")
MAX_INST=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale')" 2>/dev/null || echo "0")

[ "$MIN_INST" -ge 2 ] && green "Min instances ≥ 2 (got: $MIN_INST)" || red "Min instances < 2 (got: $MIN_INST)"
[ "$MAX_INST" -ge 10 ] && green "Max instances ≥ 10 (got: $MAX_INST)" || red "Max instances < 10 (got: $MAX_INST)"

# Check concurrency
CONCURRENCY=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(spec.template.spec.containerConcurrency)" 2>/dev/null || echo "0")
[ "$CONCURRENCY" -ge 80 ] && green "Concurrency ≥ 80 (got: $CONCURRENCY)" || red "Concurrency < 80 (got: $CONCURRENCY)"

# Check memory
MEMORY=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(spec.template.spec.containers[0].resources.limits.memory)" 2>/dev/null || echo "")
echo "  Memory limit: $MEMORY"

# Health check
if [ -n "$SERVICE_URL" ]; then
  HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/api/health")
  [ "$HEALTH_CODE" = "200" ] && green "Health endpoint responds 200" || red "Health endpoint returned $HEALTH_CODE"
fi

# --- 2. Cloud SQL ---
echo ""
echo "=== 2. Cloud SQL ==="

DB_STATE=$(gcloud sql instances describe "$DB_INSTANCE" \
  --project="$PROJECT_ID" \
  --format="value(state)" 2>/dev/null || echo "NOT_FOUND")
[ "$DB_STATE" = "RUNNABLE" ] && green "Cloud SQL is RUNNABLE" || red "Cloud SQL state: $DB_STATE"

DB_VERSION=$(gcloud sql instances describe "$DB_INSTANCE" \
  --project="$PROJECT_ID" \
  --format="value(databaseVersion)" 2>/dev/null || echo "")
echo "  Database version: $DB_VERSION"

# --- 3. Redis Memorystore ---
echo ""
echo "=== 3. Redis Memorystore ==="

REDIS_STATE=$(gcloud redis instances describe "$REDIS_INSTANCE" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(state)" 2>/dev/null || echo "NOT_FOUND")

if [ "$REDIS_STATE" = "READY" ]; then
  green "Redis is READY"
  REDIS_HOST=$(gcloud redis instances describe "$REDIS_INSTANCE" \
    --region="$REGION" --project="$PROJECT_ID" \
    --format="value(host)" 2>/dev/null || echo "")
  echo "  Redis host: $REDIS_HOST"
elif [ "$REDIS_STATE" = "NOT_FOUND" ]; then
  echo "  ⚠ Redis not provisioned (optional)"
else
  red "Redis state: $REDIS_STATE"
fi

# --- 4. VPC Connector ---
echo ""
echo "=== 4. VPC Connector ==="

VPC_STATE=$(gcloud compute networks vpc-access connectors describe "$VPC_CONNECTOR" \
  --region="$REGION" --project="$PROJECT_ID" \
  --format="value(state)" 2>/dev/null || echo "NOT_FOUND")

if [ "$VPC_STATE" = "READY" ]; then
  green "VPC connector is READY"
elif [ "$VPC_STATE" = "NOT_FOUND" ]; then
  echo "  ⚠ VPC connector not created (required for Redis)"
else
  red "VPC connector state: $VPC_STATE"
fi

# --- 5. Error Logs ---
echo ""
echo "=== 5. Recent Error Logs (last 1 hour) ==="

ERROR_COUNT=$(gcloud logging read "\
  resource.type=cloud_run_revision \
  AND resource.labels.service_name=$SERVICE_NAME \
  AND severity>=ERROR \
  AND timestamp>=\"$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)\"" \
  --project="$PROJECT_ID" --limit=50 --format=json 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")

if [ "$ERROR_COUNT" = "0" ]; then
  green "No error logs in last hour"
elif [ "$ERROR_COUNT" = "?" ]; then
  echo "  ⚠ Could not query error logs"
else
  red "$ERROR_COUNT error(s) found in last hour"
  echo "  Run: gcloud logging read 'resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR' --limit=10"
fi

# --- Summary ---
echo ""
echo "═══════════════════════════════════════════════"
TOTAL=$((PASS + FAIL))
echo "Infrastructure checks: $PASS/$TOTAL passed"
if [ "$FAIL" -eq 0 ]; then
  echo "✅ INFRASTRUCTURE VALIDATED"
  exit 0
else
  echo "⚠  $FAIL CHECK(S) NEED ATTENTION"
  exit 1
fi
