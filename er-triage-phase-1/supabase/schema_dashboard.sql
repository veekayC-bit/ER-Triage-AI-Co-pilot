-- ER Triage AI Co-pilot — Dashboard Instrumentation Migration (P5-1)
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- Requires: encounters table already created (schema.sql)

-- Adds columns to capture per-encounter latency and OpenAI token usage
-- so the observability dashboard can report real numbers instead of
-- estimates. Populated by intake-normal.html at write time; NULL for
-- any encounter rows written before this migration ran.

ALTER TABLE encounters
  ADD COLUMN IF NOT EXISTS latency_ms       INTEGER,
  ADD COLUMN IF NOT EXISTS prompt_tokens    INTEGER,
  ADD COLUMN IF NOT EXISTS completion_tokens INTEGER;
