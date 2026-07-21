-- ER Triage AI Co-pilot — Drop Leftover Unique Constraint on encounter_id
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- Requires: encounters table already created (schema.sql)

-- Context: an earlier session (2026-06-18) added a UNIQUE constraint on
-- encounter_id to support db.from("encounters").upsert(...). Session 7
-- (2026-07-10) deliberately moved the frontend back to plain .insert()
-- to avoid granting anon an UPDATE policy (see schema.sql — anon holds
-- the public key, so UPDATE access would let anyone rewrite any
-- patient's existing encounter row). The intended model since then is
-- one row per analyze() call, deduplicated at query time
-- (GROUP BY encounter_id ORDER BY created_at DESC LIMIT 1) rather than
-- one row upserted per encounter.
--
-- The UNIQUE constraint was never dropped when the code changed, so
-- every analyze() call after the first for the same encounter_id has
-- been silently failing (409, swallowed by console.warn) since
-- 2026-07-10. This migration closes that gap — no RLS/policy change,
-- no new grants, no new exposure.

ALTER TABLE encounters DROP CONSTRAINT IF EXISTS encounters_encounter_id_key;
