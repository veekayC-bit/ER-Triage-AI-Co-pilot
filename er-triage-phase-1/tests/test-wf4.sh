#!/bin/bash
# WF4 Retrieve Clinical Context — test suite
# Usage: ./test-wf4.sh
# Requires: WF4 active in N8N, PINECONE ingested via WF3

BASE_URL="https://veekayc.app.n8n.cloud/webhook"
WF4_URL="${BASE_URL}/retrieve-context"
PASS=0
FAIL=0

run_test() {
  local name="$1"
  local payload="$2"
  local expect_field="$3"

  echo ""
  echo "▶ $name"
  RESPONSE=$(curl -s -X POST "$WF4_URL" \
    -H "Content-Type: application/json" \
    -d "$payload")

  if echo "$RESPONSE" | grep -q "$expect_field"; then
    echo "  ✅ PASS — found '$expect_field' in response"
    ((PASS++))
  else
    echo "  ❌ FAIL — '$expect_field' not found"
    echo "  Response: $RESPONSE"
    ((FAIL++))
  fi
}

echo "================================================"
echo " WF4 Clinical Context Retrieval — Test Suite"
echo "================================================"

run_test "Chest pain → STEMI context" \
  '{"complaint_text":"severe chest pain radiating to left arm with diaphoresis","complaint_category":"Cardiac / Chest Pain","flag_type":"STEMI","urgency":"high"}' \
  "retrieved_context"

run_test "Shortness of breath → dyspnea/PE context" \
  '{"complaint_text":"sudden shortness of breath, SpO2 88%, tachycardia","complaint_category":"Respiratory / Dyspnea","flag_type":"Pulmonary Embolism","urgency":"high"}' \
  "retrieved_context"

run_test "Altered mental status → AMS protocol" \
  '{"complaint_text":"patient confused, not responding normally, GCS 10","complaint_category":"Neurological / AMS","flag_type":"Altered Mental Status","urgency":"high"}' \
  "retrieved_context"

run_test "Sepsis pattern → sepsis context" \
  '{"complaint_text":"fever, fast heartbeat, low blood pressure, possible infection","complaint_category":"Infectious / Sepsis","flag_type":"Sepsis","urgency":"high"}' \
  "retrieved_context"

run_test "Low urgency complaint → general ESI context" \
  '{"complaint_text":"mild headache for 2 days, no fever, no neurological symptoms","complaint_category":"Neurological / Headache","flag_type":"","urgency":"none"}' \
  "retrieved_context"

run_test "Stroke symptoms → stroke protocol" \
  '{"complaint_text":"facial drooping on right side, arm weakness, slurred speech, sudden onset","complaint_category":"Neurological / Stroke","flag_type":"Acute Stroke","urgency":"high"}' \
  "retrieved_context"

echo ""
echo "================================================"
echo " Results: ${PASS} passed · ${FAIL} failed"
echo "================================================"
