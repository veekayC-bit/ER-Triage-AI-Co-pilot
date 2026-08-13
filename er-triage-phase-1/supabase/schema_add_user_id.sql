-- ER Triage AI Co-pilot — Add user_id to encounters (P7-B)
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- Requires: encounters table already created (schema.sql)

-- Context: P7-B (Supabase Auth) is gating the app behind login and adding
-- JWT verification on all four browser-facing webhooks (parse-complaint,
-- orchestrate-triage, detect-flags, retrieve-context). ROADMAP.md's P7-B
-- section, "Critical implementation note for Option B," says whatever
-- writes user_id onto encounters must store the real Supabase Auth user
-- UUID from day one — never a placeholder, email string, or NULL — so a
-- future upgrade to Option A (RLS scoped by auth.uid()) is a cheap
-- policy-only change instead of a data backfill.
--
-- No RLS/policy change here. anon-key writes stay exactly as they are
-- today (INSERT-only, no SELECT policy) — this migration only adds the
-- column so the frontend (intake-normal.html's persistToSupabase) has
-- somewhere to put window.currentUser.id.

ALTER TABLE encounters ADD COLUMN IF NOT EXISTS user_id UUID;

COMMENT ON COLUMN encounters.user_id IS
  'Supabase Auth user UUID of the logged-in caller (session.user.id from the frontend, or the id returned by GET /auth/v1/user when N8N verifies the JWT). Populated starting P7-B (2026-08-13). Rows written before this migration will have NULL here — expected, not a bug.';
