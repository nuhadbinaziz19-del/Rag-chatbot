"""
Retrieval + answer evaluation harness.

Usage:
    cd backend
    python eval/run_eval.py eval/questions.json --document-id 1 --user-id 1

Each question needs:
  - "question": str
  - "expected_doc": int | null           -> pass if any top-k chunk comes from this document
  - "expected_page": int | null          -> pass if any top-k chunk is from this page
  - "expected_keywords": [str]           -> pass if ALL keywords appear in the retrieved context (case-insensitive)

Reports: top-k retrieval accuracy, keyword coverage, and (if ANTHROPIC_API_KEY is set) generates
answers and prints them for manual grading, since correctness of free-text answers still needs a human.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.services.prompt import SYSTEM, build_messages  # noqa: E402
from app.services.retrieve import retrieve  # noqa: E402


def check(case: dict, chunks: list[dict]) -> dict:
    context = " ".join(c["content"].lower() for c in chunks)
    result = {"id": case["id"], "question": case["question"], "retrieved": len(chunks)}

    if case.get("expected_doc") is not None:
        result["doc_hit"] = any(c["document_id"] == case["expected_doc"] for c in chunks)
    if case.get("expected_page") is not None:
        result["page_hit"] = any(c["page"] == case["expected_page"] for c in chunks)
    if case.get("expected_keywords"):
        found = [k for k in case["expected_keywords"] if k.lower() in context]
        result["keyword_coverage"] = len(found) / len(case["expected_keywords"])
        result["missing_keywords"] = [k for k in case["expected_keywords"] if k not in found]
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("questions_file")
    ap.add_argument("--user-id", type=int, required=True)
    ap.add_argument("--document-id", type=int, default=None)
    ap.add_argument("--top-k", type=int, default=settings.context_chunks)
    ap.add_argument("--generate-answers", action="store_true", help="Also call the LLM (costs tokens).")
    args = ap.parse_args()

    cases = json.loads(Path(args.questions_file).read_text(encoding="utf-8"))
    doc_ids = [args.document_id] if args.document_id else None
    results, latencies = [], []

    for case in cases:
        t0 = time.perf_counter()
        chunks = retrieve(case["question"], args.top_k, args.user_id, doc_ids)
        latencies.append(time.perf_counter() - t0)
        r = check(case, chunks)

        if args.generate_answers and chunks:
            from app.services.llm import stream_answer

            r["answer"] = "".join(stream_answer(SYSTEM, build_messages(case["question"], chunks, [])))

        results.append(r)
        print(f"[{r['id']}] {case['question']!r} -> retrieved {r['retrieved']} chunks")
        if "answer" in r:
            print(f"    answer: {r['answer'][:200]}")

    def rate(key: str) -> float | None:
        vals = [r[key] for r in results if key in r]
        return round(sum(vals) / len(vals), 3) if vals else None

    print("\n--- Summary ---")
    print(f"Questions:              {len(results)}")
    print(f"Doc-hit@{args.top_k}:            {rate('doc_hit')}")
    print(f"Page-hit@{args.top_k}:           {rate('page_hit')}")
    print(f"Keyword coverage:       {rate('keyword_coverage')}")
    print(f"Avg retrieval latency:  {sum(latencies) / len(latencies):.3f}s")

    Path("eval/last_run.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Full results written to eval/last_run.json")


if __name__ == "__main__":
    main()
