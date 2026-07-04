# ER Triage AI Co-pilot — Project Build Summary

**Project:** ER Assisted Triage Workflow System  
**Stack:** N8N Cloud · OpenAI GPT-4o · Pinecone · Vanilla JS Mockups  
**Builder:** Venkat Krishnan Chellappa (Veekay) + Claude (Co-builder)  
**Started:** May 2026 | **Last Updated:** June 17, 2026

This document captures design decisions, the reasoning behind them, problems encountered, and solutions found — in the order they happened. It is a living record, updated as each phase is completed.

---

## Phase 1 — AI Workflow Foundations

### What Was Built
- WF1: Parse patient complaint → GPT-4o → structured triage output (ESI level, chief complaint, vitals flag, disposition)
- WF2: Detect critical flags → GPT-4o → flag type, severity, recommended actions
- Frontend wired to live N8N webhooks via `Promise.all`

### Design Decisions

**Split 2-webhook architecture (WF1 + WF2 separate) vs. single combined workflow**
WHY: Separation of concerns. Parse and flag detection are distinct tasks with different prompts and output schemas. Keeping them separate means each can be improved, tested, and replaced independently. A single monolithic workflow would couple the prompt logic and make debugging harder. The frontend calls both in parallel via `Promise.all` so latency is not additive.

**N8N Cloud over a custom Python backend**
WHY: Faster iteration. N8N gives visual debugging, built-in credential management, and webhook infrastructure with zero server setup. For a portfolio build at this stage, shipping a working system quickly matters more than full infrastructure control. The tradeoff is sandbox constraints (documented in Phase 3).

**OpenAI GPT-4o over GPT-3.5 or other models**
WHY: Clinical triage requires accurate reasoning about vitals, symptoms, and urgency. GPT-4o's stronger reasoning justified the cost premium at this scale. For a production system at volume, this would be revisited with a tiered model strategy (Phase 4 consideration).

### Problems Encountered

**Problem:** `Promise.all` on the frontend fired both webhooks but the N8N test URL only handles one call at a time.  
**Solution:** Use production webhook URL (`/webhook/`) for live calls. Test URL (`/webhook-test/`) is single-threaded and only valid for manual debugging one request at a time.

---

## Phase 2 — AI Productization & UX

### What Was Built
- 3 intake mockups: `intake-normal.html`, `intake-flag-critical.html`, `intake-flag-moderate.html`
- Summary screen: `intake-summary.html`
- `sessionStorage` used to pass full analysis payload across screens without a database
- Patient fields (name, DOB, gender, MRN) set as non-editable; ethnicity editable
- Navigation: home button returns to patient intake; transition buttons go to dashboard or new intake from all screens

### Design Decisions

**sessionStorage for cross-screen state over a database**
WHY: Phase 1-2 scope was to validate the AI pipeline and UX flow, not build persistence infrastructure. sessionStorage gives browser-scoped state that works without a backend, clears on tab close (appropriate for clinical privacy), and required zero infrastructure. Database deferred to Phase 4 where persistent patient state becomes necessary for the orchestrator agent.

**Non-editable patient demographics (name, DOB, gender, MRN)**
WHY: In a real EMR-connected triage workflow, these fields come from registration and must not be altered by triage staff. Making them read-only models the correct clinical workflow even in a prototype — it prevents bad habits from being designed in early.

**Three separate intake screens rather than one screen with conditional rendering**
WHY: Each acuity outcome (normal, critical flag, moderate flag) has meaningfully different layouts — different color coding, different action panels, different clinical context emphasis. A single screen with conditional CSS becomes hard to maintain. Separate files are cleaner for a mockup and easier to demo independently.

### Problems Encountered

None that required architectural changes in Phase 2.

---

## Phase 3 — RAG & Context Systems

### What Was Built
- WF3: Ingest 24 clinical knowledge documents → OpenAI embeddings → Pinecone vector store
- WF4: Retrieve context webhook → embed query → Pinecone similarity search → return ranked guidelines
- Evaluation pipeline: `Evaluation_Answer_Key.json` (1000 records), `evaluation.py` (automated scoring), `test-wf4-cases.sh` (16 synthetic cases)
- RAG sidebar wired into all 3 intake screens showing top guidelines with relevance scores
- Evaluation result files: JSON + CSV with timestamped filenames for graph/slide consumption

### Design Decisions

**Pinecone over alternatives (Weaviate, pgvector, Chroma)**
WHY: Managed service with zero infrastructure. Pinecone's free tier supports the index size needed. REST API is simple and consistent. The main tradeoff is vendor lock-in and cost at scale — acceptable for a portfolio build.

**text-embedding-ada-002 (1536 dimensions) over newer embedding models**
WHY: Wide compatibility, stable, cost-effective at $0.0001/1K tokens. The clinical knowledge base is small enough that embedding quality differences between ada-002 and newer models are negligible. Using the same model in WF3 (ingestion) and WF4 (query) is the hard requirement — mismatched models produce meaningless similarity scores.

**Default Pinecone namespace (empty string) over a named namespace**
WHY: Simplicity. Named namespaces add a routing layer that is only useful when running multiple isolated knowledge bases on the same index. One index, one knowledge base = use default. Named namespace caused silent retrieval failures (see Problems below).

**RAG retrieval threshold set to 0.3 not 0.5**
WHY: Clinical text embeddings produce moderate cosine similarity scores even for correct matches. A strict 0.5 threshold filtered out all results during early testing. 0.3 allows clinically relevant matches through while still excluding noise. The evaluation confirmed 84–85% average top relevance after correct ingestion, well above the threshold.

**Evaluation-first, optimize second**
WHY: Built the 1000-record answer key and scoring pipeline before tuning the knowledge base. This gave an objective baseline (90% at first run) and revealed exactly which complaint categories and failure modes to target. Without the evaluation framework, knowledge base expansion would be guesswork. The 6 documents added in the second iteration were targeted directly at the failure categories identified by the eval.

**24 knowledge documents covering 5 source categories**
WHY: Coverage across ESI criteria (1–5), critical conditions (STEMI, sepsis, stroke, PE, HTN crisis, anaphylaxis), vital thresholds, triage protocols, and low-acuity patterns. The initial 18 documents were skewed toward critical/emergent content — dizziness and low-acuity cases failed because there was no matching document. Adding ESI 4-5, dizziness/vertigo, psychiatric, laceration, drug reaction, and stroke-002 brought low-acuity pass rate from 80% to 100%.

**Code nodes for data transformation only; HTTP Request nodes for all API calls**
WHY: N8N Cloud's Code node sandbox blocks both `fetch` (browser API) and `$http` (N8N helper not available in all versions). This was discovered through failure. The correct N8N pattern is: HTTP Request nodes handle all outbound API calls, Code nodes handle data wiring and transformation. Cross-node data references (`$('NodeName').item.json`) work reliably in HTTP Request node jsonBody expressions but are unreliable in Code nodes when the pairedItem chain crosses an HTTP Request node. This pattern recurred in Phase 4 WF5 (Extract and Route node tried to reference `$('Webhook').item.json` — same failure). Confirmed rule: never back-reference earlier nodes in a Code node that sits downstream of any HTTP Request node.

**N8N Code node mode vs. return format — confirmed pattern (Phase 4):**
- `"mode": "runOnceForEachItem"` → return must be a single item `{ json: {...} }` (no array wrapper). Returning `[{ json: {...} }]` in this mode throws "A 'json' property isn't an object".
- No mode set (default = runOnceForAllItems) → use `$input.all()[0].json` to access the item, return `[{ json: {...} }]` (array). This is the reliable pattern used in WF4 Extract Vector and WF5 Extract and Route.
- Rule: always omit `mode` in Code nodes, use `$input.all()[0].json`, return array.

### Problems Encountered

**Problem:** LangChain `documentDefaultDataLoader` in WF3 embedded the `id` field value ("stemi-001") instead of the `text` field. All Pinecone vectors contained a ~5-word string instead of clinical content. Similarity scores came back at 0.046 for all queries.  
**How discovered:** Pinecone query returned `text: stemi-001` in metadata and score of 0.046 — noise floor, not a match. Checked the metadata and confirmed the text stored was the id value.  
**Solution:** Rebuilt WF3 without LangChain. Used direct HTTP Request nodes to OpenAI and Pinecone with explicit field references. LangChain's data loader was abstracting the wrong field.

**Problem:** `fetch is not defined` — WF3 Code node using `fetch()` for HTTP calls failed at runtime.  
**Solution attempt 1:** Replaced with `$http.request()`. Also not defined.  
**Solution attempt 2:** `require('https')` — blocked by vm2 sandbox.  
**Final solution:** Removed all HTTP calls from Code nodes. Restructured WF3 as: Return Documents (Code) → Embed Document (HTTP Request → OpenAI) → Upsert to Pinecone (HTTP Request). Code nodes only transform data; HTTP nodes make all calls.

**Problem:** `Build Upsert Payload` Code node error: "A 'json' property isn't an object [item 0]". The Code node used `$('Return Documents').item.json` to recover original doc metadata after the HTTP Request node replaced item data. The pairedItem chain did not reliably traverse across an HTTP Request node in the Code node context.  
**Solution:** Removed the intermediate Code node entirely. Put the cross-node reference `$('Return Documents').item.json` directly into the Upsert to Pinecone HTTP Request node's `jsonBody` expression. HTTP Request node expressions resolve cross-node references reliably. The pipeline went from 5 nodes to 4.

**Problem:** WF4 Config node imported empty — Set node typeVersion 3 did not import field values correctly.  
**Solution:** Rewrote the Set node JSON using typeVersion 2 with `values.string` array format. typeVersion 2 is the reliable import format; typeVersion 3 may require manual field entry after import.

**Problem:** WF4 Query Pinecone body used `JSON.stringify({...})` inside `specifyBody: "json"`. This double-encoded the body — N8N serialized the already-stringified JSON again, sending a string to Pinecone instead of an object.  
**Solution:** Removed `JSON.stringify`. Used raw N8N expression: `={{ { vector: $json.embedding, topK: 4, includeMetadata: true } }}`. When `specifyBody: "json"`, N8N evaluates the expression as a JavaScript object and serializes it once.

**Problem:** WF4 returned empty matches. Config node had `pinecone_namespace: "er-guidelines"` but WF3 ingested into the default namespace (empty string).  
**Solution:** Set `pinecone_namespace` to empty string in Config node. Then removed the namespace field from the Pinecone query body entirely — omitting namespace defaults to the default namespace without ambiguity.

**Problem:** Evaluation pass rate 0/50 on first run after initial WF3 ingest.  
**Root cause stack:** (1) LangChain embedded wrong field → garbage vectors → 0.046 similarity → all below 0.5 threshold → relevance_ok failed for all 50. After fixing embeddings, threshold 0.5 was still too strict for clinical text. Lowered to 0.3.  
**Result after both fixes:** 90% on first 50-case run, 97% after knowledge base expansion.

**Problem:** 3 stroke cases consistently failing `source_match` — evaluation expects `critical_conditions` source in top results but ESI-2 document (source: `esi_criteria`) scores higher for stroke queries because it mentions "FAST-positive stroke signs".  
**Assessment:** Evaluation sensitivity issue, not a retrieval failure. The retrieved content is clinically correct. Stroke-specific documents (`stroke-001`, `stroke-002`) appear in the top-4 results but not at rank #1. A production fix would adjust the evaluation to check top-4 source presence more broadly, or boost `critical_conditions` source weight. Accepted as known limitation at 97% overall.

### Evaluation Results (Phase 3 Final)

| Run | Sample | Seed | Pass Rate | Keyword Hit | Source Match | Avg Relevance |
|---|---|---|---|---|---|---|
| Baseline (pre-fix) | 50 | 42 | 0% | — | — | ~5% |
| Post-ingest fix | 50 | 42 | 90% | 92% | 98% | 84% |
| After KB expansion | 100 | 42 | 97% | 100% | 97% | 84.6% |
| Separate subset | 300 | 99 | 97% | 100% | 97.7% | 85.1% |

---

## Phase 4 — Agentic Architecture (Design, Not Yet Built)

### Design Intent

Move from a fixed parallel pipeline (WF1 + WF2 + WF4 always) to an orchestrator agent that routes conditionally based on acuity — calling only the tools each case requires.

### Design Decisions (Pre-build)

**Orchestrator agent over fixed pipeline**
WHY: Current architecture runs the same three workflows regardless of acuity. A low-acuity dizziness case pays the same token cost as a STEMI and gets the same depth of analysis. An orchestrator routes ESI 4-5 cases to a lightweight path and ESI 1-2 to a full clinical reasoning path. This reduces average token cost by ~42% while increasing output quality for critical cases.

**Single-turn interaction for Phase 4; multi-turn deferred to Phase 5**
WHY: Multi-turn requires session state, a conversation loop, and the patient state database (deferred since Phase 1). Single-turn (one intake → one composed response) delivers the orchestration value without the session management complexity. Keeps Phase 4 scope bounded.

**Token optimization strategy: tiered by acuity**
- ESI 4-5: parse only, no RAG, ~500 tokens
- ESI 3: parse + RAG topK=2, ~900 tokens  
- ESI 1-2: parse + flags + RAG topK=4 + clinical summary, ~1,800 tokens
- Weighted average at real ER distribution (~60% low, 20% high, 20% critical): ~840 tokens vs ~1,450 today

**Prompt caching for system prompt**
WHY: The system prompt (triage rules, ESI criteria, JSON output schema) is identical across all calls. OpenAI prompt caching reduces cost of repeated prefixes by 50%. Keep system prompt static; vary only patient data in user turn.

**Structured JSON output enforced**
WHY: Prose responses cost more tokens and require parsing before rendering. Forcing a JSON schema (`{esi, flag, actions[], disposition, confidence}`) eliminates verbose preamble and makes frontend rendering deterministic.

**Patient state database introduced in Phase 4**
WHY: The orchestrator needs to store encounter outcomes for the multi-turn foundation in Phase 5 and for audit/analytics. Deferred from Phase 1 because sessionStorage was sufficient for the linear pipeline. Now the agent needs to persist reasoning steps and encounter state across the session.

### Open Questions at Phase 4 Start
- N8N AI Agent node vs. custom orchestration chain (control vs. speed of build)
- Database choice: Supabase (Postgres + REST) vs. Airtable vs. N8N internal storage
- Whether clinical summary generation should be a separate WF6 or part of the orchestrator prompt

---

## Phase 4 — Build Log (In Progress)

### Problem Identified: Quick Classify not grounded in clinical knowledge

**What we found:** The Quick Classify node (first GPT-4o call) makes the routing decision — ESI 1-5, which determines whether a patient gets the full Critical brief, the Urgent summary, or the Low response. This is the highest-stakes decision in the workflow. But Quick Classify was using only a 50-word ESI summary in the system prompt plus GPT-4o's general training data. Our 24 Pinecone documents (evaluated at 97% accuracy) were not used at this step — RAG only entered after routing.

**Why this matters:** If Quick Classify miscategorises a STEMI as ESI 3, it routes to Branch Urgent and generates a lighter summary without door-to-balloon timing, cardiology alert, or resuscitation room disposition. The most critical decision was the least grounded.

**Options considered:**
- Option A: Embed explicit clinical criteria directly in the Quick Classify system prompt (no extra API call, anchors classification in our defined rules)
- Option B: Run a broad RAG retrieval before Quick Classify, pass guidelines into the classification prompt (most accurate, adds latency + complexity — Phase 5 candidate)
- Option C: Deterministic vital sign pre-filter before GPT-4o (removes model uncertainty for life-critical routing)

**Decision: Option A — prompt-embedded clinical criteria**
WHY: Zero added latency, zero added cost, immediately implementable. The ESI 1-2 criteria are well-defined and can be expressed as explicit rules in the prompt. The classification becomes anchored to our clinical definitions rather than relying on what GPT-4o's training happens to know. Option B (RAG-first) is the right long-term architecture but belongs in Phase 5 where we revisit the orchestrator with full observability.

**How applied:** Expanded Quick Classify system prompt from ~50 words to explicit per-ESI trigger criteria: vital thresholds (SBP, SpO2, HR, GCS), condition-specific flags (STEMI pattern, FAST stroke criteria, sepsis SIRS criteria), and resource-based ESI 3-5 rules. Applied in order — ESI 1 checked first, ESI 5 last. ~300 tokens vs. original ~100 tokens; acceptable tradeoff for routing accuracy.

---

### WF5 Final Architecture (Completed)

```
Webhook (POST /orchestrate-triage)
    ↓
Quick Classify (HTTP → GPT-4o, ~350 tokens)
    → { esi_level, acuity, primary_flag, complaint_summary }
    ↓
Extract and Route (Code — parse GPT JSON, derive tier)
    → { tier: critical|urgent|low, esi_level, acuity, primary_flag, complaint_summary }
    ↓
Route by Tier (Switch)
    ↓
tier=critical → Embed Query Critical (HTTP → OpenAI, topK=4 signal)
             → Query Pinecone Critical (HTTP → Pinecone, topK=4)
             → Build Clinical Brief (HTTP → GPT-4o, ~1,450 tokens)
             → Respond Critical
             Output: { esi_level, acuity, primary_flag, immediate_actions[], 
                       clinical_protocol, time_targets, disposition, 
                       retrieved_guidelines[], confidence }

tier=urgent  → Embed Query Urgent (HTTP → OpenAI)
             → Query Pinecone Urgent (HTTP → Pinecone, topK=2)
             → Build Urgent Summary (HTTP → GPT-4o, ~900 tokens)
             → Respond Urgent
             Output: { esi_level, acuity, primary_flag, recommended_actions[],
                       clinical_notes, disposition, retrieved_guidelines[], confidence }

tier=low     → Respond Low (respondToWebhook, 0 additional API calls)
             Output: { esi_level, acuity, primary_flag, recommended_actions[],
                       clinical_notes, disposition: fast_track|waiting_room, confidence }
```

### Token Cost by Branch (Achieved)

| Branch | Tokens | API Calls |
|---|---|---|
| Low (ESI 4-5) | ~350 | 1 (Quick Classify only) |
| Urgent (ESI 3) | ~900 | 3 (Classify + embed + RAG + summary) |
| Critical (ESI 1-2) | ~1,800 | 4 (Classify + embed + RAG topK=4 + brief) |
| Weighted avg (real ER dist.) | ~840 | vs ~1,450 in Phase 1-3 fixed pipeline |

### Problems Encountered in Phase 4

**Problem:** `"mode": "runOnceForEachItem"` in Code nodes causes "A 'json' property isn't an object [item 0]" when returning `[{ json: {...} }]`.  
**Root cause:** In `runOnceForEachItem` mode, N8N expects a single item return `{ json: {...} }` not an array. In `runOnceForAllItems` mode (no mode set), array return `[{ json: {...} }]` is correct.  
**Solution:** Remove `mode` from all Code nodes. Use `$input.all()[0].json` to access the incoming item. Return `[{ json: {...} }]`. This matches the pattern already working in WF4 Extract Vector.  
**Rule confirmed:** Always omit mode in Code nodes. Use `$input.all()[0].json`. Return array.

**Problem:** Code node (Extract and Route) back-referenced `$('Webhook').item.json.body` — same pairedItem chain failure as Phase 3.  
**Solution:** Removed all back-references from Code nodes. Only `$input.all()[0].json` used in Code nodes. `$('Webhook').item.json.body` referenced only in HTTP Request node jsonBody expressions downstream where it works reliably.

**Problem (design):** Quick Classify used only a 50-word ESI summary in the system prompt — routing decision was not grounded in clinical criteria.  
**Solution:** Expanded to ~300 token explicit criteria per ESI level (vital thresholds, condition-specific patterns, resource requirements). Applied in order, first match wins. Stroke correctly classified ESI 2 not ESI 1 after fix. See design decision section above.

### Phase 4 Validation Results

| Case | ESI | Branch | Output |
|---|---|---|---|
| STEMI (chest pain + diaphoresis + HR 138) | 1 | Critical | STEMI protocol, ECG 10 min, aspirin, cardiology ✅ |
| Stroke (FAST positive, BP 195/105) | 2 | Critical | Stroke code, CT head, neurology 15 min ✅ |
| Septic shock (BP 88/55, HR 122, Temp 39.2) | 1 | Critical | 1-hour bundle: cultures → antibiotics → lactate ✅ |
| Vomiting/dehydration | 3 | Urgent | IV fluids, antiemetic, metabolic panel ✅ |
| Hand laceration (controlled bleeding) | 3 | Urgent | Wound assessment, tendon check, sutures, tetanus ✅ |
| Mild dizziness (stable vitals) | 5 | Low | Waiting room, 0 extra API calls ✅ |

### What Remains for Phase 4

- **Database layer** — Supabase to persist encounters, enable audit trail, and lay groundwork for multi-turn in Phase 5
- **Wire WF5 into frontend** — replace Promise.all(WF1, WF2, WF4) on intake screens with single call to WF5 orchestrator
- **STEMI time_targets gap** — door-to-balloon target missing from Build Clinical Brief output; prompt needs one line addition

---

## Phase 4 — Frontend Wiring to WF5

### What Was Built
- Replaced `Promise.all(WF1, WF2, WF4)` in `intake-normal.html` with `Promise.all(WF1, WF5)` — 3 API calls reduced to 2
- Dropped WF2 (detect-flags) and WF4 (retrieve-context) from the frontend entirely; WF5 subsumes both
- New sidebar sections: **AI Triage Assessment** (ESI badge + acuity + disposition), **Primary Flag** (replaces Critical Flag Screening), **Clinical Actions** (immediate_actions or recommended_actions), **Clinical Notes** (clinical_protocol or clinical_notes + time_targets), **Retrieved Guidelines** (RAG output from WF5)
- Removed Vitals Consistency Check section — vitals are now baked into ESI classification by the orchestrator
- `intake-summary.html` sessionStorage reader updated from `data.flags` shape to `data.wf5` shape
- `applyUrgencyTheme()` now driven by `wf5.esi_level` (≤2 → critical red, 3 → warning orange, ≥4 → normal) instead of `flags.urgency`
- `confidence` field handled as string ("high"/"medium"/"low") not number — WF5 returns string labels, not 0.0–1.0

### Design Decisions

**Keep WF1 (parse-complaint) alongside WF5 — don't drop it**  
WHY: WF1 returns the structured parsing fields (complaint_category, onset, duration, symptoms, trigger, context) that populate the "Suggested Structured Fields" sidebar section. WF5's Quick Classify returns `complaint_summary` (a one-liner) but not the full structured breakdown nurses use for EMR documentation. Dropping WF1 would remove structured field suggestions. Keeping it means the frontend fires 2 parallel calls (WF1 + WF5) instead of 3 (WF1 + WF2 + WF4) — still a net reduction.

**sessionStorage shape updated, not migrated**  
WHY: `intake-summary.html` previously read `data.flags` (WF2 output shape). That shape is now replaced by `data.wf5` (orchestrator output shape). No migration needed — sessionStorage is session-scoped, not persisted. Updated the summary script to read `wf5.esi_level`, `wf5.primary_flag`, `wf5.acuity`, `wf5.disposition` directly.

---

## Phase 4 — RAG-Before-Routing Decision (Closed)

### Option B Evaluated and Deferred Permanently

**What Option B proposed:** Run a Pinecone retrieval step before Quick Classify so the routing decision is grounded in the knowledge base, not just the hardcoded system prompt criteria.

**Why we assessed it:** 7 stroke evaluation cases failed `source_match` (ESI-2 doc outranked stroke-specific docs at rank #1). The hypothesis was that passing retrieved stroke guidelines into Quick Classify would improve routing accuracy.

**Why we rejected it:**

1. **The evaluation failures are a metrics artifact, not a routing failure.** `keyword_hit` passes on all 7 stroke cases — clinical content is correct. `source_match` is a strict rank-1 check. The ESI-2 document outranks stroke-specific docs at retrieval because "FAST-positive stroke" is mentioned there too. RAG-before-routing would not fix this — the same embedding similarity would still rank ESI-2 first for stroke queries.

2. **The hardcoded prompt IS the clinical knowledge.** The Quick Classify system prompt encodes ESI vital thresholds, condition-specific patterns, and resource rules — the same information that would be retrieved from Pinecone. Running a retrieval step would pull back documents containing the criteria already in the prompt. Net information gain: zero.

3. **Cost impact goes the wrong direction.** Option B adds 1 embed + 1 Pinecone query to every single case — including ESI 4-5 (low-acuity), which currently costs zero extra API calls. At real ER ESI distribution (40–60% low-acuity), this meaningfully raises the weighted average cost. Phase 4's entire token optimization was about not doing work for low-acuity cases. Option B undoes that.

4. **Routing accuracy is already validated.** 6/6 test cases routed to the correct branch. STEMI → Critical, Stroke → Critical, Septic Shock → Critical, Vomiting → Urgent, Laceration → Urgent, Mild Dizziness → Low. The routing is not broken.

**When Option B would make sense:** If the knowledge base grew to hundreds of specialized conditions that couldn't fit in a prompt, or if routing criteria changed frequently enough that maintaining the hardcoded prompt became a bottleneck. Neither is true at this stage.

**Correct fix for the stroke source_match gap:** Expand stroke knowledge docs to increase their semantic distance from the ESI-2 doc, or relax the evaluation metric from rank-1 source_match to top-3 source presence. Either is a 15-minute change with no architectural impact.

**Decision: Option B permanently deferred. Prompt-embedded criteria (Option A) is the right architecture for this system at this scale.**

---

---

## Revised Roadmap — Demo-Scoped (June 2026)

### Context
Adjusted scope to target the Maven Agentic AI course demo. Priority is a demonstrable, end-to-end system that shows AI product craft — not feature completeness.

### Phase 4 — Remaining (Must Complete Before Demo)

| Item | Status | Notes |
|---|---|---|
| Supabase DB layer | ⏳ Next | Required dependency for Phase 5 observability. Logs encounter_id, branch, ESI level, primary_flag, latency_ms, complaint_summary per WF5 call. |
| STEMI time_targets prompt fix | ⏳ Next | One-line addition to Build Clinical Brief prompt. Door-to-balloon target missing from time_targets output. ~10 min. |
| Wire intake-flag-critical + intake-flag-moderate to WF5 | ❌ Deferred post-demo | intake-normal.html already demonstrates all 3 branches dynamically. These screens are polish, not substance for the demo. |

### Phase 5 — Demo Scope (Observability Only)

Full observability = data capture + storage + display. All three required to be demo-able.

**What gets built:**
- WF5 gets 1 additional node → writes each call to Supabase on completion (timestamp, branch, ESI level, primary_flag, latency_ms, complaint_summary)
- `dashboard.html` extended with live observability panel: calls today, branch distribution (critical/urgent/low), avg latency by branch, estimated token cost

**Why this is the right demo focus:** Shows AI PM thinking beyond "it works" — cost tracking, latency by branch, usage distribution. That's the signal the course demo is looking for.

**Not in Phase 5 demo scope:**
- Multi-turn interaction (requires session loop + conversation state)
- Queue intelligence (live queue feed from DB)

### Post-Demo Backlog (Phase 5 remainder + Phase 6)

| Item | Phase | Why Deferred |
|---|---|---|
| Multi-turn interaction | 5 | Requires session state management + conversation loop. Correct architecture but out of demo scope. |
| Queue intelligence — live queue feed from DB | 5 | Good Phase 5 item but adds no new PM craft dimension to demo vs. observability. |
| Wire intake-flag-critical + intake-flag-moderate | 4 | intake-normal covers all ESI tiers dynamically. |
| GitHub cleanup + README + live demo link | 6 | Post-demo portfolio polish. |
| Architecture diagram update | 6 | Reflects WF5 orchestrator. Do after system is stable. |
| Case study / EB1 content write-up | 6 | RAG-before-routing decision + token optimization are strong PM craft stories. Write after demo. |

---

## Session 4 — 2026-07-03: Phase 4 Closed, N8N Repo Resync

**Note:** The "demo scope" framing above (Phase 4/5 sections) is superseded — as of this session, there is no target demo/shadow-mode milestone. The product is being built out for completeness, not staged toward a specific showcase. See `ROADMAP.md` "Scope Note (2026-07-03)" for the full decision.

### Phase 4 (Agentic Architecture) — now fully complete

All five R4 items closed this session:

- **R4-4 (PII scope):** Removed `patient_name`/`patient_mrn` from the Supabase `encounters` upsert in `intake-normal.html` (Option B — kept on the form for display/context, never persisted). Two open questions deferred to the user: whether to clean up already-persisted PII rows, and whether `patient_dob` should also be dropped (roadmap only specified name/MRN).
- **R4-2 (Stroke RAG source fix):** Two real bugs found and fixed, not the ranking problem originally assumed:
  1. The live ingestion workflow ("ER Triage: Ingest Clinical Knowledge Base") was missing 6 of 24 knowledge-base documents, including `stroke-002` — never embedded into Pinecone. Fixed by restoring the full doc set and re-running ingestion.
  2. `evaluation.py` (the 300-case eval harness) was calling WF4 with a synthetic narrative string that had demographics and raw vitals digits baked into `complaint_text`, unlike production (which sends clean complaint text only). This noise was crowding out stroke-relevant matches. Fixed by pointing the harness at `patient_case.chief_complaint` instead of `query_text`.
  - Verified: 300/300 (100%) on re-run, up from 293/300 (97.67%). No knowledge-base synonym expansion was needed once the eval matched production's real input shape.
- **R4-3 (Consistency test):** Built and ran a 6-case, run-twice consistency test against WF5. Result: 6/6 identical (ESI level, primary_flag, disposition) after fixing an unrelated regression (see below). One earlier 5/6 result showing `primary_flag` wording drift ("asthma" vs "asthma exacerbation") turned out to be one-off GPT-4o sampling noise, not a systematic issue — no prompt changes were ultimately needed.

### Notable detour: self-inflicted `Quick Classify` regression

While attempting to tighten the `primary_flag` prompt wording (later abandoned as unnecessary — see R4-3 above), repeated edits to the live `Quick Classify` node broke it with `"undefined" is not valid JSON` errors. Root cause: the local repo copy of `wf5-orchestrator.json` predated the guardrail integration and still referenced `$json.body.complaint_text` / `$json.body.{bp,hr,spo2,temp,rr}`. Production had already been correctly updated to `$json.complaint_text` / `$json.vitals.{bp,hr,spo2,temp,rr}` (matching the `Guardrail Route` node's output shape). Pasting prompt edits built from the stale local file overwrote the live node's correct logic with the outdated pattern — a regression introduced and fixed within this same session, with **no impact on historical production data**. Fixed by restoring the correct field references.

### N8N workflow repo resync

Discovered the local `n8n-workflows/` files were significantly out of sync with what's actually live in N8N Cloud — this was the second such discovery this session (the first being a stale, never-live draft ingestion workflow with a placeholder API key). User downloaded fresh exports of all 3 live workflows directly from N8N Cloud and shared them for reconciliation. Confirmed live topology:

1. **"ER Triage: Backend"** → merges what the repo had as two separate files (`wf1-parse-complaint.json` + `wf2-detect-flags.json`) into one workflow container with two independent webhook triggers (no functional change, matches the documented split-architecture decision).
2. **"ER Triage: Ingest Clinical Knowledge Base"** → merges retrieval (`wf4-retrieve-context.json`, exact match) with ingestion. Correction to what was believed earlier in this session: live ingestion uses raw HTTP nodes (`Embed Document` + `Upsert to Pinecone`, matching the old `wf3-ingest-knowledge.json` structure) with a **real** Pinecone API key — the LangChain-based file that was edited earlier for the R4-2 fix was never actually the live workflow (same workflow name, different/stale implementation). The R4-2 fix still worked correctly regardless, since the `Return Documents` code change is structure-agnostic and the user pasted it into whatever was actually live.
3. **"ER Triage: Orchestrator Agent"** → replaces `wf5-orchestrator.json`, confirmed to include the guardrail logic directly (`Guardrail Check`/`Guardrail Route`/`Guardrail Switch`/`Respond Blocked`) rather than as a separate `wf-guardrail.json` workflow.

Repo reorganized: fresh exports promoted to canonical names (`wf-backend.json`, `wf-ingest-and-retrieve.json`, `wf5-orchestrator.json`), 9 stale/superseded files moved to `n8n-workflows/archive/` (not deleted, kept for history): `wf1-parse-complaint.json`, `wf2-detect-flags.json`, `wf4-retrieve-context.json`, `ER Triage_ Ingest Clinical Knowledge Base.json` (LangChain draft, never live), `wf3-ingest-knowledge.json` (draft, never live), `wf-guardrail.json` (merged in), `wf-merged-parse-and-detect.json` + ` 2.json` variant (already-known retired), and the prior session's stale `wf5-orchestrator.json`.

### Scope decisions this session

- Demo/shadow-mode readiness dropped as a target milestone — building for product completeness instead. Phase 7 deprioritized accordingly (see `ROADMAP.md` Scope Note).
- **P6-2 (External EHR/FHIR integration) put ON HOLD** — highest effort remaining item (2-3 weeks), lowest near-term leverage. Phase 7 (portfolio wrap-up) moves up ahead of it, after P6-1.

### Current state

HHH scorecard: 9 of 10 dimensions passing. Only **P5-1 (observability dashboard)** remains open. Next up per the sequenced queue: P5-1 → P5-2 (nurse field modification capture, currently partial) → P5-4 (validator agent) → P5-6 (audio-to-text intake) → P5-3 (multi-turn) → P5-5 (queue intelligence) → P6-1 (prior visit history) → Phase 7 (portfolio wrap-up). P6-2 (FHIR) on hold indefinitely.

*Next immediate action: P5-1, Observability dashboard (2-3 hr) — reads from `encounters` + `eval_results` tables, closes the last open HHH gap.*
