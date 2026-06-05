#!/bin/bash
# WF-2 acceptance test — all 8 PRD examples
# Input: structured JSON from WF-1 output
# Usage: ./test-wf2.sh [webhook_url]

WEBHOOK_URL="${1:-https://veekayc.app.n8n.cloud/webhook/detect-flags}"
PASS=0
FAIL=0

run_test() {
  local id="$1"
  local label="$2"
  local payload="$3"
  local expect_flag="$4"      # true or false
  local expect_type="$5"      # flag type string or "null"
  local expect_urgency="$6"   # high, standard, or null

  echo ""
  echo "── Case $id: $label"

  response=$(curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$payload")

  got_flag=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('flag_detected',''))" 2>/dev/null)
  got_type=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('flag_type',''))" 2>/dev/null)
  got_urgency=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('urgency',''))" 2>/dev/null)
  got_confidence=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('confidence',''))" 2>/dev/null)
  got_citation=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('source_citation',''))" 2>/dev/null)

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
echo "WF-2: Detect Flags — PRD Acceptance Tests"
echo "Target: $WEBHOOK_URL"
echo "========================================"

# Case 1 — Acute MI (confidence 91% → high urgency)
run_test "01" "Acute MI" \
  '{"complaint_category":"Chest tightness and left arm pain","onset":"acute — 20 minutes","duration":"20 minutes","symptoms":[],"trigger":null,"context":"at rest"}' \
  "True" "Acute MI" "high"

# Case 2 — Stroke (confidence 88% → standard urgency)
run_test "02" "Stroke" \
  '{"complaint_category":"Confusion","onset":"acute — this morning","duration":null,"symptoms":["slurring words"],"trigger":null,"context":"family reports she was fine this morning"}' \
  "True" "Stroke" "standard"

# Case 3 — Anaphylaxis (confidence 96% → high urgency)
run_test "03" "Anaphylaxis" \
  '{"complaint_category":"Bee sting","onset":"acute — 5 minutes","duration":null,"symptoms":["throat feels tight","tongue swelling"],"trigger":"bee sting","context":null}' \
  "True" "Anaphylaxis" "high"

# Case 4 — No flag
run_test "04" "No flag — Dizziness" \
  '{"complaint_category":"Dizziness","onset":"gradual — 2 days","duration":"2 days","symptoms":["not eating well"],"trigger":null,"context":null}' \
  "False" "null" "null"

# Case 5 — No flag
run_test "05" "No flag — Laceration" \
  '{"complaint_category":"Cut on hand","onset":null,"duration":null,"symptoms":["bleeding"],"trigger":"kitchen accident","context":null}' \
  "False" "null" "null"

# Case 6 — Suicidal ideation (confidence 97% → high urgency)
run_test "06" "Suicidal ideation" \
  '{"complaint_category":"Suicidal ideation","onset":null,"duration":null,"symptoms":[],"trigger":null,"context":"brought in by police"}' \
  "True" "Suicidal ideation" "high"

# Case 7 — Allergic reaction (confidence 72% → standard urgency)
run_test "07" "Allergic reaction" \
  '{"complaint_category":"Rash","onset":"acute — 3 hours ago","duration":null,"symptoms":[],"trigger":"new medication","context":null}' \
  "True" "Anaphylactoid reaction" "standard"

# Case 8 — Respiratory distress (confidence 85% → standard urgency)
run_test "08" "Respiratory distress" \
  '{"complaint_category":"Shortness of breath","onset":null,"duration":null,"symptoms":[],"trigger":null,"context":"oxygen reading at home was 88%"}' \
  "True" "Respiratory distress" "standard"

echo ""
echo "========================================"
echo "Results: $PASS passed / $FAIL failed"
echo "Gate: All 8 must pass before building frontend"
echo "========================================"
