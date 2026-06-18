-- ER Triage AI Co-pilot — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query

-- ── Encounters ──────────────────────────────────────────────
-- One row per AI triage session. Written by frontend after each
-- successful WF5 orchestrator response.

CREATE TABLE IF NOT EXISTS encounters (
  id                  UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  encounter_id        TEXT        NOT NULL,
  patient_name        TEXT,
  patient_mrn         TEXT,
  patient_dob         TEXT,
  patient_sex         TEXT,
  complaint_text      TEXT,
  vitals              JSONB,
  esi_level           INTEGER,
  acuity              TEXT,
  primary_flag        TEXT,
  disposition         TEXT,
  confidence          TEXT,
  time_targets        TEXT,
  clinical_protocol   TEXT,
  immediate_actions   JSONB,
  retrieved_guidelines JSONB,
  ai_branch           TEXT,
  ai_brief            JSONB,
  structured_fields   JSONB,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── Nurse Actions ────────────────────────────────────────────
-- Audit log of every accept / dismiss / override action a nurse
-- takes on AI-suggested structured fields. Feed for future RLHF.

CREATE TABLE IF NOT EXISTS nurse_actions (
  id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  encounter_id  TEXT        NOT NULL,
  action_type   TEXT        NOT NULL CHECK (action_type IN ('accept', 'dismiss', 'override')),
  field_name    TEXT,
  ai_value      TEXT,
  nurse_value   TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_encounters_encounter_id  ON encounters(encounter_id);
CREATE INDEX IF NOT EXISTS idx_encounters_created_at    ON encounters(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nurse_actions_encounter  ON nurse_actions(encounter_id);
CREATE INDEX IF NOT EXISTS idx_nurse_actions_created_at ON nurse_actions(created_at DESC);

-- ── Row Level Security ───────────────────────────────────────
-- Enable RLS — anon key can insert but NOT read other sessions.
-- Tighten before any production deployment.

ALTER TABLE encounters    ENABLE ROW LEVEL SECURITY;
ALTER TABLE nurse_actions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon can insert encounters"
  ON encounters FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon can insert nurse_actions"
  ON nurse_actions FOR INSERT TO anon WITH CHECK (true);
