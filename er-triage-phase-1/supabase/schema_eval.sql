-- ER Triage AI Co-pilot — Live Eval Results Schema + Encounters Migration
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- Requires: encounters and nurse_actions tables already created (schema.sql)

-- ── Encounters migration ──────────────────────────────────────────────────────
-- Step 1: Remove duplicate encounter rows (keep most recent per encounter_id)
DELETE FROM encounters
WHERE id NOT IN (
  SELECT DISTINCT ON (encounter_id) id
  FROM encounters
  ORDER BY encounter_id, created_at DESC
);

-- Step 2: Add unique index so upsert works correctly going forward
CREATE UNIQUE INDEX IF NOT EXISTS encounters_encounter_id_key ON encounters(encounter_id);

-- ── Eval Results ─────────────────────────────────────────────────────────────
-- One row per encounter per eval run.
-- Written by live_eval.py using the service_role key.

CREATE TABLE IF NOT EXISTS eval_results (
  id                      UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  eval_run_id             TEXT        NOT NULL,         -- groups a batch run (e.g. live-20260618-143000)
  encounter_id            TEXT        NOT NULL,         -- links to encounters.encounter_id
  eval_timestamp          TIMESTAMPTZ DEFAULT NOW(),

  -- Ground truth matching
  matched_flag            TEXT,                         -- answer key flag category inferred from primary_flag
  matched_acuity          TEXT,                         -- acuity from the production encounter
  expected_esi            TEXT,                         -- JSON array of valid ESI values for this flag
  actual_esi              INTEGER,                      -- ESI level from the production encounter

  -- RAG quality (WF4 call) — NULL when run with --no-rag
  rag_keyword_hit         BOOLEAN,
  rag_source_match        BOOLEAN,
  rag_relevance_ok        BOOLEAN,
  rag_top_score           INTEGER,
  rag_top_guideline       TEXT,

  -- WF5 output quality
  esi_match               BOOLEAN,                      -- production ESI in expected range
  acuity_match            BOOLEAN,                      -- production acuity matches expected
  disposition_valid       BOOLEAN,                      -- disposition valid for the ESI level returned
  confidence_calibrated   BOOLEAN,                      -- confidence appropriate for acuity level

  -- Overall
  overall_pass            BOOLEAN,
  failure_reasons         JSONB,                        -- list of failed dimension keys

  created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_eval_results_run_id       ON eval_results(eval_run_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_encounter_id ON eval_results(encounter_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_created_at   ON eval_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eval_results_flag         ON eval_results(matched_flag);
CREATE INDEX IF NOT EXISTS idx_eval_results_pass         ON eval_results(overall_pass);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Only service_role (live_eval.py) can read/write eval_results.
-- Anon key (frontend) cannot see evaluation data.

ALTER TABLE eval_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service role full access on eval_results"
  ON eval_results FOR ALL TO service_role
  USING (true) WITH CHECK (true);

-- ── Useful queries ────────────────────────────────────────────────────────────
-- Uncomment and run in SQL Editor as needed.

-- Latest eval run summary:
-- SELECT
--   eval_run_id,
--   COUNT(*) AS total,
--   SUM(CASE WHEN overall_pass THEN 1 ELSE 0 END) AS passed,
--   ROUND(AVG(CASE WHEN overall_pass THEN 1.0 ELSE 0.0 END) * 100, 1) AS pass_pct,
--   ROUND(AVG(rag_top_score), 1) AS avg_rag_score,
--   ROUND(AVG(CASE WHEN esi_match THEN 1.0 ELSE 0.0 END) * 100, 1) AS esi_match_pct,
--   ROUND(AVG(CASE WHEN disposition_valid THEN 1.0 ELSE 0.0 END) * 100, 1) AS disposition_valid_pct
-- FROM eval_results
-- GROUP BY eval_run_id
-- ORDER BY MIN(created_at) DESC;

-- Failures by flag type:
-- SELECT matched_flag, COUNT(*) AS failures
-- FROM eval_results
-- WHERE NOT overall_pass
-- GROUP BY matched_flag
-- ORDER BY failures DESC;

-- Most common failure reasons:
-- SELECT jsonb_array_elements_text(failure_reasons) AS reason, COUNT(*) AS count
-- FROM eval_results
-- WHERE NOT overall_pass
-- GROUP BY reason
-- ORDER BY count DESC;

-- Pass rate trend by day:
-- SELECT
--   DATE(created_at) AS day,
--   COUNT(*) AS total,
--   ROUND(AVG(CASE WHEN overall_pass THEN 1.0 ELSE 0.0 END) * 100, 1) AS pass_pct
-- FROM eval_results
-- GROUP BY day
-- ORDER BY day;
