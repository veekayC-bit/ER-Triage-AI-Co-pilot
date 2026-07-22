---
name: feedback-n8n-workflow-json-comments
description: Every N8N workflow JSON committed to the repo must carry a top-level "_comment" field documenting its webhook path, purpose, and which frontend screens/fields it supports
metadata:
  type: feedback
---

Every N8N workflow JSON file in `er-triage-phase-1/n8n-workflows/` must have a top-level `"_comment"` field as the first key (right after the opening brace), documenting: the webhook path it serves, what the workflow does, and which frontend fields/sections/screens depend on it.

**Why:** Standing rule set by the user 2026-07-21, directly motivated by that same session's `detect-flags` incident — a workflow existed live in N8N Cloud with zero local documentation of what it was for or which screens called it, which made the outage far harder to diagnose than it should have been (curl/CORS-level debugging couldn't find the real cause; only pulling the live JSON did). Also motivated by the broader recurring pattern this session surfaced repeatedly: local `n8n-workflows/*.json` silently drifting from live N8N Cloud state (see [[project-build-state]] — `wf-backend.json`/`wf5-orchestrator.json` themselves went stale on CORS values within the same session they were edited in Cloud). A `_comment` field doesn't stop drift, but it means anyone opening the file later — including a future Claude session — immediately knows what the workflow is supposed to do without reverse-engineering it from node structure.

**How to apply:**
- Mandatory, not optional, for any new workflow JSON committed to the repo from now on.
- Applied retroactively to all 4 canonical files as of commit `958f4e5`/same session: `wf-backend.json`, `wf5-orchestrator.json`, `wf-ingest-and-retrieve.json`, `wf-detect-flags.json`.
- If exporting a fresh workflow JSON from N8N Cloud (which won't have this field), add it before committing — don't commit a bare export.
- Keep it in sync if the workflow's webhook path or consuming screens change — a stale `_comment` is arguably worse than none, since it actively misleads.
