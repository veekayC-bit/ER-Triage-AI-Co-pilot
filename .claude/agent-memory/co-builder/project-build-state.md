---
name: project-build-state
description: Current build phase, what is done, what is next, and open blockers for the ER Triage AI Co-pilot
metadata:
  type: project
---

# ER Triage AI Co-pilot — Build State

Last updated: 2026-06-16 (see note below for current state)

## ⚠️ Superseded — see `er-triage-phase-1/ROADMAP.md` and `er-triage-phase-1/project_build_summary.md` (Session 4, 2026-07-03) for current state

As of 2026-07-03: Phase 4 (Agentic Architecture) is fully complete. HHH scorecard 9/10 passing, only P5-1 (observability dashboard) open. Next task: P5-1. P6-2 (FHIR EHR integration) is ON HOLD; Phase 7 (portfolio wrap-up) moved up ahead of it.

`n8n-workflows/` was reorganized 2026-07-03 — canonical files are now `wf-backend.json`, `wf-ingest-and-retrieve.json`, `wf5-orchestrator.json` (the last now includes guardrail logic inline). Everything referencing `wf1-parse-complaint.json`, `wf2-detect-flags.json`, `wf4-retrieve-context.json`, or `wf-guardrail.json` below is stale — those files were moved to `n8n-workflows/archive/`. Local workflow JSON files can silently drift from what's actually live in N8N Cloud — verify before trusting, ask the user for a fresh export if unsure.

Everything below this point is historical (pre-2026-07-03) context only.

## Current Phase: Phase 1 gate cleared (split architecture, live in production) / Phase 2 frontend wiring in progress

## What Is Done

- PRD written and in repo at `prd_er_triage_ai.md` — Draft/Solution Review stage
- All 6 frontend mockups built in `/mockups/` (intake-normal, intake-flag-moderate, intake-flag-critical, intake-summary, queue-panel, manual-mode)
- Two independent workflows live and active in N8N Cloud, both passing the 9-case PRD acceptance suite in production:
  - `er-triage-phase-1/n8n-workflows/wf1-parse-complaint.json` → `POST /webhook/parse-complaint` → `{ "structured": {...} }`
  - `er-triage-phase-1/n8n-workflows/wf2-detect-flags.json` → `POST /webhook/detect-flags` → `{ "flags": {...} }`
- Test script `er-triage-phase-1/tests/test-split.sh` — 9/9 passing against production as of 2026-06-16
- `mockups/intake-normal.html` fully wired: `analyze()` fires both endpoints via `Promise.all()`, renders structured fields, flag screening, vitals consistency check, and reasoning note
- N8N Cloud instance: `veekayc.app.n8n.cloud`

## Architecture Decisions Made

- N8N Cloud (not self-hosted) — `veekayc.app.n8n.cloud`
- OpenAI GPT-4o for both extraction and flag detection
- 2026-06-16, first pass: WF-1 and WF-2 merged into a single workflow (`wf-merged-parse-and-detect.json`) with one webhook and two "parallel" branches.
- 2026-06-16, **reverted**: discovered N8N does not execute fanned-out branches concurrently — they run sequentially regardless of visual layout, causing ~20s latency (~2x a single GPT-4o call). Rejected the alternative fix (merging both OpenAI calls into one combined prompt) to avoid regressing the hardened flag-detection prompt and to preserve safety-critical-path isolation. **Final architecture: two independent webhooks, parallelized at the frontend via `Promise.all()`.** Confirmed ~2.9s actual latency via direct concurrent curl test — true parallelism achieved outside N8N's engine.
- The merged workflow file is retired/deactivated in N8N Cloud, kept on disk for reference only.
- The pre-merge `wf1-parse-complaint.json` / `wf2-detect-flags.json` were not restored — they were stale (WF-2 depended on WF-1's structured output, ran after it; length-guard ran after the OpenAI call in WF-1). Both files were rewritten from scratch to match the merged workflow's hardened logic, just split across two webhooks, each running its own length-guard before its own OpenAI call.

## Flag-Detection Prompt — Hardened (carries into WF2 unchanged from the merged version)

Two mandatory, explicitly-labeled evaluations every request:
- **Evaluation 1** (`flag_detected`, 10 named conditions): requires a literal, quotable phrase from the complaint text naming the condition's defining symptom. Vitals can only corroborate an already-text-confirmed flag, never independently decide one.
- **Evaluation 2** (`vitals_mismatch`): independent threshold check (SpO2<90%, BP≥180/120, GCS≤13, HR≥150 or ≤40, Temp≥39.5°C) — fires when a crossed threshold isn't explained by the complaint text, regardless of Evaluation 1's outcome.

This took several rounds to get right — the model twice rationalized around "vitals never independently decide a flag" (once via a framing line that anchored it to ignore Evaluation 2 entirely, once via inferring an unrelated symptom like "dizzy" as evidence for "severe headache"). Fixed by requiring literal quotable evidence and explicitly listing disqualifying symptoms. Don't relax this without re-running `test-split.sh` plus a manual extreme-vitals/mild-text edge case.

## N8N Cloud Quirks (recurring — expect these going forward)

- Editing a node and saving does NOT immediately propagate to the production webhook. Symptom: HTTP 200 with `content-length: 0`, zero new executions. Fix: Save, then toggle Active Off then On to force re-registration. Also seen on first activation after a fresh JSON import.
- `/webhook-test/<path>` reflects current editor state immediately (no Save/Activate needed) but only stays armed for one request after clicking "Listen for test event" — can't arm two workflows simultaneously in the same browser session, so cross-workflow sanity checks have to run one at a time.
- N8N does not truly execute "parallel" fanned-out branches concurrently within one workflow run — this was the root cause of the original merged-workflow's ~20s latency.

## Bugs Fixed (historical reference, all resolved)

- Merge node (now removed, was part of the merged workflow): invalid param key `combinationMode` → corrected to `combineBy: "combineByPosition"`.
- IF node (length guard): `typeValidation: strict` → `loose` (was rejecting a numeric string).
- IF node left-value drifted during manual edits in earlier sessions — correct value is `{{ $json.complaint_text.length }}` (bare reference to the `Extract Fields` Set node's output, not the raw webhook body).
- Flag prompt condition 10 ("Anaphylactoid reaction") said "without identified allergen trigger," which contradicted a PRD test case (rash after new medication — trigger IS identified). Broadened to cover both cases.
- Hypertensive crisis regression: vitals alone (extreme BP) named the condition without literal text support — fixed via the Evaluation 1 literal-quote requirement above.

## Mockup Wiring — Completed 2026-06-16

All approved wiring work is done:

- `intake-normal.html` — was already wired; added `persistAnalysis()` to write `erTriageLastAnalysis` to sessionStorage after each successful analyze().
- `intake-flag-critical.html` — fully wired: same `Promise.all()` analyze() as intake-normal, plus `updateSubmitGate(flags)` that disables/enables the Review & Submit button based on `flags.urgency === "high"`, plus sessionStorage persist.
- `intake-flag-moderate.html` — fully wired: same analyze() pattern, no submit-gating (Review & Submit is not disabled by default for moderate), plus sessionStorage persist.
- `intake-summary.html` — sessionStorage handoff script: on load reads `erTriageLastAnalysis`, populates complaint text, structured fields (complaint_category/duration/onset/symptoms, plus trigger/context rows shown conditionally if non-null), vitals, and AI Flag Screening card (green success / amber moderate / red critical based on flag state). Falls back to static demo content if sessionStorage is absent.
- `queue-panel.html` — skipped by user decision: multi-patient list, no single-complaint backend available.
- `manual-mode.html` — skipped by user decision: by-design offline fallback screen, should never call AI.

sessionStorage key: `"erTriageLastAnalysis"`, shape: `{ complaint_text, vitals: {bp,hr,spo2,rr,temp,gcs}, structured: {...}, flags: {...}, timestamp }`.

## Open Items / Next Concrete Action

1. Frontend wiring is fully complete — all approved mockups are live.
2. DB/audit-log schema design remains deferred until before Phase 4 (WF-3: Intake Submitter).
3. RAG was assessed and declined for the current ruleset (too small/static/exhaustive-by-design) — revisit only if the clinical guideline scope grows large enough to need retrieval, tied to the PRD's deferred verifier/critic layer.
