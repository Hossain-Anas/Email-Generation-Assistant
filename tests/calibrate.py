"""Layer 2 metric calibration - needs one API key, no generator.

Proves the metrics can separate a great email from a bad one before spending
tokens on the full run. Run manually: python tests/calibrate.py
"""
from src.llm_client import LLMClient
from src import metrics

judge = LLMClient(provider="groq", model="openai/gpt-oss-120b", reasoning_effort="medium")

facts = ["Meeting was Tuesday", "15% discount before month end", "Demo is ready"]
tone = "Friendly but professional"

GREAT = """Subject: Great speaking Tuesday - next steps

Hi Jordan,
Thanks for the chat on Tuesday. Your demo environment is ready to explore, and we can
offer a 15% discount if you sign before month end. Happy to help with next steps.
Best, Sam"""

BAD = """hey. we talked. theres a discount maybe. anyway let me know whenever no rush
this email goes on and on with lots of filler and repeats itself and repeats itself."""

for label, email in [("GREAT", GREAT), ("BAD", BAD)]:
    fc = metrics.fact_coverage(judge, email, facts)["score"]
    ta = metrics.tone_alignment(judge, email, tone)["score"]
    cf = metrics.conciseness_fluency(judge, email)["score"]
    print(f"{label:5} fact={fc} tone={ta} concise={cf}")
