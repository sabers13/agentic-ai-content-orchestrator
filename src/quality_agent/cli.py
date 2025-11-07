# src/quality_agent/cli.py
import argparse
from src.quality_agent.quality_runner import process_file

def main():
    parser = argparse.ArgumentParser(description="Quality Agent for blog drafts")
    parser.add_argument("--input", required=True, help="Path to draft JSON")
    parser.add_argument("--final-dir", default="data/final")
    parser.add_argument("--rejected-dir", default="data/rejected")
    args = parser.parse_args()

    res = process_file(args.input, args.final_dir, args.rejected_dir)

    if res["passes"]:
        print("[PASS] Draft accepted.")
        print(f"Quality score: {res['quality_score']}, SEO: {res['seo_score']}")
    else:
        print("[FAIL] Draft rejected.")
        for r in res["reasons"]:
            print(" -", r)

if __name__ == "__main__":
    main()
