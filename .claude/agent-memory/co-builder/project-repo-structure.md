---
name: project-repo-structure
description: What files exist in the ER Triage AI Co-pilot repo and what each folder contains
metadata:
  type: project
---

# Repo Structure — Product-er-ai-assist-system

Last updated: 2026-06-13

## Active ER Triage Build

```
/mockups/                         — All 6 frontend mockups (HTML/CSS, static)
  index.html                      — Mockup navigator
  architecture.html               — Architecture diagram
  intake-normal.html
  intake-flag-moderate.html
  intake-flag-critical.html
  intake-summary.html
  queue-panel.html
  manual-mode.html
  mockup-styles.css               — Shared stylesheet

/er-triage-phase-1/
  n8n-workflows/                  — resynced 2026-07-03 to match live N8N Cloud; verify against a fresh export before trusting for edits
    wf-backend.json               — live "ER Triage: Backend" (parse-complaint + detect-flags, 2 webhooks in one container)
    wf-ingest-and-retrieve.json   — live "ER Triage: Ingest Clinical Knowledge Base" (Pinecone ingestion via raw HTTP nodes + retrieval)
    wf5-orchestrator.json         — live "ER Triage: Orchestrator Agent" (includes guardrail logic inline)
    archive/                      — 9 superseded files kept for history, not live (old wf1/wf2/wf4/wf-guardrail, stale drafts)
  tests/
    test-wf1.sh                   — 8 PRD acceptance tests for WF-1
    test-wf2.sh                   — 8 PRD acceptance tests for WF-2

/prd_er_triage_ai.md              — Product Requirements Document

/.claude/agents/
  co-builder.md                   — Co-builder agent definition
  prd-mockup-generator.md         — Mockup generator agent definition
```

## Legacy / Archived (Document Parser Phase 2)

```
/document-parser-phase-2/         — Prior Python/RAG project, archived here
```

## Planning Docs (Non-build)

```
AI-PM-Roadmap.md
Technical-Roadmap.md
ZerotoOne-Path.md
Learnings.md
PRD/product_docs/productai_assessment.md
```

## Git Status Note

Many files show as `D` (deleted) in git status — these are the old Python/RAG stack that was moved to `document-parser-phase-2/` subfolder. The repo root is now clean for the ER Triage build.
