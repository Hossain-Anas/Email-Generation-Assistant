"""Layer 1 unit tests - no API key required, instant."""
import json

import config
from src.generator import _format_facts
from src.prompts import BASIC_USER, ADVANCED_USER, ADVANCED_SYSTEM
from src import metrics


# --- 1a. Fact formatting ---
def test_format_facts():
    assert _format_facts(["a", "b"]) == "- a\n- b"
    assert _format_facts([]) == ""


# --- 1b. Prompts fill without errors and contain the right ingredients ---
def test_prompts_format():
    args = dict(intent="X", facts="- a", tone="formal")
    assert "X" in BASIC_USER.format(**args)
    adv = ADVANCED_USER.format(**args)
    assert "X" in adv


def test_advanced_has_all_three_techniques():
    # Role-play in system, few-shot + CoT in user
    assert "expert" in ADVANCED_SYSTEM.lower()
    assert "EXAMPLE" in ADVANCED_USER          # few-shot
    assert "do NOT show" in ADVANCED_USER      # silent CoT


# --- 1c. The JSON judge parser is robust to messy model output ---
class FakeJudge:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, system, user, **kw):
        return self.reply


def test_judge_strips_code_fences():
    j = FakeJudge('```json\n{"covered": [true, false]}\n```')
    out = metrics._judge(j, "x")
    assert out["covered"] == [True, False]


def test_judge_ignores_surrounding_prose():
    j = FakeJudge('Sure! Here you go: {"rating": 4} hope that helps')
    assert metrics._judge(j, "x")["rating"] == 4


# --- 1d. Metric math (normalization & coverage fraction) with a fake judge ---
def test_fact_coverage_fraction():
    j = FakeJudge('{"covered": [true, true, false], "notes": "ok"}')
    r = metrics.fact_coverage(j, "email", ["f1", "f2", "f3"])
    assert r["score"] == round(2 / 3, 3)


def test_tone_normalization():
    assert metrics.tone_alignment(FakeJudge('{"rating":5}'), "e", "t")["score"] == 1.0
    assert metrics.tone_alignment(FakeJudge('{"rating":1}'), "e", "t")["score"] == 0.0


def test_conciseness_length_component():
    # long email -> length_score should drop below 1.0
    long_email = "word " * 300
    r = metrics.conciseness_fluency(FakeJudge('{"rating":5}'), long_email)
    assert r["length_score"] < 1.0
    assert r["word_count"] == 300


# --- 1e. Scenarios file is valid and complete ---
def test_scenarios_valid():
    data = json.load(open(config.DATA_FILE, encoding="utf-8"))
    assert len(data) == 10
    ids = [s["id"] for s in data]
    assert len(set(ids)) == 10                       # unique ids
    for s in data:
        assert s["facts"] and s["tone"] and s["intent"]
        assert s["reference_email"].strip()          # every scenario has a reference
    tones = {s["tone"].lower() for s in data}
    assert len(tones) >= 6                            # tones are varied, not all the same
