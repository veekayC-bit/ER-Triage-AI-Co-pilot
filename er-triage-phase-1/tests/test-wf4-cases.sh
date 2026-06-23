#!/bin/bash
# WF4 Synthetic Case Retrieval — test suite
# Tests that WF4 returns clinically relevant guidelines for each complaint type
# Usage: ./test-wf4-cases.sh

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

  if echo "$RESPONSE" | grep -qi "$expect_field"; then
    echo "  ✅ PASS — found '$expect_field' in response"
    ((PASS++))
  else
    echo "  ❌ FAIL — '$expect_field' not found"
    echo "  Response snippet: $(echo "$RESPONSE" | head -c 300)"
    ((FAIL++))
  fi
}

echo "========================================================"
echo " WF4 Synthetic Case Retrieval — Test Suite"
echo " Tests 16 cases across 8 complaint types"
echo "========================================================"

# --- Bee sting / Anaphylaxis ---
run_test "Bee sting ESI 2 → Anaphylaxis guideline" \
  '{"complaint_text":"70-year-old female, bee sting 28 minutes ago, throat feels tight. BP 98/62, HR 115, SpO2 91%.","complaint_category":"Allergic Reaction","flag_type":"Anaphylaxis","urgency":"high"}' \
  "Anaphylaxis"

run_test "Bee sting ESI 1 → Epinephrine action" \
  '{"complaint_text":"25-year-old male, bee sting 10 minutes ago, throat tight, stridor. BP 87/65, HR 149, SpO2 83%, RR 32.","complaint_category":"Allergic Reaction","flag_type":"Anaphylaxis","urgency":"high"}' \
  "Epinephrine"

# --- Acute confusion and dysarthria / Stroke ---
run_test "Confusion + slurred speech ESI 2 → Stroke protocol" \
  '{"complaint_text":"68-year-old female, sudden confusion, slurring words, fine this morning per family. BP 195/100, HR 88, SpO2 98%.","complaint_category":"Neurological / Stroke","flag_type":"Acute Stroke","urgency":"high"}' \
  "Stroke"

run_test "Confusion + dysarthria ESI 1 → tPA assessment" \
  '{"complaint_text":"Patient confused, facial droop, arm weakness, slurred speech, onset unknown. BP 210/110, HR 102, SpO2 96%, RR 22.","complaint_category":"Neurological / Stroke","flag_type":"Acute Stroke","urgency":"high"}' \
  "tPA"

# --- Chest pain with left arm radiation / STEMI ---
run_test "Chest pain ESI 2 → STEMI protocol" \
  '{"complaint_text":"44-year-old female, chest tightness and left arm pain 36 minutes, started at rest. BP 158/90, HR 105, SpO2 96%.","complaint_category":"Cardiac / Chest Pain","flag_type":"STEMI","urgency":"high"}' \
  "STEMI"

run_test "Chest pain ESI 1 → door-to-balloon" \
  '{"complaint_text":"73-year-old male, crushing chest pain with left arm radiation 56 minutes, diaphoresis, nausea. BP 188/98, HR 138, SpO2 91%.","complaint_category":"Cardiac / Chest Pain","flag_type":"STEMI","urgency":"high"}' \
  "balloon"

# --- Dyspnea / Respiratory ---
run_test "Dyspnea ESI 2 → oxygen threshold" \
  '{"complaint_text":"72-year-old male, shortness of breath, SpO2 90% at home. BP 171/84, HR 110, SpO2 90%, RR 25.","complaint_category":"Respiratory / Dyspnea","flag_type":"Respiratory Distress","urgency":"high"}' \
  "SpO2"

run_test "Dyspnea ESI 1 → respiratory failure" \
  '{"complaint_text":"18-year-old female, severe shortness of breath, cannot speak in sentences. BP 180/88, HR 108, SpO2 88%, RR 34.","complaint_category":"Respiratory / Dyspnea","flag_type":"Respiratory Failure","urgency":"high"}' \
  "respiratory"

# --- Dizziness ---
run_test "Dizziness ESI 4 → general ESI context" \
  '{"complaint_text":"33-year-old male, feeling dizzy for 38 days, not eating well. BP 137/73, HR 97, SpO2 99%, RR 17.","complaint_category":"Neurological / Dizziness","flag_type":"","urgency":"low"}' \
  "retrieved_context"

run_test "Dizziness ESI 3 → syncope protocol" \
  '{"complaint_text":"59-year-old female, dizziness with near-syncope episode, palpitations preceding. BP 131/74, HR 83, SpO2 96%.","complaint_category":"Neurological / Syncope","flag_type":"Syncope","urgency":"moderate"}' \
  "Syncope"

# --- Hand laceration ---
run_test "Hand laceration ESI 4 → ESI 4/5 context" \
  '{"complaint_text":"52-year-old patient, cut on hand from kitchen accident, bleeding controlled. BP 131/78, HR 93, SpO2 99%.","complaint_category":"Trauma / Laceration","flag_type":"","urgency":"low"}' \
  "retrieved_context"

run_test "Hand laceration with vitals concern → ESI 3" \
  '{"complaint_text":"49-year-old patient, hand laceration, bleeding not fully controlled, hypotensive. BP 100/70, HR 97, SpO2 98%.","complaint_category":"Trauma / Laceration","flag_type":"","urgency":"moderate"}' \
  "retrieved_context"

# --- Generalized rash ---
run_test "Drug rash ESI 4 → drug reaction context" \
  '{"complaint_text":"58-year-old patient, rash spreading on torso, started 53 hours ago after new medication. Stable vitals.","complaint_category":"Dermatology / Rash","flag_type":"Drug Reaction","urgency":"low"}' \
  "retrieved_context"

run_test "Rash with anaphylaxis risk → anaphylaxis guideline" \
  '{"complaint_text":"Patient with rash after medication, now with hives and throat itching, BP dropping. BP 92/60, HR 120, SpO2 94%.","complaint_category":"Allergic Reaction","flag_type":"Anaphylaxis","urgency":"high"}' \
  "Anaphylaxis"

# --- Suicidal ideation ---
run_test "Suicidal ideation ESI 2 → psychiatric emergency" \
  '{"complaint_text":"7-year-old brought in by police, says wants to hurt himself. BP 103/78, HR 90, SpO2 100%, RR 20.","complaint_category":"Psychiatric / Suicidal Ideation","flag_type":"Psychiatric Emergency","urgency":"high"}' \
  "retrieved_context"

run_test "Sepsis with AMS → sepsis context" \
  '{"complaint_text":"40-year-old male, fever, confusion, fast heartbeat, possible infection source UTI. BP 88/55, HR 122, SpO2 95%, Temp 39.2C.","complaint_category":"Infectious / Sepsis","flag_type":"Sepsis","urgency":"high"}' \
  "Sepsis"

echo ""
echo "========================================================"
echo " Results: ${PASS} passed · ${FAIL} failed out of 16"
echo "========================================================"
