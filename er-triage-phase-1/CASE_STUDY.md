# ER Triage AI Co-pilot — Case Study

Three decisions from this build that say more about product/engineering judgment than the feature list does: a cost-efficiency call, a debugging discipline story, and an architecture-risk call made under time pressure. Each includes what was actually tried, what turned out to be wrong, and what shipped.

---

## 1. Tiered acuity routing — cutting average token cost ~42% without touching output quality for the cases that matter

**The problem:** the first working version of the orchestrator ran the same three-step pipeline — GPT-4o classification, Pinecone retrieval, GPT-4o clinical brief generation — for every single intake, regardless of acuity. A patient here for a prescription refill (ESI 5) was paying the exact same token cost and getting the exact same depth of AI reasoning as a suspected STEMI (ESI 1). That's backwards: the low-acuity case needs almost nothing, and the critical case is exactly where you want to spend more, not less.

**The fix:** route by acuity tier immediately after classification. ESI 4–5 (Low) gets a lightweight, template-driven response with no RAG call and no second GPT-4o call at all. ESI 3 (Urgent) and ESI 1–2 (Critical) get the full RAG-retrieval-plus-clinical-brief treatment — but Critical gets a deeper prompt (immediate actions, time-to-intervention targets, disposition to resuscitation room) than Urgent does.

**Result:** ~42% reduction in average token cost across a representative case mix, while the cases that actually need deep reasoning — STEMI, stroke, anaphylaxis — get *more* structured output than before (dedicated time-target and disposition fields that the old one-size-fits-all pipeline didn't have room for). This is the tradeoff a real triage system should make: spend compute where clinical stakes are highest, not uniformly.

---

## 2. The stroke recall "failure" that wasn't a retrieval problem

**What it looked like:** an early 300-case evaluation run showed 293/300 (97.67%) recall, with every miss clustered in the stroke category. The obvious hypothesis: the knowledge base's stroke document was ranking below a more generic ESI-2 document at retrieval time — a classic embedding-similarity ranking problem, fixable by adding synonym expansion or re-weighting the stroke document.

**What actually happened when that was tested:** re-ranking wouldn't have worked, because the eval harness wasn't testing what production actually does. `evaluation.py` was calling the retrieval endpoint with a synthetic query string that baked in raw vitals digits ("BP 194/88, HR 104") alongside the complaint — noise that production never sends. The real orchestrator only ever embeds clean complaint text plus the classified flag and summary. That mismatch was crowding out stroke-relevant matches in the eval specifically, not in production.

**The second, compounding bug:** separately, the live N8N ingestion workflow had a truncated document list — 18 of 24 source documents, missing the stroke-specific guideline entirely. It had simply never been embedded into Pinecone.

**Why this is the actual story, not the retrieval-ranking one:** the instinct to fix the knowledge base first — re-weight embeddings, add synonyms, tune the index — would have been treating a symptom while leaving both real bugs in place. Fixing the eval harness's payload shape and restoring the full 24-document ingestion list took the recall to 300/300 (100%) with zero changes to the retrieval logic or the documents themselves. The lesson that generalizes: when an AI system's output looks wrong, check whether the *evaluation* matches production reality before touching the model or the knowledge base — a mismatched test can manufacture a problem that doesn't exist in the system it's supposed to be testing.

---

## 3. Finding — and closing — a duplicated-reasoning safety gap under real time pressure

**The gap:** two separate parts of the system needed to reason about the same 10 critical conditions (STEMI, stroke, anaphylaxis, sepsis, etc.) from the same raw complaint text — the main triage orchestrator (for ESI routing) and a separate flag-detection endpoint (for the nurse-facing alert screens). They were built as two independently-maintained GPT-4o prompts. By the time this was caught, they'd already drifted: the flag-detection prompt had a 10th condition ("Anaphylactoid reaction") and an independent vitals-consistency check that the orchestrator's prompt didn't carry. Two prompts reasoning separately over the same clinical judgment call is a real risk in a system like this — they can silently diverge further, and a nurse could get a different answer for the same complaint depending on which screen happened to be open.

**The first proposed fix was wrong, and it mattered that it got caught before being built.** The initial plan was for the flag-detection endpoint to call the orchestrator's public webhook directly to reuse its classification. On inspection, that would have: (a) paid for the orchestrator's full RAG-retrieval-and-clinical-brief-generation chain on every flag-screen request, roughly doubling real cost for output the flag screens never render; (b) consumed two full N8N execution slots per request instead of one, hitting the platform's concurrency quota twice as fast under load; and (c) coupled the flag-detection endpoint's reliability to the heavier orchestrator chain's latency and failure modes, when the two are supposed to be independent today.

**What shipped instead:** the shared classification logic was extracted into its own sub-workflow, called via an in-instance sub-workflow invocation (not a public network hop) from both the orchestrator and the flag-detection endpoint. Same single source of truth, but neither caller pays for work it doesn't need, and there's no added failure coupling to the heavier path.

**Validation discipline, not just a build:** before this replaced any real traffic, all 9 of the acceptance test cases — including a deliberately adversarial one designed to stress-test the vitals-independence rule (an unexplained critically low SpO2 next to a complaint that had nothing to do with breathing) — were run against the live endpoint and confirmed correct before calling the consolidation done. That specific check matters because it's the exact failure mode the original prompt had to be hardened against once already: letting an extreme vital independently imply a clinical flag instead of requiring literal textual evidence.

**Why this is the AI PM story, not just the engineering one:** the interesting decision here wasn't "should these be merged" — that was obvious once the drift was spotted. It was resisting the faster, more obvious integration path (call the existing public endpoint) once its downstream cost and reliability implications were actually worked out, under explicit pressure to move quickly toward wrapping up the project. Shipping the correct architecture took maybe 20% longer than the naive one would have. That's the tradeoff worth being able to explain in an interview.

---

*Full build history, decision log, and current phase status: [`ROADMAP.md`](./ROADMAP.md). Live demo: https://er-triage-ai-co-pilot.pages.dev*
