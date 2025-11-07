# src/llm_compare/cli.py
import argparse
from src.llm_compare.evaluator import compare_models
from src.llm_compare.storage import save_result

def main():
    parser = argparse.ArgumentParser(description="LLM A/B comparison")
    parser.add_argument("--brief", required=True, help="Topic / content brief")
    parser.add_argument("--model-a", default="gpt-4o-mini")
    parser.add_argument("--model-b", default="gpt-4o-mini")
    parser.add_argument(
        "--tone",
        default=None,
        help="Optional tone hint (practical, technical, etc.).",
    )
    args = parser.parse_args()

    try:
        result = compare_models(args.brief, args.model_a, args.model_b, tone=args.tone)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        print("Hint: ensure OPENAI_API_KEY is set in your environment or .env file.")
        raise SystemExit(1) from exc

    save_result(result)

    print(f"[OK] Winner: {result.winner}")
    print(f"Stored run in data/runs.sqlite and JSON in data/runs/")
    print(f"Model A latency: {result.model_a.latency_ms} ms")
    print(f"Model B latency: {result.model_b.latency_ms} ms")

if __name__ == "__main__":
    main()
