"""
Live Evaluation Script — ER Triage AI Co-pilot
Pulls production encounters from Supabase and scores them against ground truth.

Scoring dimensions per encounter (5 total):
  1. RAG Keyword Hit   — clinical keywords present in WF4 retrieved context
  2. RAG Source Match  — correct guideline source retrieved (via WF4)
  3. RAG Relevance     — top relevance score above threshold
  4. WF5 Output        — ESI level, acuity, and disposition match expected range for flag type
  5. Confidence Cal    — confidence level appropriate for the acuity returned

Maps to HHH:
  Helpful  → RAG keyword hit + ESI accuracy + acuity accuracy
  Honest   → RAG source match + confidence calibration
  Harmless → RAG relevance + disposition validity

Usage:
  python3 live_eval.py                      # eval all unscored encounters
  python3 live_eval.py --since 2026-06-18   # only encounters after this date
  python3 live_eval.py --limit 50           # cap at 50 encounters
  python3 live_eval.py --no-rag             # skip WF4 call, score WF5 output only
  python3 live_eval.py --no-write           # dry run, print results without writing

Requires env vars:
  SUPABASE_URL          project URL (e.g. https://lcaslbfjygzniosaobue.supabase.co)
  SUPABASE_SERVICE_KEY  service role key — needed to read encounters (bypasses RLS)

Optional env vars:
  WF4_URL               defaults to veekayc.app.n8n.cloud/webhook/retrieve-context
"""

import json
import argparse
import os
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone

# ── Config ───────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lcaslbfjygzniosaobue.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
WF4_URL = os.environ.get("WF4_URL", "https://veekayc.app.n8n.cloud/webhook/retrieve-context")
ANSWER_KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Evaluation_Answer_Key.json")
REQUEST_DELAY_S = 0.4

# Valid WF5 disposition values per ESI level (from prompt guardrails)
VALID_DISPOSITIONS_BY_ESI = {
    1: {"resuscitation_room"},
    2: {"immediate_bed"},
    3: {"urgent_bed", "waiting_room_monitored"},
    4: {"fast_track", "waiting_room"},
    5: {"fast_track", "waiting_room"},
}

# Confidence requirements per acuity — critical/high must never return low confidence
CONFIDENCE_FLOOR = {
    "critical": {"high", "medium"},
    "high":     {"high", "medium"},
    "medium":   {"high", "medium", "low"},
    "low":      {"high", "medium", "low"},
}

# Map WF5 primary_flag strings → answer key flag categories
FLAG_MAP = [
    (["stemi", "acute mi", "myocardial", "cardiac arrest", "chest pain"], "Acute MI Indicator"),
    (["stroke", "confusion", "dysarthria", "facial droop", "arm weakness", "tpa"], "Stroke Indicator"),
    (["anaphylaxis", "anaphylactic", "bee sting", "epipen", "epinephrine", "throat tight"], "Anaphylaxis"),
    (["allergic", "allergy", "rash", "hives", "urticaria"], "Possible Allergic Reaction"),
    (["respiratory", "dyspnea", "shortness of breath", "breathing", "wheezing", "copd", "asthma"], "Respiratory Distress"),
    (["suicid", "self-harm", "overdose", "mental health crisis", "psychiatric"], "Suicidal Ideation"),
]


# ── Ground truth loader ───────────────────────────────────────────────────────

def load_ground_truth(path: str) -> dict:
    """
    Build lookup: flag_category -> {expected_esi, expected_acuity, eval_criteria}
    expected_esi and expected_acuity are sets derived from all matching answer key records.
    """
    with open(path) as f:
        answer_key = json.load(f)

    criteria = {}
    for case in answer_key:
        gt = case["ground_truth"]
        flag = gt["flag"]
        if flag not in criteria:
            criteria[flag] = {
                "expected_esi": set(),
                "expected_acuity": set(),
                "eval_criteria": case["evaluation_criteria"],
            }
        criteria[flag]["expected_esi"].add(str(gt["expected_esi"]))
        criteria[flag]["expected_acuity"].add(gt["acuity"].lower())

    return criteria


def map_production_flag(primary_flag: str) -> str:
    """Map WF5 primary_flag to the closest answer key flag category."""
    if not primary_flag:
        return "No Critical Flag"
    pf = primary_flag.lower()
    for keywords, category in FLAG_MAP:
        if any(kw in pf for kw in keywords):
            return category
    return "No Critical Flag"


# ── Supabase client ───────────────────────────────────────────────────────────

def supabase(method: str, path: str, body: dict = None, headers_extra: dict = None) -> object:
    if not SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_KEY env var not set.\n"
            "Get it from: Supabase Dashboard → Settings → API → service_role key"
        )
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    data = json.dumps(body).encode() if body else None
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    if method == "GET":
        del headers["Content-Type"]
        del headers["Prefer"]
    if headers_extra:
        headers.update(headers_extra)

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body_bytes = resp.read()
            return json.loads(body_bytes) if body_bytes else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase {method} {path} → HTTP {e.code}: {e.read().decode()}")


def fetch_encounters(since: str = None, limit: int = 200) -> list:
    fields = "encounter_id,complaint_text,vitals,esi_level,acuity,primary_flag,disposition,confidence,ai_branch,retrieved_guidelines,created_at"
    path = f"encounters?select={fields}&order=created_at.desc&limit={limit}"
    if since:
        path += f"&created_at=gte.{since}"
    return supabase("GET", path)


def fetch_already_scored() -> set:
    try:
        rows = supabase("GET", "eval_results?select=encounter_id")
        return {r["encounter_id"] for r in rows}
    except Exception:
        return set()


def write_eval_result(row: dict):
    supabase("POST", "eval_results", row)


# ── WF4 RAG scoring ───────────────────────────────────────────────────────────

def call_wf4(complaint_text: str, flag: str, acuity: str) -> dict:
    urgency_map = {"critical": "high", "high": "high", "medium": "moderate", "low": "low"}
    payload = json.dumps({
        "complaint_text": complaint_text,
        "complaint_category": "",
        "flag_type": flag if "No Critical" not in flag else "",
        "urgency": urgency_map.get((acuity or "").lower(), "low"),
    }).encode()

    req = urllib.request.Request(
        WF4_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "retrieved_context": []}


def score_rag(retrieved: dict, eval_criteria: dict) -> dict:
    context_items = retrieved.get("retrieved_context", [])
    all_text = " ".join(
        (r.get("title", "") + " " + r.get("excerpt", "")).lower()
        for r in context_items
    )
    all_sources = [r.get("source", "") for r in context_items]
    top_score = context_items[0].get("relevance_score", 0) if context_items else 0

    keywords = eval_criteria.get("expected_guideline_keywords", [])
    keyword_hit = any(kw.lower() in all_text for kw in keywords) if keywords else True

    expected_sources = eval_criteria.get("expected_sources", [])
    source_match = any(s in all_sources for s in expected_sources) if expected_sources else True

    relevance_ok = top_score >= eval_criteria.get("min_relevance_score", 60)

    return {
        "rag_keyword_hit": keyword_hit,
        "rag_source_match": source_match,
        "rag_relevance_ok": relevance_ok,
        "rag_top_score": top_score,
        "rag_top_guideline": retrieved.get("top_guideline"),
    }


# ── WF5 output scoring ────────────────────────────────────────────────────────

def score_output(encounter: dict, gt: dict) -> dict:
    esi = encounter.get("esi_level")
    acuity = (encounter.get("acuity") or "").lower()
    disposition = (encounter.get("disposition") or "").lower().replace(" ", "_")
    confidence = (encounter.get("confidence") or "").lower()

    expected_esi = gt.get("expected_esi", set())
    expected_acuity = gt.get("expected_acuity", set())

    esi_match = str(esi) in expected_esi if (esi and expected_esi) else True
    acuity_match = acuity in expected_acuity if (acuity and expected_acuity) else True

    valid_dispositions = VALID_DISPOSITIONS_BY_ESI.get(esi, set())
    disposition_valid = disposition in valid_dispositions if (disposition and valid_dispositions) else True

    allowed_confidence = CONFIDENCE_FLOOR.get(acuity, {"high", "medium", "low"})
    confidence_calibrated = confidence in allowed_confidence if confidence else True

    return {
        "esi_match": esi_match,
        "acuity_match": acuity_match,
        "disposition_valid": disposition_valid,
        "confidence_calibrated": confidence_calibrated,
    }


# ── Summary and report ────────────────────────────────────────────────────────

def build_summary(scored: list) -> dict:
    total = len(scored)
    if not total:
        return {}

    def rate(key):
        vals = [s[key] for s in scored if s.get(key) is not None]
        return round(sum(1 for v in vals if v) / len(vals), 4) if vals else None

    by_flag = defaultdict(lambda: {"pass": 0, "total": 0})
    for s in scored:
        flag = s.get("matched_flag", "Unknown")
        by_flag[flag]["total"] += 1
        if s.get("overall_pass"):
            by_flag[flag]["pass"] += 1

    failures = [s for s in scored if not s.get("overall_pass")]
    failure_reasons = defaultdict(int)
    for s in failures:
        for reason in json.loads(s.get("failure_reasons", "[]")):
            failure_reasons[reason] += 1

    return {
        "total": total,
        "passed": sum(1 for s in scored if s.get("overall_pass")),
        "pass_rate": rate("overall_pass"),
        # RAG dimensions
        "rag_keyword_hit_rate": rate("rag_keyword_hit"),
        "rag_source_match_rate": rate("rag_source_match"),
        "rag_relevance_ok_rate": rate("rag_relevance_ok"),
        "avg_rag_score": round(
            sum(s.get("rag_top_score", 0) for s in scored) / total, 1
        ),
        # Output dimensions
        "esi_match_rate": rate("esi_match"),
        "acuity_match_rate": rate("acuity_match"),
        "disposition_valid_rate": rate("disposition_valid"),
        "confidence_calibrated_rate": rate("confidence_calibrated"),
        # Breakdowns
        "by_flag": [
            {
                "flag": flag,
                "pass": counts["pass"],
                "total": counts["total"],
                "pass_rate": round(counts["pass"] / counts["total"], 4),
            }
            for flag, counts in sorted(by_flag.items())
        ],
        "top_failure_reasons": dict(sorted(failure_reasons.items(), key=lambda x: -x[1])),
    }


def print_report(scored: list, summary: dict, run_id: str):
    total = summary.get("total", 0)
    if not total:
        print("No encounters scored.")
        return

    passed = summary["passed"]
    pct = summary["pass_rate"] * 100

    print()
    print("=" * 68)
    print(f"  LIVE EVAL REPORT  |  run_id: {run_id}")
    print(f"  {total} production encounters  |  {passed} passed  |  {pct:.1f}% pass rate")
    print("=" * 68)

    # RAG quality
    rag_kh = summary.get("rag_keyword_hit_rate")
    rag_sm = summary.get("rag_source_match_rate")
    rag_ro = summary.get("rag_relevance_ok_rate")
    print()
    print("  HELPFUL")
    print(f"    RAG Keyword Hit        : {f'{rag_kh*100:.1f}%' if rag_kh is not None else 'skipped (--no-rag)'}")
    print(f"    ESI Match Rate         : {summary['esi_match_rate']*100:.1f}%")
    print(f"    Acuity Match Rate      : {summary['acuity_match_rate']*100:.1f}%")

    print()
    print("  HONEST")
    print(f"    RAG Source Match       : {f'{rag_sm*100:.1f}%' if rag_sm is not None else 'skipped (--no-rag)'}")
    print(f"    Confidence Calibrated  : {summary['confidence_calibrated_rate']*100:.1f}%")

    print()
    print("  HARMLESS")
    print(f"    RAG Relevance OK       : {f'{rag_ro*100:.1f}%' if rag_ro is not None else 'skipped (--no-rag)'}")
    print(f"    Avg RAG Score          : {summary['avg_rag_score']}")
    print(f"    Disposition Valid      : {summary['disposition_valid_rate']*100:.1f}%")

    # By flag
    print()
    print("  By Flag Type:")
    for entry in summary.get("by_flag", []):
        bar_filled = int(entry["pass_rate"] * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        status = "✅" if entry["pass_rate"] == 1.0 else "❌"
        print(f"    {status} {bar}  {entry['pass']}/{entry['total']}  {entry['flag']}")

    # Failure reasons
    if summary.get("top_failure_reasons"):
        print()
        print("  Failure Breakdown:")
        for reason, count in summary["top_failure_reasons"].items():
            print(f"    {count:>3}x  {reason}")

    # Sample failures
    failures = [s for s in scored if not s.get("overall_pass")]
    if failures:
        print()
        print(f"  Failures ({len(failures)}):")
        for f in failures[:10]:
            reasons = json.loads(f.get("failure_reasons", "[]"))
            print(f"    {f.get('encounter_id')}  [{f.get('matched_flag')}]")
            print(f"      ESI: {f.get('actual_esi')}  Acuity: {f.get('matched_acuity')}  Reasons: {', '.join(reasons)}")

    print()
    print("=" * 68)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Live evaluation of production encounters against ground truth")
    parser.add_argument("--since", type=str, default=None,
                        help="ISO date string — only score encounters created after this (e.g. 2026-06-18)")
    parser.add_argument("--limit", type=int, default=200,
                        help="Max encounters to pull from Supabase (default: 200)")
    parser.add_argument("--no-rag", action="store_true",
                        help="Skip WF4 RAG call — score WF5 output quality only")
    parser.add_argument("--no-write", action="store_true",
                        help="Dry run — print results but do not write to eval_results table")
    parser.add_argument("--run-id", type=str, default=None,
                        help="Custom eval run ID for grouping results (default: auto timestamp)")
    args = parser.parse_args()

    run_id = args.run_id or f"live-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    # Load ground truth
    if not os.path.exists(ANSWER_KEY_PATH):
        print(f"ERROR: Answer key not found at {ANSWER_KEY_PATH}")
        sys.exit(1)
    print(f"Loading ground truth...")
    criteria_by_flag = load_ground_truth(ANSWER_KEY_PATH)
    print(f"  {len(criteria_by_flag)} flag categories loaded: {list(criteria_by_flag.keys())}")

    # Fetch encounters
    print(f"\nFetching encounters (limit={args.limit}, since={args.since or 'all time'})...")
    try:
        encounters = fetch_encounters(since=args.since, limit=args.limit)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    print(f"  {len(encounters)} encounters fetched")

    if not encounters:
        print("Nothing to score.")
        sys.exit(0)

    # Skip already-scored encounters
    if not args.no_write:
        already_scored = fetch_already_scored()
        before = len(encounters)
        encounters = [e for e in encounters if e.get("encounter_id") not in already_scored]
        skipped = before - len(encounters)
        if skipped:
            print(f"  {skipped} already scored — skipping")
    print(f"  {len(encounters)} encounters to score")

    if not encounters:
        print("All encounters already scored. Use --since to target a specific window.")
        sys.exit(0)

    # Score each encounter
    scored = []
    print(f"\nScoring (run_id={run_id}) {'[dry run]' if args.no_write else ''}...")

    for i, enc in enumerate(encounters):
        enc_id = enc.get("encounter_id", f"unknown-{i}")
        complaint = enc.get("complaint_text", "")
        primary_flag = enc.get("primary_flag", "")
        acuity = enc.get("acuity", "")
        esi = enc.get("esi_level")

        matched_flag = map_production_flag(primary_flag)
        gt = criteria_by_flag.get(matched_flag, {})

        # RAG quality
        if not args.no_rag and complaint:
            retrieved = call_wf4(complaint, matched_flag, acuity)
            rag_scores = score_rag(retrieved, gt.get("eval_criteria", {}))
            time.sleep(REQUEST_DELAY_S)
        else:
            rag_scores = {
                "rag_keyword_hit": None,
                "rag_source_match": None,
                "rag_relevance_ok": None,
                "rag_top_score": 0,
                "rag_top_guideline": None,
            }

        # WF5 output quality
        output_scores = score_output(enc, gt)

        # Failure reasons
        failure_reasons = []
        if rag_scores.get("rag_keyword_hit") is False:
            failure_reasons.append("rag_keyword_miss")
        if rag_scores.get("rag_source_match") is False:
            failure_reasons.append("rag_wrong_source")
        if rag_scores.get("rag_relevance_ok") is False:
            failure_reasons.append("rag_low_relevance")
        if not output_scores["esi_match"]:
            failure_reasons.append("esi_mismatch")
        if not output_scores["acuity_match"]:
            failure_reasons.append("acuity_mismatch")
        if not output_scores["disposition_valid"]:
            failure_reasons.append("invalid_disposition")
        if not output_scores["confidence_calibrated"]:
            failure_reasons.append("confidence_miscalibrated")

        overall_pass = len(failure_reasons) == 0

        row = {
            "eval_run_id": run_id,
            "encounter_id": enc_id,
            "matched_flag": matched_flag,
            "matched_acuity": acuity,
            "expected_esi": json.dumps(sorted(gt.get("expected_esi", []))),
            "actual_esi": esi,
            **rag_scores,
            **output_scores,
            "overall_pass": overall_pass,
            "failure_reasons": json.dumps(failure_reasons),
        }
        scored.append(row)

        if not args.no_write:
            try:
                write_eval_result(row)
            except Exception as e:
                print(f"\n  WARN: failed to write {enc_id}: {e}")

        print("." if overall_pass else "✗", end="", flush=True)
        if (i + 1) % 50 == 0:
            print(f" {i+1}", flush=True)

    print()

    summary = build_summary(scored)
    print_report(scored, summary, run_id)

    if args.no_write:
        print("  [Dry run complete — nothing written to Supabase]\n")
    else:
        print(f"  Results written to eval_results table\n")


if __name__ == "__main__":
    main()
