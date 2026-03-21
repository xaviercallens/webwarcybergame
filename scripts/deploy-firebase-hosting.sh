#!/bin/bash
set -e

# Firebase Hosting deployment via REST API
# Uses gcloud auth token — no firebase CLI login needed

PROJECT_ID="webwar-490207"
SITE_ID="neohack-v3"
DIST_DIR="build/web/dist"
API_BASE="https://firebasehosting.googleapis.com/v1beta1"
TOKEN=$(gcloud auth print-access-token)
AUTH="Authorization: Bearer $TOKEN"
QUOTA="x-goog-user-project: $PROJECT_ID"

echo "=== Firebase Hosting Deploy: $SITE_ID ==="

# 1. Create a new version with hosting config
echo "1. Creating new version..."
VERSION_RESPONSE=$(curl -s -X POST \
  -H "$AUTH" -H "$QUOTA" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "rewrites": [
        {"glob": "/api/**", "run": {"serviceId": "neohack-v3", "region": "europe-west1"}},
        {"glob": "/docs/**", "run": {"serviceId": "neohack-v3", "region": "europe-west1"}},
        {"glob": "**", "path": "/index.html"}
      ],
      "headers": [
        {
          "glob": "**/*.@(js|css|map)",
          "headers": {"Cache-Control": "public, max-age=31536000, immutable"}
        },
        {
          "glob": "**",
          "headers": {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin"
          }
        }
      ]
    }
  }' \
  "$API_BASE/sites/$SITE_ID/versions")

VERSION_NAME=$(echo "$VERSION_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null)
if [ -z "$VERSION_NAME" ]; then
  echo "ERROR: Failed to create version"
  echo "$VERSION_RESPONSE"
  exit 1
fi
echo "   Version: $VERSION_NAME"

# 2. Compute file hashes and populate
echo "2. Computing file hashes..."
FILE_HASHES="{\"files\":{"
FIRST=true
for file in $(find "$DIST_DIR" -type f); do
  REL_PATH="/${file#$DIST_DIR/}"
  HASH=$(gzip -c "$file" | sha256sum | cut -d' ' -f1)
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    FILE_HASHES+=","
  fi
  FILE_HASHES+="\"$REL_PATH\":\"$HASH\""
done
FILE_HASHES+="}}"

echo "3. Populating files..."
POPULATE_RESPONSE=$(curl -s -X POST \
  -H "$AUTH" -H "$QUOTA" \
  -H "Content-Type: application/json" \
  -d "$FILE_HASHES" \
  "$API_BASE/$VERSION_NAME:populateFiles")

# Check if we need to upload files
UPLOAD_URL=$(echo "$POPULATE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('uploadUrl',''))" 2>/dev/null)
UPLOAD_HASHES=$(echo "$POPULATE_RESPONSE" | python3 -c "
import sys,json
resp = json.load(sys.stdin)
hashes = resp.get('uploadRequiredHashes', [])
for h in hashes:
    print(h)
" 2>/dev/null)

if [ -n "$UPLOAD_URL" ] && [ -n "$UPLOAD_HASHES" ]; then
  echo "4. Uploading files..."
  for file in $(find "$DIST_DIR" -type f); do
    HASH=$(gzip -c "$file" | sha256sum | cut -d' ' -f1)
    if echo "$UPLOAD_HASHES" | grep -q "$HASH"; then
      echo "   Uploading: ${file#$DIST_DIR/}"
      gzip -c "$file" | curl -s -X POST \
        -H "$AUTH" -H "$QUOTA" \
        -H "Content-Type: application/octet-stream" \
        --data-binary @- \
        "${UPLOAD_URL}/${HASH}" > /dev/null
    fi
  done
else
  echo "4. All files already cached, no uploads needed."
fi

# 5. Finalize the version
echo "5. Finalizing version..."
curl -s -X PATCH \
  -H "$AUTH" -H "$QUOTA" \
  -H "Content-Type: application/json" \
  -d '{"status": "FINALIZED"}' \
  "$API_BASE/$VERSION_NAME?updateMask=status" > /dev/null

# 6. Create a release
echo "6. Creating release..."
RELEASE_RESPONSE=$(curl -s -X POST \
  -H "$AUTH" -H "$QUOTA" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"v3.2.0 production deploy $(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
  "$API_BASE/sites/$SITE_ID/releases?versionName=$VERSION_NAME")

RELEASE_NAME=$(echo "$RELEASE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name',''))" 2>/dev/null)

echo "==================================="
echo "Deployment complete!"
echo "Site: https://${SITE_ID}.web.app"
echo "Release: $RELEASE_NAME"
echo "==================================="
