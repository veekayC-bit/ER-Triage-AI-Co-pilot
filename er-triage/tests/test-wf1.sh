#!/bin/bash
# WF-1 acceptance test — all 8 PRD examples
# Usage: ./test-wf1.sh [webhook_url]
# Default URL assumes N8N running locally on port 5678

WEBHOOK_URL="${1:-https://veekayc.app.n8n.cloud/webhook/parse-complaint}"
PASS=0
FAIL=0

run_test() {
  local id="$1"
  local label="$2"
  local payload="$3"
  local expected_flag="$4"

  echo ""
  echo "── Case $id: $label"
  echo "   Input: $(echo "$payload" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["complaint_text"])')"

  response=$(curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$payload")

  http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$payload")

  echo "   HTTP: $http_code"
  echo "   Response: $(echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response")"
  echo "   Expected flag context: $expected_flag"

  if echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'complaint_category' in d" 2>/dev/null; then
    echo "   [PASS] — structured JSON returned"
    PASS=$((PASS + 1))
  else
    echo "   [FAIL] — missing complaint_category in response"
    FAIL=$((FAIL + 1))
  fi
}

echo "========================================"
echo "WF-1: Parse Complaint — PRD Acceptance Tests"
echo "Target: $WEBHOOK_URL"
echo "========================================"

# Case 1 — Acute MI indicator (confidence 91%)
run_test "01" "Chest pain / Acute MI" \
  '{"complaint_text": "Patient says chest tightness and left arm pain for 20 min, started at rest"}' \
  "⚠️ Acute MI indicator — confidence 91%"

# Case 2 — Stroke indicator (confidence 88%)
run_test "02" "Acute confusion / Stroke" \
  '{"complaint_text": "Came in confused, family says she was fine this morning, slurring her words"}' \
  "⚠️ Stroke indicator — confidence 88%"

# Case 3 — Anaphylaxis (confidence 96%) — primary acceptance test
run_test "03" "Bee sting / Anaphylaxis" \
  '{"complaint_text": "Bee sting 5 minutes ago, throat feels tight, tongue swelling"}' \
  "🔴 Anaphylaxis — confidence 96%"

# Case 4 — No critical flag
run_test "04" "Dizziness / No flag" \
  '{"complaint_text": "Feeling dizzy for 2 days, not eating well"}' \
  "No critical flag"

# Case 5 — No critical flag
run_test "05" "Laceration / No flag" \
  '{"complaint_text": "Cut on hand from kitchen accident, bleeding controlled"}' \
  "No critical flag"

# Case 6 — Suicidal ideation (confidence 97%)
run_test "06" "Self-harm ideation" \
  '{"complaint_text": "Says he wants to hurt himself, was brought in by police"}' \
  "⚠️ Suicidal ideation — confidence 97%"

# Case 7 — Allergic reaction (confidence 72%)
run_test "07" "Rash / Possible allergic reaction" \
  '{"complaint_text": "Rash spreading on torso, started 3 hours ago after new medication"}' \
  "⚠️ Possible allergic reaction — confidence 72%"

# Case 8 — Respiratory distress (confidence 85%)
run_test "08" "Dyspnea / Respiratory distress" \
  '{"complaint_text": "Shortness of breath, oxygen reading at home was 88%"}' \
  "⚠️ Respiratory distress — confidence 85%"

# Edge case — short complaint triggers 400
echo ""
echo "── Edge: Short complaint (< 10 chars) — expect 400"
short_response=$(curl -s -w "\nHTTP:%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"complaint_text": "Pain"}')
echo "   $short_response"

echo ""
echo "========================================"
echo "Results: $PASS passed / $FAIL failed"
echo "Gate: All 8 must pass before moving to WF-2"
echo "========================================"