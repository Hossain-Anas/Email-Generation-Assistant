"""Runs one scenario through generation + all three metrics."""
from src.generator import generate_email
from src import metrics
import config


def evaluate_scenario(gen_client, judge_client, scenario, strategy):
    email = generate_email(
        gen_client,
        scenario["intent"],
        scenario["facts"],
        scenario["tone"],
        strategy=strategy,
        temperature=config.GEN_TEMPERATURE,
        max_tokens=config.GEN_MAX_TOKENS,
    )

    fc = metrics.fact_coverage(judge_client, email, scenario["facts"])
    ta = metrics.tone_alignment(judge_client, email, scenario["tone"])
    cf = metrics.conciseness_fluency(judge_client, email)

    overall = round((fc["score"] + ta["score"] + cf["score"]) / 3, 3)

    return {
        # flat fields -> CSV
        "id": scenario["id"],
        "intent": scenario["intent"],
        "tone": scenario["tone"],
        "strategy": strategy,
        "fact_coverage": fc["score"],
        "tone_alignment": ta["score"],
        "conciseness_fluency": cf["score"],
        "overall": overall,
        # rich fields -> JSON audit trail
        "generated_email": email,
        "details": {
            "fact_coverage": fc,
            "tone_alignment": ta,
            "conciseness_fluency": cf,
        },
    }
