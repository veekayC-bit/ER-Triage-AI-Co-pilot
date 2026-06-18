-- ER Triage AI Co-pilot — Guardrail Audit Log
-- Run in: Supabase Dashboard → SQL Editor → New Query
-- Purpose: log blocked complaint attempts without storing the complaint text itself

CREATE TABLE IF NOT EXISTS guardrail_blocks (
  id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  encounter_id    TEXT        NOT NULL,          -- links to the session encounter
  blocked_at      TIMESTAMPTZ DEFAULT NOW(),
  block_layer     TEXT        NOT NULL,          -- 'client_injection' | 'llm_content'
  reason          TEXT,                          -- LLM-provided reason (for llm_content blocks)
  complaint_hash  TEXT,                          -- SHA-256 of blocked text — dedup only, not reversible
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Note: complaint text is never stored. complaint_hash is SHA-256 only.
-- This allows dedup analysis (same text blocked N times) without PII exposure.

CREATE INDEX IF NOT EXISTS idx_guardrail_blocks_encounter ON guardrail_blocks(encounter_id);
CREATE INDEX IF NOT EXISTS idx_guardrail_blocks_layer     ON guardrail_blocks(block_layer);
CREATE INDEX IF NOT EXISTS idx_guardrail_blocks_at        ON guardrail_blocks(blocked_at DESC);

ALTER TABLE guardrail_blocks ENABLE ROW LEVEL SECURITY;

-- anon key can INSERT (frontend logs client-side injection blocks)
CREATE POLICY "anon can insert guardrail_blocks"
  ON guardrail_blocks FOR INSERT TO anon WITH CHECK (true);

-- service_role can read all (for audit and analysis)
CREATE POLICY "service role full access on guardrail_blocks"
  ON guardrail_blocks FOR ALL TO service_role USING (true) WITH CHECK (true);
