"""Three custom metrics for email quality.

1. fact_coverage      - LLM-judge: fraction of key facts correctly present (0-1)
2. tone_alignment     - LLM-judge: tone match rated 1-5, normalized to 0-1
3. conciseness_fluency- HYBRID: deterministic length score + LLM fluency rating
"""
import json
import re

import config

JUDGE_SYSTEM = (
    "You are a strict, fair evaluator of professional emails. "
    "You respond with VALID JSON ONLY - no prose, no markdown, no code fences."
)


def _parse_json(raw):
    cleaned = re.sub(r"```(?:json)?", "", raw or "").strip()
    # Grab the outermost JSON object even if the model added stray text.
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def _judge(judge_client, prompt):
    """Call the judge at temperature 0 and parse JSON robustly.

    Reasoning models (e.g. gpt-oss) can spend the token budget on hidden
    reasoning and emit little/no content, so we use a generous max_tokens and
    retry once. On total failure we return {} so one bad call can't abort the
    whole run (callers fall back to safe defaults via .get()).
    """
    last_raw = ""
    for _ in range(2):
        last_raw = judge_client.complete(
            JUDGE_SYSTEM, prompt, temperature=0.0, max_tokens=config.JUDGE_MAX_TOKENS
        )
        try:
            return _parse_json(last_raw)
        except (json.JSONDecodeError, ValueError):
            continue
    print(f"    [warn] judge returned unparseable output; using defaults. Raw: {last_raw[:80]!r}")
    return {}


# ---------------- Metric 1: Fact Coverage ----------------
def fact_coverage(judge_client, email, facts):
    facts_str = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(facts))
    prompt = f"""For each KEY FACT below, decide whether it is clearly and accurately
present in the EMAIL. Be strict.

A fact is "covered" (true) ONLY if its full meaning AND every specific detail
(names, numbers, dates, amounts, codes, IDs) appears accurately. Rephrasing the
wording is fine. Mark it NOT covered (false) if the fact is missing, contradicted,
distorted, only vaguely alluded to, partially stated (some specifics dropped), or
replaced by an unfilled placeholder such as [Date], [Amount], or [Order Number].

KEY FACTS:
{facts_str}

EMAIL:
\"\"\"{email}\"\"\"

Return JSON exactly like:
{{"covered": [true, false, ...], "notes": "one short sentence"}}
The "covered" list must have one boolean per fact, in order."""
    result = _judge(judge_client, prompt)
    covered = result.get("covered", [])
    score = (sum(1 for c in covered if c) / len(facts)) if facts else 0.0
    return {"score": round(score, 3), "covered": covered, "notes": result.get("notes", "")}


# ---------------- Metric 2: Tone Alignment ----------------
def tone_alignment(judge_client, email, tone):
    prompt = f"""Rate how well the EMAIL matches the REQUESTED TONE, 1 to 5. Be strict and discriminating.
5 = the requested tone is precisely and consistently matched throughout, with appropriate
    word choice, formality, and warmth.
4 = mostly matched but with a minor slip or a touch of generic phrasing.
3 = partially matched, or generic/neutral corporate tone that doesn't really commit to the request.
2 = noticeably off (e.g. stiff when warmth was asked for, or casual when formal was asked for).
1 = wrong tone.
Do NOT default to 5: reserve it for emails that genuinely nail the requested tone.

REQUESTED TONE: {tone}

EMAIL:
\"\"\"{email}\"\"\"

Return JSON exactly like:
{{"rating": 4, "reason": "one short sentence"}}"""
    result = _judge(judge_client, prompt)
    rating = float(result.get("rating", 1))
    score = (rating - 1) / 4.0          # 1->0.0, 5->1.0
    return {"score": round(score, 3), "rating": rating, "reason": result.get("reason", "")}


# ---------------- Metric 3: Conciseness & Fluency (hybrid) ----------------
def conciseness_fluency(judge_client, email):
    # Deterministic length component
    words = len(email.split())
    if words <= config.LENGTH_FULL_MARKS_MAX:
        length_score = 1.0
    elif words <= config.LENGTH_PARTIAL_MAX:
        length_score = 0.7
    else:
        length_score = 0.4

    # LLM fluency/grammar component
    prompt = f"""Rate the grammar, fluency, and professional tightness of this EMAIL, 1 to 5. Be strict.
5 = flawless and natural, with zero filler, no repetition, and no leftover placeholder fields.
4 = strong, with at most one small lapse.
3 = readable but padded with filler or generic phrasing.
2 = noticeably wordy, repetitive, awkward, or cluttered with unfilled placeholders.
1 = many errors or hard to read.
Deduct points for empty filler ("I hope this email finds you well"), redundancy, padding,
and unfilled placeholder fields like [Insert Tracking Link] or [Your Phone Number].

EMAIL:
\"\"\"{email}\"\"\"

Return JSON exactly like:
{{"rating": 5, "reason": "one short sentence"}}"""
    result = _judge(judge_client, prompt)
    fluency_rating = float(result.get("rating", 1))
    fluency_score = (fluency_rating - 1) / 4.0

    score = round(config.LENGTH_WEIGHT * length_score +
                  config.FLUENCY_WEIGHT * fluency_score, 3)
    return {
        "score": score,
        "word_count": words,
        "length_score": length_score,
        "fluency_rating": fluency_rating,
        "reason": result.get("reason", ""),
    }
