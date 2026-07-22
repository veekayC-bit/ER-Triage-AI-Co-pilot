---
name: project-build-state
description: Current build phase, what is done, what is next, and open blockers for the ER Triage AI Co-pilot
metadata:
  type: project
---

# ER Triage AI Co-pilot — Build State

Last updated: 2026-07-21 (see note below for current state)

## 2026-07-21 session — Supabase 409 bug found while checking live-intake console after CORS work (unrelated to CORS)

Console showed `Supabase write failed: duplicate key value violates unique constraint encounters_encounter_id_key` (409) on repeat `analyze()` calls for the same encounter. Traced root cause via `er-triage-phase-1/project_build_summary.md` Session 7 (2026-07-10, "Upsert/RLS Bug"):

- 2026-06-18 session added a UNIQUE constraint on `encounters.encounter_id` to support upsert.
- Session 7 (2026-07-10) deliberately reverted frontend from `upsert` back to plain `.insert()` — reasoning: an RLS UPDATE policy for the anon key would let anyone rewrite any patient's existing encounter row (anon key is public/client-side). Intent from that point: one row per `analyze()` call, deduped later at query time (`GROUP BY encounter_id ORDER BY created_at DESC LIMIT 1`) when the observability dashboard (P5-1) gets built.
- The UNIQUE constraint from 06-18 was never dropped when the code moved to plain insert. Every `analyze()` call after the first for a given `encounter_id` has been silently 409ing (swallowed by `console.warn`, invisible in the UI) since **2026-07-10** — live unnoticed bug for over a week.
- First fix attempt (reverting to upsert) was wrong and not committed — would have reopened the exact RLS/security exposure Session 7 was written to avoid. Caught before committing.
- **Actual fix, committed and pushed (`5bae642`):** new migration `er-triage-phase-1/supabase/schema_drop_encounter_unique.sql` — `ALTER TABLE encounters DROP CONSTRAINT IF EXISTS encounters_encounter_id_key;`. No RLS/policy change, no new grants. Also added a comment in `schema.sql`'s RLS section warning future sessions not to re-add a UNIQUE constraint on `encounter_id` — doing so would require upsert, which would require the UPDATE policy this was written to avoid.

**RESOLVED — final fix, verified in production.** First migration attempt (`DROP CONSTRAINT IF EXISTS encounters_encounter_id_key`) was run correctly in the right Supabase project (`lcaslbfjygzniosaobue`), no error — but was a **silent no-op**. Retest immediately after reproduced the identical 409. Root cause: the live DB enforced uniqueness via a plain unique **INDEX** named `encounters_encounter_id_key`, not a table **CONSTRAINT** — almost certainly created via Supabase's Table Editor UI rather than an `ADD CONSTRAINT` statement. Postgres treats these as different catalog objects, so `DROP CONSTRAINT` silently did nothing — a deceptively quiet failure mode (no error, looks successful, bug persists).

Fix: `DROP INDEX IF EXISTS encounters_encounter_id_key`, added to `schema_drop_encounter_unique.sql`, committed and pushed (`9bf160c`). Verified end-to-end in production (not just locally) via browser automation against the live Cloudflare Pages URL: ran the same `encounter_id` through `analyze()` three times in a row — all three writes silent, zero console warnings, where every repeat previously 409'd every time. No RLS/policy change made — plain `.insert()` and the INSERT-only anon policy are unchanged, so the Session 7 (2026-07-10) security posture is fully intact.

**Bug fully closed.** Code and live schema now agree; verified in production.

**Data-completeness caveat for P5-1 (observability dashboard) — flag whenever that phase is picked up:** any encounter with more than one `analyze()` call, in the date range 2026-07-10 through 2026-07-21 (when `9bf160c` landed), will be undercounted — rows for repeat calls on the same encounter_id were silently dropped by the 409 for that entire window. The dashboard must account for this gap, not just assume the DB has a complete row-per-call history.

**New quirk for the N8N/Supabase gotchas list:** if `schema.sql` is ever re-derived against a fresh Supabase project, check whether a Table Editor-created "unique" setting lands as an `INDEX` or a `CONSTRAINT` — they're different Postgres catalog objects, and `DROP CONSTRAINT IF EXISTS` against an index target succeeds with no error while doing nothing. This is worse than a loud failure because it looks fixed.

## 2026-07-21 session — CORS tightening (P7-A) — COMPLETE: all 5 browser-facing webhooks confirmed done or fine, detect-flags outage found AND fixed

**P7-A is now fully closed** — all five browser-facing webhooks (`parse-complaint`, `orchestrate-triage`, `retrieve-context`, `detect-flags`, `observability-data`) are either confirmed CORS-tightened or confirmed already-fine. Both `intake-flag-moderate.html` and `intake-flag-critical.html` are fully functional in production again (see `detect-flags` fix below), not merely diagnosed as broken.

**`detect-flags` — root cause found and fixed.** Curl/CORS-level debugging alone could not have found this — resolved only after the user exported the actual live N8N workflow JSON directly. "ER Triage: Detect Flags" turned out to exist as its own standalone workflow (separate from `wf-backend.json`, which Session 7 correctly cleaned up on 2026-07-10) — with the full original hardened two-evaluation flag-detection prompt still intact. But its Webhook node's path was set to a stray UUID (`3e310117-920b-4c5e-b2b7-df283a7412ea`) instead of the literal string `detect-flags`. So `/webhook/detect-flags` was actually hitting a stale/orphaned N8N routing-table entry left over from Session 7's deletion of the *other* copy — not this workflow at all — which is why it 500'd with zero execution log entries no matter what got changed on it.

**User's explicit direction on scope:** preserve the existing design/product scope exactly; fix the underlying backend even if it requires rework; do not simplify the frontend to fit WF5/orchestrator's leaner output shape (that option — migrating the two screens to the orchestrator instead of restoring the real backend — was explicitly rejected). Fix applied: corrected the Webhook path to `detect-flags`, tightened CORS to the production origin on all three response nodes (Webhook `allowedOrigins`, `Respond: Flags JSON`, `Respond: Insufficient Detail1` — previously all wildcard). Nothing else touched — same prompt, same `vitals_mismatch` logic, same node wiring as originally hardened.

Verified three ways: (1) curl OPTIONS preflight — correct scoped origin header. (2) curl real POST with a STEMI-pattern complaint — correct output: `flag_detected: true`, `flag_type: "Acute MI"`, `confidence: 0.95`, `urgency: high`, correct `source_citation` quote, correct reasoning, `vitals_mismatch` correctly not triggered. (3) full live browser test against `intake-flag-moderate.html` on production — renders the complete original design (confidence %, source citation, reasoning text, Vitals Consistency Check all present and correct), zero console errors.

Committed as `er-triage-phase-1/n8n-workflows/wf-detect-flags.json` (`e4a6e62`) — first-ever local backup of this workflow.

**Loose end, explicitly not urgent, flag for next session only — don't act unprompted:** the user also exported 4 other fresh N8N JSONs tonight as ground-truth references (Backend, Ingest Clinical Knowledge Base, Orchestrator Agent, observability). Not committed yet. Backend/Ingest/Orchestrator would duplicate existing canonical `wf-backend.json`/`wf-ingest-and-retrieve.json`/`wf5-orchestrator.json` under a different naming scheme — needs a deliberate reconciliation/diff pass to check for drift before deciding how to merge or rename. `observability` has never had a local backup at all — needs a proper name chosen (matching the `wf-*.json` convention) before committing. This is a real gap (production-serving workflows with no or stale local backup) but tonight's session explicitly scoped it out — pick it up next time, don't do it proactively.

**Self-caught sync gap, now fixed (commit `958f4e5`):** `wf-backend.json` and `wf5-orchestrator.json` had never actually been synced after their live CORS fix earlier tonight — local copies still showed wildcard `*` despite the real fix being live and verified in N8N Cloud. This is the exact local-vs-Cloud drift pattern this project keeps hitting (see [[project_er_triage_n8n_repo_sync]]) — caught this time before it caused confusion in a future session. Fixed: `allowedOrigins` + all `Access-Control-Allow-Origin` headers in both files updated to match production. **All four canonical workflow JSON files (`wf-backend.json`, `wf5-orchestrator.json`, `wf-ingest-and-retrieve.json`, `wf-detect-flags.json`) are now confirmed actually in sync with live state**, not just assumed to be.

**New standing process rule (effective 2026-07-21, mandatory going forward):** every N8N workflow JSON in the repo must carry a top-level `"_comment"` field (first key) documenting its webhook path, what it does, and which frontend screens/fields depend on it. Applied to all 4 canonical files tonight. Full rationale and how-to-apply guidance in [[feedback-n8n-workflow-json-comments]] — apply to any new workflow JSON from now on without being asked again.

**Architecture debt — APPROVED, SCHEDULED for next session (decision made, not just flagged).** `wf-detect-flags.json`'s flag-detection reasoning and `wf5-orchestrator.json`'s Quick Classify step independently reason over the same complaint text for overlapping critical conditions (STEMI, stroke, sepsis, anaphylaxis, etc.) via two separately-maintained GPT prompts that have already drifted apart — `detect-flags` has a distinct "Anaphylactoid reaction" condition and a `vitals_mismatch` check that Quick Classify's ESI criteria don't carry. They never fire in the same request today (`intake-normal.html` only calls `orchestrate-triage`; `intake-flag-moderate.html`/`intake-flag-critical.html` only call `detect-flags`), so it's not double-billing any single request — but it is duplicated clinical-reasoning surface that can silently drift further out of sync, a patient-safety-adjacent risk, not just tech debt. User wants backend consolidated/optimized but explicitly does **not** want frontend design or output shape touched — ruled out simplifying the two flag screens down to the orchestrator's leaner shape. **User gave explicit go-ahead to proceed with the plan below next session** — this is no longer an open judgment call awaiting a decision.

**Next session's starting point — the approved plan:**
1. Make Quick Classify (inside `wf5-orchestrator.json`) the single reasoning engine — it already runs on every real intake and covers the full ESI 1-5 range, a superset of `detect-flags`' narrower 10-condition scope.
2. Extend Quick Classify's output to also carry the richer fields `intake-flag-moderate.html`/`intake-flag-critical.html` need: `source_citation`, numeric confidence (0.0-1.0), a reasoning sentence, and a `vitals_mismatch` object — alongside its existing `esi_level`/`acuity`/`primary_flag`/etc.
3. Make `wf-detect-flags.json`'s webhook a thin wrapper: call/reuse the orchestrator's classification internally, reshape into the exact same `{ flags: {...} }` contract the frontend already expects. **Zero frontend changes.**
4. **Mandatory, non-negotiable before trusting any of this:** re-run the full 300-case eval suite (`er-triage-phase-1/Evaluations/`) to confirm no recall regression on the hardened Quick Classify prompt — STEMI/stroke recall specifically, given patient-safety stakes. Do not skip this step even under time pressure.
5. Apply the [[feedback-n8n-workflow-json-comments]] standing rule to whatever new/modified workflow JSON comes out of this work.
6. Once done, sync the local `wf5-orchestrator.json`/`wf-detect-flags.json` files the same way as tonight's `958f4e5` fix — don't let them drift from live state again.

---

## 2026-07-21 session — CORS tightening (P7-A) — earlier session narrative (superseded by "COMPLETE" summary above, kept for the debugging trail)

**P7-A CLOSED, verified, on 3 of the 5 browser-facing webhooks:**
- `parse-complaint` (`wf-backend.json`) — CORS origin scoped to `https://er-triage-ai-co-pilot.pages.dev` on Webhook trigger + all Respond nodes, Active toggled off/on, verified via curl preflight (proper `Access-Control-Request-Method`/`Headers`) AND live browser test (real repeat `analyze()` calls succeeded end-to-end from production).
- `orchestrate-triage` (`wf5-orchestrator.json`) — same treatment, same dual verification.
- `retrieve-context` — CORS updated to the Pages origin, verified via curl preflight, clean 204 with correct `access-control-allow-origin`.
- Net result: the roadmap's original "three webhooks" framing turns out to be accurate again — just a different three than initially assumed (`retrieve-context` instead of `detect-flags`/`observability-data`). Earlier notes in this file claiming `detect-flags`/`retrieve-context` were both "confirmed still Active" and both needing the same CORS fix were half right — `retrieve-context` was real and is now fixed; `detect-flags` turned out to be a different, unrelated problem (below).

**NOT closed — investigated as two possible problems, resolved to one confirmed outage + one false alarm, unrelated to CORS:**

1. **`detect-flags` — likely long-dead, mislabeled as a CORS gap.** `project_build_summary.md` Session 7 (2026-07-10) already investigated this, confirmed it was dead code (`intake-normal.html` never called it), and **deleted it entirely** — both the live N8N branch and the local `wf-backend.json` copy. That audit never checked `intake-flag-moderate.html`/`intake-flag-critical.html`, which (per this session's earlier finding) *do* still call `detect-flags` — meaning those two screens have likely been silently broken since 2026-07-10, independent of tonight's work. Tonight, attempting the CORS fix on whatever currently exists under `detect-flags` returned persistent 500s with zero execution log entries (last execution 2026-07-20, nothing logged even after retries + Active off/on toggle). Reverting CORS to wildcard did NOT fix the 500 — rules out CORS as the cause entirely. **Open question:** is the thing currently in N8N under `detect-flags` the same object Session 7 documented deleting, or something recreated/different? Needs someone with editor access to check node structure directly.

1. **`detect-flags` — CONFIRMED, HIGH PRIORITY: active production outage on two screens, not a maybe.** Checked the actual fetch calls: both `intake-flag-moderate.html:526` and `intake-flag-critical.html:535` call `fetch(FLAGS_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: payload })`. The explicit `Content-Type: application/json` header on a POST is a real CORS non-simple request — the browser genuinely sends an OPTIONS preflight before every call, and `detect-flags` 500s on that preflight. Both screens issue this call inside `Promise.all([parseRes, flagsRes, contextRes])` — a CORS-blocked fetch throws before resolving, so `Promise.all` rejects immediately on the first failure. **Net effect: both `intake-flag-moderate.html` and `intake-flag-critical.html` are fully non-functional in production right now** — not just missing flag data, the entire `analyze()` call fails, because `detect-flags`'s broken preflight takes down the otherwise-working `parse-complaint` and `retrieve-context` calls with it. This is the higher-priority item of the two open problems — an active, user-facing outage, not latent/cosmetic like `observability-data` turned out to be. Root cause still unknown: Session 7 (2026-07-10) documented deleting a same-named endpoint as dead code; unclear whether what exists now under `detect-flags` is a recreation, or the deletion never fully took. Needs N8N editor access to resolve.

**`observability-data` — CORRECTED, NOT a regression, P5-1 stays CLOSED.** Initial read tonight ("500 on OPTIONS preflight = broken dashboard") was wrong — jumped to a conclusion without checking whether the real frontend code path ever triggers a preflight at all. It doesn't: `observability.html` calls `fetch(OBS_URL)` as a bare GET with zero custom headers — a CORS "simple request," which browsers never preflight with OPTIONS; they send the GET directly and just check the response's `Access-Control-Allow-Origin` header after the fact. Verified two ways: (1) `curl -X GET` against `observability-data` returns 200 with correct real data (14 encounters, proper aggregated stats) and the correct scoped `access-control-allow-origin` header; (2) loaded the live `observability.html` in an actual browser against production — every panel renders correctly with live data, zero console errors. **Not broken. P5-1 remains fully closed**, as validated in Session 7 (2026-07-10). The OPTIONS-preflight 500 on this workflow is a real latent bug in N8N's preflight handling — worth fixing eventually in case a future caller adds custom headers and turns its GET into a non-simple request — but it is not urgent and not user-facing today.

**Lesson from this back-and-forth, worth keeping in mind:** an OPTIONS-preflight failure only matters if the real frontend fetch call actually triggers a preflight (non-simple request: custom headers like `Content-Type: application/json`, non-GET/POST-with-simple-body, etc.). Check the actual `fetch()` call in the mockup before treating a curl-level OPTIONS failure as a production-breaking bug — confirmed the hard way twice in one session (almost misjudged `observability-data` as broken, correctly caught `detect-flags` as genuinely at risk only after checking its headers).

**Next session should start with:** N8N editor access, opening `detect-flags` directly to check node structure (is it the same object Session 7 documented deleting 2026-07-10, or something recreated/different) and confirm whether it's actually reachable/wired for the two screens that call it. `observability-data`'s OPTIONS-preflight bug can be fixed opportunistically, not urgently — it's cosmetic today.

## 2026-07-21 session — repo structure cleanup (file organization only, no build progress)

Pushed to `origin/main`. Purely housekeeping — did not touch `er-triage-phase-1` app code, workflows, or the CORS/auth work below.
- Deleted a stale nested duplicate git clone (`ER-Triage-AI-Co-pilot/`) that had been sitting inside the repo, duplicating most top-level content — verified no unique commits or unique uncommitted content before deleting.
- Deleted a self-nested duplicate `document-parser-phase-2/document-parser-phase-2/` folder.
- Added `.gitignore`; untracked `document-parser-phase-2/venv/` (3,094 files) and stray `.DS_Store` files that had been committed by mistake.
- Moved four orphaned N8N node-prompt files (previously loose at repo root as `json-formatter-*` with unclear names) into `er-triage-phase-1/n8n-workflows/node-prompts/`, renamed to match their live WF5 orchestrator node names: `build-clinical-brief.txt`, `build-urgent-summary.txt`, `guardrail-check-and-route.txt`, `quick-classify.txt`.

## 2026-07-20 session — P7-A (Cloudflare Pages hosting) shipped

- App is now live in production: **https://er-triage-ai-co-pilot.pages.dev** (repo: `veekayC-bit/ER-Triage-AI-Co-pilot`, **public**).
- Local `er-triage-phase-1/.env` and `mockups/env.local.js` had been lost (never committed — both gitignored by design). Recovered: `SUPABASE_URL` was already recoverable from a hardcoded fallback in `intake-normal.html`; `SUPABASE_KEY` (anon/public key) was re-pulled from the Supabase dashboard. `.env` recreated locally, `scripts/gen-env-local.sh` re-run to regenerate `env.local.js`.
- First Cloudflare Pages deploy failed: the build command (`scripts/gen-env-cloudflare.sh`, root dir `er-triage-phase-1`, output dir `mockups`) was configured in the Cloudflare dashboard but the script itself was never committed — 127/"not found" on every build. Root cause: P7-A's roadmap spec called for this script but it was scoped/described, never actually written before wiring it into Cloudflare's build settings.
- Fix: wrote `er-triage-phase-1/scripts/gen-env-cloudflare.sh` (mirrors `gen-env-local.sh` but reads `SUPABASE_URL`/`SUPABASE_KEY` directly from Cloudflare's build-time env vars, which were already correctly configured in the dashboard as plaintext — anon key is public-safe by design). Committed `ebe08f5` to `main`, pushed, deploy succeeded, verified live with no console errors.
- **Local git push friction (environment note, not project note):** pushing from this machine hangs — the Bash tool's sandbox can't reach the macOS Keychain (osxkeychain credential helper hangs indefinitely), and even the user's own `!`-prefixed terminal session lacks a real TTY for interactive prompts ("Device not configured"), so `GIT_ASKPASS`/VS Code's askpass.sh can't complete either. Only working path found: user opens a genuinely separate terminal window (Terminal.app or a real VS Code terminal, not through Claude Code at all) and runs `git push` there interactively with a GitHub PAT. Expect to hit this again on the next push.
- **Outstanding to fully close P7-A:** CORS on the three N8N webhooks (`parse-complaint`, `orchestrate-triage`, `observability-data`) is still wildcard `*` — needs tightening to `https://er-triage-ai-co-pilot.pages.dev`. Deliberately deferred (user call, 2026-07-20) since the repo/link isn't being actively shared yet; real exposure is bounded by the repo already being public with zero request-level auth (P7-B, not yet built) regardless of CORS — CORS only closes the browser-drive-by vector, not direct curl access. **Do this before the link is sent to any external recruiter/reviewer.**
- Next up per `ROADMAP.md`'s 2026-07-17 re-prioritization: CORS tightening (finish P7-A), then Phase 7 wrap-up (README, case study, resume), then the open P7-B/C scope decision (full Supabase Auth vs. cheap shared-password gate) before building auth.

## ⚠️ Everything below is superseded — see `er-triage-phase-1/ROADMAP.md` and `er-triage-phase-1/project_build_summary.md` (Session 4, 2026-07-03) for current state

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
