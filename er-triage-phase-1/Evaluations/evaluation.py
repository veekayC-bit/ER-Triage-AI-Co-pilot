"""
RAG Evaluation Script — ER Triage AI Co-pilot
Sends patient queries to WF4 (retrieve-context webhook), scores retrieved
guidelines against the Evaluation_Answer_Key.json ground truth.

Scoring dimensions per case:
  1. Keyword Hit    — expected flag keywords appear in retrieved excerpts
  2. Source Match   — expected Pinecone source appears in retrieved results
  3. Relevance OK   — top result relevance_score >= min threshold (default 60)

Usage:
  python3 evaluation.py                    # runs on 50 random cases
  python3 evaluation.py --sample 100       # 100 random cases
  python3 evaluation.py --sample 1000      # full dataset (slow, ~15-20 min)
  python3 evaluation.py --flag "Anaphylaxis"       # filter by flag
  python3 evaluation.py --acuity "Critical"        # filter by acuity
  python3 evaluation.py --sample 20 --verbose      # show per-case detail
"""

import json
import argparse
import random
import sys
import time
import csv
import os
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime

WF4_URL = "https://veekayc.app.n8n.cloud/webhook/retrieve-context"
ANSWER_KEY_PATH = "Evaluation_Answer_Key.json"
REQUEST_DELAY_S = 0.4   # stay under rate limits


def call_wf4(query_text: str, flag: str, acuity: str) -> dict:
    payload = json.dumps({
        "complaint_text": query_text,
        "complaint_category": "",
        "flag_type": flag if flag != "No Critical Flag" else "",
        "urgency": {"Critical": "high", "High": "high", "Medium": "moderate", "Low": "low"}.get(acuity, "low")
    }).encode()

    req = urllib.request.Request(
        WF4_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "retrieved_context": []}


def score_result(retrieved: dict, criteria: dict) -> dict:
    context_items = retrieved.get("retrieved_context", [])
    all_text = " ".join(
        (r.get("title", "") + " " + r.get("excerpt", "")).lower()
        for r in context_items
    )
    all_sources = [r.get("source", "") for r in context_items]
    top_score = context_items[0].get("relevance_score", 0) if context_items else 0

    keywords = criteria.get("expected_guideline_keywords", [])
    keyword_hit = any(kw.lower() in all_text for kw in keywords) if keywords else True

    expected_sources = criteria.get("expected_sources", [])
    source_match = any(s in all_sources for s in expected_sources) if expected_sources else True

    relevance_ok = top_score >= criteria.get("min_relevance_score", 60)

    overall = keyword_hit and source_match and relevance_ok

    return {
        "keyword_hit": keyword_hit,
        "source_match": source_match,
        "relevance_ok": relevance_ok,
        "overall_pass": overall,
        "top_score": top_score,
        "match_count": retrieved.get("match_count", 0),
        "top_guideline": retrieved.get("top_guideline"),
        "matched_keywords": [kw for kw in keywords if kw.lower() in all_text]
    }


def build_summary(results: list) -> dict:
    total = len(results)
    if total == 0:
        return {}
    passed = sum(1 for r in results if r["score"]["overall_pass"])

    by_cat = defaultdict(lambda: {"pass": 0, "total": 0})
    for r in results:
        cat = r["category"]
        by_cat[cat]["total"] += 1
        if r["score"]["overall_pass"]:
            by_cat[cat]["pass"] += 1

    by_acuity = defaultdict(lambda: {"pass": 0, "total": 0})
    for r in results:
        ac = r["acuity"]
        by_acuity[ac]["total"] += 1
        if r["score"]["overall_pass"]:
            by_acuity[ac]["pass"] += 1

    return {
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total, 4),
        "keyword_hit_rate": round(sum(1 for r in results if r["score"]["keyword_hit"]) / total, 4),
        "source_match_rate": round(sum(1 for r in results if r["score"]["source_match"]) / total, 4),
        "relevance_ok_rate": round(sum(1 for r in results if r["score"]["relevance_ok"]) / total, 4),
        "avg_top_relevance": round(sum(r["score"]["top_score"] for r in results) / total, 1),
        "by_category": [
            {
                "category": cat,
                "pass": counts["pass"],
                "total": counts["total"],
                "pass_rate": round(counts["pass"] / counts["total"], 4)
            }
            for cat, counts in sorted(by_cat.items())
        ],
        "by_acuity": [
            {
                "acuity": ac,
                "pass": by_acuity[ac]["pass"],
                "total": by_acuity[ac]["total"],
                "pass_rate": round(by_acuity[ac]["pass"] / by_acuity[ac]["total"], 4)
            }
            for ac in ["Critical", "High", "Medium", "Low"] if ac in by_acuity
        ]
    }


def save_results(results: list, args, output_dir: str = "."):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    seed_tag = f"_seed{args.seed}" if args.seed != 42 else ""
    flag_tag = f"_{args.flag.replace(' ', '')}" if args.flag else ""
    acuity_tag = f"_{args.acuity}" if args.acuity else ""
    base_name = f"eval_{timestamp}_{args.sample}cases{seed_tag}{flag_tag}{acuity_tag}"

    summary = build_summary(results)

    # --- JSON (full structured output for graphs) ---
    json_path = os.path.join(output_dir, base_name + ".json")
    output = {
        "run_metadata": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "sample_size": args.sample,
            "seed": args.seed,
            "filter_flag": args.flag,
            "filter_acuity": args.acuity,
            "wf4_url": WF4_URL
        },
        "summary": summary,
        "cases": [
            {
                "id": r["id"],
                "category": r["category"],
                "acuity": r["acuity"],
                "expected_esi": r["expected_esi"],
                "flag": r["flag"],
                "overall_pass": r["score"]["overall_pass"],
                "keyword_hit": r["score"]["keyword_hit"],
                "source_match": r["score"]["source_match"],
                "relevance_ok": r["score"]["relevance_ok"],
                "top_score": r["score"]["top_score"],
                "match_count": r["score"]["match_count"],
                "top_guideline": r["score"]["top_guideline"],
                "matched_keywords": r["score"]["matched_keywords"]
            }
            for r in results
        ],
        "failures": [
            {
                "id": r["id"],
                "category": r["category"],
                "acuity": r["acuity"],
                "flag": r["flag"],
                "reasons": (
                    (["keyword_miss"] if not r["score"]["keyword_hit"] else []) +
                    (["wrong_source"] if not r["score"]["source_match"] else []) +
                    (["low_relevance"] if not r["score"]["relevance_ok"] else [])
                ),
                "top_score": r["score"]["top_score"],
                "top_guideline": r["score"]["top_guideline"]
            }
            for r in results if not r["score"]["overall_pass"]
        ]
    }
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)

    # --- CSV (per-case rows for spreadsheet charting) ---
    csv_path = os.path.join(output_dir, base_name + ".csv")
    fieldnames = [
        "id", "category", "acuity", "expected_esi", "flag",
        "overall_pass", "keyword_hit", "source_match", "relevance_ok",
        "top_score", "match_count", "top_guideline"
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "id": r["id"],
                "category": r["category"],
                "acuity": r["acuity"],
                "expected_esi": r["expected_esi"],
                "flag": r["flag"],
                "overall_pass": r["score"]["overall_pass"],
                "keyword_hit": r["score"]["keyword_hit"],
                "source_match": r["score"]["source_match"],
                "relevance_ok": r["score"]["relevance_ok"],
                "top_score": r["score"]["top_score"],
                "match_count": r["score"]["match_count"],
                "top_guideline": r["score"]["top_guideline"]
            })

    return json_path, csv_path


def print_report(results: list, verbose: bool = False):
    total = len(results)
    if total == 0:
        print("No results to report.")
        return

    passed = sum(1 for r in results if r["score"]["overall_pass"])

    print("\n" + "=" * 62)
    print(f"  RAG EVALUATION REPORT  —  {total} cases evaluated")
    print("=" * 62)
    print(f"  Overall Pass Rate : {passed}/{total}  ({100*passed//total}%)")
    print(f"  Keyword Hit Rate  : {sum(1 for r in results if r['score']['keyword_hit'])}/{total}")
    print(f"  Source Match Rate : {sum(1 for r in results if r['score']['source_match'])}/{total}")
    print(f"  Relevance OK Rate : {sum(1 for r in results if r['score']['relevance_ok'])}/{total}")
    avg_score = sum(r["score"]["top_score"] for r in results) / total
    print(f"  Avg Top Relevance : {avg_score:.1f}%")

    # By complaint category
    by_cat = defaultdict(lambda: {"pass": 0, "total": 0})
    for r in results:
        cat = r["category"]
        by_cat[cat]["total"] += 1
        if r["score"]["overall_pass"]:
            by_cat[cat]["pass"] += 1

    print("\n  By Complaint Category:")
    print(f"  {'Category':<35} {'Pass':>5} {'Total':>6} {'Rate':>6}")
    print("  " + "-" * 55)
    for cat, counts in sorted(by_cat.items()):
        rate = 100 * counts["pass"] // counts["total"]
        bar = "█" * (rate // 10) + "░" * (10 - rate // 10)
        print(f"  {cat:<35} {counts['pass']:>5} {counts['total']:>6}  {bar} {rate}%")

    # By acuity
    by_acuity = defaultdict(lambda: {"pass": 0, "total": 0})
    for r in results:
        ac = r["acuity"]
        by_acuity[ac]["total"] += 1
        if r["score"]["overall_pass"]:
            by_acuity[ac]["pass"] += 1

    print("\n  By Acuity Level:")
    print(f"  {'Acuity':<12} {'Pass':>5} {'Total':>6} {'Rate':>6}")
    print("  " + "-" * 35)
    for ac in ["Critical", "High", "Medium", "Low"]:
        if ac in by_acuity:
            counts = by_acuity[ac]
            rate = 100 * counts["pass"] // counts["total"]
            print(f"  {ac:<12} {counts['pass']:>5} {counts['total']:>6}   {rate}%")

    # Failures summary
    failures = [r for r in results if not r["score"]["overall_pass"]]
    if failures:
        print(f"\n  Failures ({len(failures)}):")
        for r in failures[:10]:
            s = r["score"]
            reasons = []
            if not s["keyword_hit"]: reasons.append("keyword miss")
            if not s["source_match"]: reasons.append("wrong source")
            if not s["relevance_ok"]: reasons.append(f"low relevance ({s['top_score']}%)")
            print(f"    {r['id']} [{r['acuity']}] {r['flag']}")
            print(f"      Reason: {', '.join(reasons)}")
            print(f"      Top guideline: {s['top_guideline']}")
        if len(failures) > 10:
            print(f"    ... and {len(failures)-10} more")

    # Verbose per-case
    if verbose:
        print("\n  Per-Case Detail:")
        for r in results:
            s = r["score"]
            status = "✅" if s["overall_pass"] else "❌"
            print(f"  {status} {r['id']} | {r['flag']} | ESI {r['expected_esi']} | top={s['top_score']}% | {s['top_guideline']}")

    print("=" * 62)


def main():
    parser = argparse.ArgumentParser(description="Evaluate WF4 RAG retrieval quality")
    parser.add_argument("--sample", type=int, default=50, help="Number of cases to evaluate (default: 50)")
    parser.add_argument("--flag", type=str, default=None, help="Filter by flag type")
    parser.add_argument("--acuity", type=str, default=None, help="Filter by acuity (Critical/High/Medium/Low)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--verbose", action="store_true", help="Show per-case results")
    parser.add_argument("--no-save", action="store_true", help="Skip saving result files")
    args = parser.parse_args()

    with open(ANSWER_KEY_PATH) as f:
        answer_key = json.load(f)

    # Apply filters
    filtered = answer_key
    if args.flag:
        filtered = [r for r in filtered if args.flag.lower() in r["ground_truth"]["flag"].lower()]
    if args.acuity:
        filtered = [r for r in filtered if args.acuity.lower() == r["ground_truth"]["acuity"].lower()]

    if not filtered:
        print(f"No records match the filter criteria.")
        sys.exit(1)

    # Sample
    random.seed(args.seed)
    sample = random.sample(filtered, min(args.sample, len(filtered)))
    sample.sort(key=lambda x: x["id"])

    print(f"Evaluating {len(sample)} cases against WF4 at {WF4_URL}")
    if args.flag: print(f"Filter: flag = {args.flag}")
    if args.acuity: print(f"Filter: acuity = {args.acuity}")
    print("Running", end="", flush=True)

    results = []
    for i, record in enumerate(sample):
        gt = record["ground_truth"]
        retrieved = call_wf4(
            query_text=record["query_text"],
            flag=gt["flag"],
            acuity=gt["acuity"]
        )
        s = score_result(retrieved, record["evaluation_criteria"])
        results.append({
            "id": record["id"],
            "flag": gt["flag"],
            "acuity": gt["acuity"],
            "expected_esi": gt["expected_esi"],
            "category": gt["chief_complaint_category"],
            "score": s
        })
        dot = "." if s["overall_pass"] else "✗"
        print(dot, end="", flush=True)
        if (i + 1) % 50 == 0:
            print(f" {i+1}", flush=True)
        time.sleep(REQUEST_DELAY_S)

    print()
    print_report(results, verbose=args.verbose)

    if not args.no_save:
        output_dir = os.path.dirname(os.path.abspath(__file__))
        json_path, csv_path = save_results(results, args, output_dir=output_dir)
        print(f"\n  Saved → {os.path.basename(json_path)}")
        print(f"  Saved → {os.path.basename(csv_path)}")


if __name__ == "__main__":
    main()
