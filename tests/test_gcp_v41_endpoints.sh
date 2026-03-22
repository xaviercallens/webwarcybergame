#!/bin/bash
# ============================================
# Neo-Hack: Gridlock v4.1 — GCP Staging Validation
# Tests all v4.1 API endpoints against a deployed instance
#
# Usage:
#   ./tests/test_gcp_v41_endpoints.sh https://neohack-staging-xxx.run.app
# ============================================

set -euo pipefail

BASE="${1:?Usage: $0 <staging-url>}"
PASS=0
FAIL=0

green() { echo -e "\033[32m✓ $1\033[0m"; PASS=$((PASS+1)); }
red()   { echo -e "\033[31m✗ $1\033[0m"; FAIL=$((FAIL+1)); }
check() { [ "$1" = "$2" ] && green "$3" || red "$3 (expected=$2 got=$1)"; }

echo "╔═══════════════════════════════════════════════╗"
echo "║  v4.1 Phantom Mesh — GCP Endpoint Validation  ║"
echo "║  Target: ${BASE}                               "
echo "╚═══════════════════════════════════════════════╝"
echo ""

# --- 1. Health ---
echo "=== Phase 1: Health ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/health")
check "$STATUS" "200" "Health endpoint responds 200"

BODY=$(curl -s "$BASE/api/health" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "")
check "$BODY" "healthy" "Health body is 'healthy'"

# --- 2. Auth ---
echo ""
echo "=== Phase 2: Auth ==="
# Register test user
REG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"V41_TEST_BOT","password":"testpass123"}')
# 200 or 400 (already exists) both acceptable
[[ "$REG_STATUS" == "200" || "$REG_STATUS" == "400" ]] && green "Register endpoint works ($REG_STATUS)" || red "Register endpoint ($REG_STATUS)"

# Login
LOGIN_RESP=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"V41_TEST_BOT","password":"testpass123"}')
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
[ -n "$TOKEN" ] && green "Login returns JWT token" || red "Login failed — no token"

AUTH="-H 'Authorization: Bearer $TOKEN'"

# --- 3. v4.1 Ghost Nodes ---
echo ""
echo "=== Phase 3: Ghost Nodes ==="
GHOST_RESP=$(curl -s -X POST "$BASE/api/ghost-nodes/deploy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_node_id":1}')
GHOST_STATUS=$(echo "$GHOST_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
check "$GHOST_STATUS" "deployed" "Ghost node deployment"

GHOST_LIST=$(curl -s "$BASE/api/ghost-nodes" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('ghost_nodes',[])))" 2>/dev/null || echo "0")
[ "$GHOST_LIST" -ge 1 ] && green "Ghost node list has entries ($GHOST_LIST)" || red "Ghost node list empty"

# --- 4. Phantom Presences ---
echo ""
echo "=== Phase 4: Phantom Presences ==="
PHANTOM_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/phantom-presences" \
  -H "Authorization: Bearer $TOKEN")
check "$PHANTOM_CODE" "200" "Phantom presences endpoint responds"

# --- 5. Leaderboard Search ---
echo ""
echo "=== Phase 5: Leaderboard Search ==="
SEARCH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/leaderboard/search?q=TEST")
check "$SEARCH_CODE" "200" "Leaderboard search responds"

# --- 6. Campaign Missions ---
echo ""
echo "=== Phase 6: Campaign ==="
CAMP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/campaign/missions" \
  -H "Authorization: Bearer $TOKEN")
check "$CAMP_CODE" "200" "Campaign missions endpoint responds"

# --- 7. Replays ---
echo ""
echo "=== Phase 7: Replays ==="
REPLAY_SAVE=$(curl -s -X POST "$BASE/api/replays" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('replay_id',''))" 2>/dev/null || echo "")
[ -n "$REPLAY_SAVE" ] && green "Replay saved (id=$REPLAY_SAVE)" || red "Replay save failed"

REPLAY_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/replays" \
  -H "Authorization: Bearer $TOKEN")
check "$REPLAY_CODE" "200" "Replay list responds"

# --- 8. React Phase ---
echo ""
echo "=== Phase 8: React Phase ==="
RP_RESP=$(curl -s -X POST "$BASE/api/react-phase/resolve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_id":1,"attacker_success_pct":42.0,"defender_inputs":"w,a,s,d","time_remaining":7,"defender_won":true}')
RP_STATUS=$(echo "$RP_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
check "$RP_STATUS" "resolved" "React phase resolution"

# --- Summary ---
echo ""
echo "═══════════════════════════════════════════════"
TOTAL=$((PASS + FAIL))
echo "Results: $PASS/$TOTAL passed"
if [ "$FAIL" -eq 0 ]; then
  echo "✅ ALL ENDPOINTS VALIDATED"
  exit 0
else
  echo "❌ $FAIL ENDPOINT(S) FAILED"
  exit 1
fi
