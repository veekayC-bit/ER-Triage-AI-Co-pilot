#!/usr/bin/env node
// Generates a one-time Supabase magic link for a single recruiter/reviewer.
// Run manually per person: node scripts/generate-magic-link.js <email> [redirectTo]
// Prints the link — paste it into your own outreach (email/LinkedIn) rather
// than relying on Supabase's invite-email mailer.
//
// Reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from er-triage-phase-1/.env
// (gitignored, never committed, never web-reachable). The service_role key
// bypasses RLS — this script only ever runs locally, never in a browser.

const fs = require("fs");
const path = require("path");

const ENV_FILE = path.join(__dirname, "..", ".env");
const DEFAULT_REDIRECT = "https://er-triage-ai-co-pilot.pages.dev/intake-normal.html";

function readEnvVar(name) {
  const contents = fs.readFileSync(ENV_FILE, "utf8");
  const match = contents.match(new RegExp(`^${name}=(.*)$`, "m"));
  return match ? match[1].trim() : undefined;
}

async function main() {
  const [email, redirectTo = DEFAULT_REDIRECT] = process.argv.slice(2);

  if (!email) {
    console.error("Usage: node scripts/generate-magic-link.js <email> [redirectTo]");
    process.exit(1);
  }

  if (!fs.existsSync(ENV_FILE)) {
    console.error(`No .env file found at ${ENV_FILE}`);
    process.exit(1);
  }

  const supabaseUrl = readEnvVar("SUPABASE_URL");
  const serviceRoleKey = readEnvVar("SUPABASE_SERVICE_ROLE_KEY");

  if (!supabaseUrl || !serviceRoleKey) {
    console.error(
      "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.\n" +
      "Add SUPABASE_SERVICE_ROLE_KEY=<service_role key from Supabase dashboard > Settings > API> to .env."
    );
    process.exit(1);
  }

  const res = await fetch(`${supabaseUrl}/auth/v1/admin/generate_link`, {
    method: "POST",
    headers: {
      apikey: serviceRoleKey,
      Authorization: `Bearer ${serviceRoleKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      type: "magiclink",
      email,
      options: { redirectTo }
    })
  });

  const data = await res.json();

  if (!res.ok) {
    console.error(`Supabase Admin API error (${res.status}):`, JSON.stringify(data, null, 2));
    process.exit(1);
  }

  const actionLink = data.action_link || data.properties?.action_link;

  if (!actionLink) {
    console.error("No action_link in response:", JSON.stringify(data, null, 2));
    process.exit(1);
  }

  console.log(`Magic link for ${email} (redirects to ${redirectTo}):\n`);
  console.log(actionLink);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
