"""Entry point: run all scenarios x all strategies, write CSV/JSON/comparison."""
import argparse
import json

import pandas as pd

import config
from src.llm_client import LLMClient
from src.evaluator import evaluate_scenario

METRIC_DEFINITIONS = {
    "fact_coverage": "Fraction of key facts correctly present in the email (LLM-judge, 0-1).",
    "tone_alignment": "How well the email matches the requested tone (LLM-judge 1-5, normalized 0-1).",
    "conciseness_fluency": "Blend of a deterministic length score and an LLM grammar/fluency rating (0-1).",
}


def load_scenarios(limit=None):
    with open(config.DATA_FILE, encoding="utf-8") as f:
        scenarios = json.load(f)
    return scenarios[:limit] if limit else scenarios


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Run only first N scenarios (smoke test).")
    parser.add_argument("--gen-provider", default=config.GENERATOR_PROVIDER)
    parser.add_argument("--gen-model", default=config.GENERATOR_MODEL)
    parser.add_argument("--judge-provider", default=config.JUDGE_PROVIDER)
    parser.add_argument("--judge-model", default=config.JUDGE_MODEL)
    args = parser.parse_args()

    config.RESULTS_DIR.mkdir(exist_ok=True)
    scenarios = load_scenarios(args.limit)

    gen_client = LLMClient(provider=args.gen_provider, model=args.gen_model,
                           reasoning_effort=config.GEN_REASONING_EFFORT)
    judge_client = LLMClient(provider=args.judge_provider, model=args.judge_model,
                             reasoning_effort=config.JUDGE_REASONING_EFFORT)

    records = []
    for scenario in scenarios:
        for strategy in config.STRATEGIES:
            print(f"  Evaluating {scenario['id']} [{strategy}] ...")
            records.append(evaluate_scenario(gen_client, judge_client, scenario, strategy))

    # --- CSV (flat, no nested details) ---
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "details"} for r in records])
    csv_path = config.RESULTS_DIR / "evaluation_results.csv"
    df.to_csv(csv_path, index=False)

    # --- JSON (full audit trail + metric definitions) ---
    json_path = config.RESULTS_DIR / "evaluation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"metric_definitions": METRIC_DEFINITIONS, "records": records},
                  f, indent=2, ensure_ascii=False)

    # --- Averages + comparison report ---
    metric_cols = ["fact_coverage", "tone_alignment", "conciseness_fluency", "overall"]
    averages = df.groupby("strategy")[metric_cols].mean().round(3)
    print("\n=== Average scores by strategy ===")
    print(averages)

    winner = averages["overall"].idxmax()
    write_comparison_report(averages, winner)
    print(f"\nWinner by overall average: {winner}")
    print(f"Wrote: {csv_path}, {json_path}, and comparison_report.md")


def write_comparison_report(averages, winner):
    lines = ["# Comparison Report\n",
             "## Average scores by strategy\n",
             averages.to_markdown(), "\n",
             f"## Winner: **{winner}**\n"]
    if {"basic", "advanced"}.issubset(averages.index):
        delta = (averages.loc["advanced"] - averages.loc["basic"]).round(3)
        lines += ["## Advanced minus Basic (delta)\n", delta.to_frame("delta").to_markdown(), "\n"]
    lines += [
        "## Analysis (fill in from the data above)\n",
        "- **Which performed better?** ...\n",
        "- **Biggest failure mode of the loser?** ... (cite the metric that dropped most "
        "and a concrete example from evaluation_results.json)\n",
        "- **Production recommendation?** ... (justify with the numbers; add cost/latency notes)\n",
    ]
    (config.RESULTS_DIR / "comparison_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
