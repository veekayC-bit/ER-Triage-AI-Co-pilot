---
name: feedback-discuss-judgment-calls
description: Judgment calls (scope omissions, what-counts-in-a-metric decisions, tradeoff choices) must be discussed with Venkat before implementing, not decided unilaterally and reported after the fact
metadata:
  type: feedback
---

Don't make product/scope judgment calls solo and present them as done deals — surface the tradeoff and ask before implementing, especially anything affecting what a metric measures, what gets included/excluded from calculations, or anything with an "Honest"/auditability HHH implication.

**Why:** Called out 2026-07-08 (Session 6) over the Session 5 decision to exclude Pinecone embedding-call tokens from the P5-1 token-usage-per-request calculation. The reasoning (embedding tokens are ~50x cheaper than chat tokens, negligible to the estimate) may well be correct, but it was decided and documented as a fait accompli in `project_build_summary.md` rather than surfaced as a choice for Venkat to weigh in on. This is exactly the kind of decision where the omission itself is a product-accuracy tradeoff, not a pure implementation detail — those are his call, not mine to make and retroactively document.

**How to apply:**
- Before implementing something that changes what a number *means* (what's counted, what's excluded, precision tradeoffs, sampling/estimation vs. exact), stop and ask — present 2-3 options with tradeoffs, let him pick.
- This is distinct from pure implementation choices (variable naming, which N8N node type to use, code structure) — those don't need a check-in.
- A useful test: if reversing the decision later would require a different schema, different UI copy, or would change a number a user/nurse/PM would see and reason about — discuss it first.
- Once decided (by him, or jointly), document it in `project_build_summary.md` under the relevant session with the actual tradeoff considered and why — not just the outcome. See [[project-build-state]] for where that file lives (`er-triage-phase-1/project_build_summary.md`).
- This complements the existing co-builder rule "never skip a phase gate without flagging the risk" — same spirit, applied to smaller in-flight decisions, not just phase gates.
