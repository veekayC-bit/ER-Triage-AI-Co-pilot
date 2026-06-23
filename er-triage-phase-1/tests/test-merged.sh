#!/bin/bash
# Merged workflow acceptance test — single endpoint, parallel structured extraction + flag detection
# Input: raw complaint_text (matches PRD "AI behaviour examples" table)
# Response shape: { "structured": {...}, "flags": {...} }
# Usage: ./test-merged.sh [webhook_url]

WEBHOOK_URL="${1:-https://veekayc.app.n8n.cloud/webhook/parse-complaint}"
PASS=0
FAIL=0

run_test() {
  local id="$1"
  local label="$2"
  local complaint_text="$3"
  local expect_flag="$4"      # true or false
  local expect_type="$5"      # flag type string or "null"
  local expect_urgency="$6"   # high, standard, or null

  echo ""
  echo "── Case $id: $label"

  payload=$(python3 -c "import json,sys; print(json.dumps({'complaint_text': sys.argv[1]}))" "$complaint_text")

  response=$(curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$payload")

  got_category=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('structured',{}).get('complaint_category',''))" 2>/dev/null)
  got_flag=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('flags',{}).get('flag_detected',''))" 2>/dev/null)
  got_type=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('flags',{}).get('flag_type',''))" 2>/dev/null)
  got_urgency=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('flags',{}).get('urgency',''))" 2>/dev/null)
  got_confidence=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('flags',{}).get('confidence',''))" 2>/dev/null)
  got_citation=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('flags',{}).get('source_citation',''))" 2>/dev/null)

  echo "   structured.complaint_category : $got_category"
  echo "   flag_detected : $got_flag  (expected: $expect_flag)"
  echo "   flag_type     : $got_type  (expected: $expect_type)"
  echo "   urgency       : $got_urgency  (expected: $expect_urgency)"
  echo "   confidence    : $got_confidence"
  echo "   source_citation: $got_citation"

  if [ "$got_flag" = "$expect_flag" ]; then
    echo "   [PASS]"
    PASS=$((PASS + 1))
  else
    echo "   [FAIL] — flag_detected mismatch"
    FAIL=$((FAIL + 1))
  fi
}

echo "========================================"
echo "Merged WF: Parse + Detect — PRD Acceptance Tests"
echo "Target: $WEBHOOK_URL"
echo "========================================"

# Case 1 — Acute MI (confidence 91% → high urgency)
run_test "01" "Acute MI" \
  "Patient says chest tightness and left arm pain for 20 min, started at rest" \
  "True" "Acute MI" "high"

# Case 2 — Stroke (confidence 88% → standard urgency)
run_test "02" "Stroke" \
  "Came in confused, family says she was fine this morning, slurring her words" \
  "True" "Stroke" "standard"

# Case 3 — Anaphylaxis (confidence 96% → high urgency)
run_test "03" "Anaphylaxis" \
  "Bee sting about 5 minutes ago, throat feels tight" \
  "True" "Anaphylaxis" "high"

# Case 4 — No flag
run_test "04" "No flag — Dizziness" \
  "Feeling dizzy for 2 days, not eating well" \
  "False" "null" "null"

# Case 5 — No flag
run_test "05" "No flag — Laceration" \
  "Cut on hand from kitchen accident, bleeding controlled" \
  "False" "null" "null"

# Case 6 — Suicidal ideation (confidence 97% → high urgency)
run_test "06" "Suicidal ideation" \
  "Says he wants to hurt himself, was brought in by police" \
  "True" "Suicidal ideation" "high"

# Case 7 — Allergic reaction (confidence 72% → standard urgency)
run_test "07" "Allergic reaction" \
  "Rash spreading on torso, started 3 hours ago after new medication" \
  "True" "Anaphylactoid reaction" "standard"

# Case 8 — Respiratory distress (confidence 85% → standard urgency)
run_test "08" "Respiratory distress" \
  "Shortness of breath, oxygen reading at home was 88%" \
  "True" "Respiratory distress" "standard"

echo ""
echo "── Case 09: Insufficient detail guard (short complaint, must NOT call OpenAI)"
short_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"complaint_text":"pain"}')
echo "   HTTP status: $short_response (expected: 400)"
if [ "$short_response" = "400" ]; then
  echo "   [PASS]"
  PASS=$((PASS + 1))
else
  echo "   [FAIL] — expected 400 Insufficient Detail"
  FAIL=$((FAIL + 1))
fi

echo ""
echo "========================================"
echo "Results: $PASS passed / $FAIL failed"
echo "Gate: All 9 must pass before building frontend"
echo "========================================"
