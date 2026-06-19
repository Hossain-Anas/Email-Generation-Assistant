# Email Generation Assistant

An LLM-powered assistant that turns **Intent + Key Facts + Tone** into a polished,
professional email — then **objectively evaluates** that output with three custom
metrics and **compares two prompting strategies** (a basic baseline vs. an advanced
engineered prompt) on the same 10 scenarios.

> **Repository:** https://github.com/Hossain-Anas/Email-Generation-Assistant

The headline result: the **advanced** prompt beats the **basic** baseline
**0.946 vs. 0.856** overall, driven mostly by conciseness (advanced avoids the
verbose, placeholder-laden padding the basic prompt produces).

---

## 1. What this project does

| Pillar | Implementation |
|--------|----------------|
| **The Assistant** | `Intent + Key Facts + Tone -> email`, using an **advanced prompt** that combines Role-Playing + silent Chain-of-Thought + Few-Shot (`src/prompts.py`). |
| **Evaluation** | **3 custom metrics** (`src/metrics.py`) run over **10 scenarios** with **human reference emails** (`data/scenarios.json`), producing a structured CSV + JSON. |
| **Comparison** | The same 10 scenarios + metrics run against a **second strategy** (basic prompt); the winner, failure mode, and recommendation are reported in `ANALYSIS.md`. |

---

## 2. Setup

Requires **Python 3.10+** and a **Groq API key** (free at <https://console.groq.com>).

```bash
git clone https://github.com/Hossain-Anas/Email-Generation-Assistant.git
cd Email-Generation-Assistant

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env                  # then open .env and add your GROQ_API_KEY
```

Your `.env` should contain:

```
GROQ_API_KEY=gsk_...
```

By default the project uses the **Groq** API:

| Role | Model | Reasoning |
|------|-------|-----------|
| Generator | `qwen/qwen3.6-27b` | `none` (fast / cheap, high volume) |
| Judge | `openai/gpt-oss-120b` | `medium` (more reasoning for fairer scoring) |

---

## 3. Run

```bash
python run_evaluation.py             # full: 10 scenarios x 2 strategies (40 generations + 60 judgements)
python run_evaluation.py --limit 2   # quick smoke test (cheap)
```

Outputs land in `results/`:

- `evaluation_results.csv` — flat, one row per (scenario x strategy) with all metric scores.
- `evaluation_results.json` — the same data **plus** the full generated email and the judge's per-metric notes (audit trail).
- `comparison_report.md` — auto-generated averages, per-metric deltas, and the winner.

Generate the final report document:

```bash
python generate_report.py            # writes Final_Report.docx
```

---

## 4. Testing

```bash
pytest tests/test_unit.py -q          # Layer 1: offline, no API key, instant
python tests/calibrate.py             # Layer 2: prove metrics separate good vs. bad (needs API key)
python run_evaluation.py --limit 2    # Layer 3: integration smoke test
python run_evaluation.py              # Layer 4: full run + analysis
```

---

## 5. The advanced prompting technique

The **advanced** prompt (`src/prompts.py`) layers three documented techniques:

1. **Role-Playing** — the system prompt casts the model as *"an expert executive
   communications assistant with 15 years of experience"* that never invents facts
   and always includes every provided fact. Raises the floor on tone and professionalism.
2. **Chain-of-Thought (silent)** — the user prompt gives a numbered internal process
   (infer recipient → draft subject → plan fact placement → choose structure → verify
   all facts present) and explicitly instructs the model **not** to show this reasoning.
   This boosts fact coverage and structure without polluting the email.
3. **Few-Shot** — one complete worked example (Intent + Facts + Tone → ideal
   Subject/body/sign-off) teaches the output format and natural fact-weaving.

A **format lock** ("Output EXACTLY a `Subject:` line, then the body") prevents reasoning
from leaking into the output.

The **basic** baseline is deliberately the opposite — a one-line "write a professional
email" with no persona, example, or planning. The gap between them is the experiment.

---

## 6. The 3 custom metrics

All three are normalized to **0–1** and averaged into an `overall` score. The LLM judge
runs at **temperature 0** with **JSON-only** output, and parsing is hardened against
code-fences, stray prose, and reasoning-model token exhaustion.

| # | Metric | Maps to | Type | Logic |
|---|--------|---------|------|-------|
| 1 | **Fact Coverage** | Key Facts | LLM-judge | Judge returns a boolean per fact (covered only if every specific detail — names, numbers, dates, amounts, codes — is accurately present). Score = `covered / total`. Reference-free. |
| 2 | **Tone Alignment** | Tone | LLM-judge | Judge rates the tone match 1–5 against a strict rubric; normalized `(rating-1)/4`. |
| 3 | **Conciseness & Fluency** | Quality | **Hybrid** | `0.5 × length_score + 0.5 × fluency`. `length_score` is deterministic from word count (≤130 → 1.0, ≤190 → 0.7, else 0.4); `fluency` is an LLM 1–5 rating that penalizes filler, repetition, and unfilled placeholders. |

The hybrid metric is a deliberate counterbalance to the well-known LLM-judge bias toward
verbose answers.

---

## 7. The 10 scenarios

`data/scenarios.json` spans the tone and difficulty space — formal ↔ casual, few ↔ many
facts, easy ↔ tricky (apology, declining a vendor, urgent bug report, etc.). Each scenario
carries 5–6 fact-dense items with droppable specifics and a tight **human reference email**
used for spot-checking and as few-shot inspiration.

---

## 8. Results summary

| strategy | fact_coverage | tone_alignment | conciseness_fluency | overall |
|----------|--------------:|---------------:|--------------------:|--------:|
| **advanced** | 1.000 | 1.000 | 0.838 | **0.946** |
| basic | 0.983 | 0.975 | 0.610 | 0.856 |

Full write-up (winner, failure mode, production recommendation) in **`ANALYSIS.md`**.

---

## 9. Project layout

```
Email-Generation-Assistant/
├── README.md
├── ANALYSIS.md              # 1-page comparative analysis (Section 3)
├── requirements.txt
├── .env.example
├── .gitignore
├── config.py               # models, strategies, metric weights, paths
├── run_evaluation.py       # runner -> CSV + JSON + comparison_report.md
├── generate_report.py      # builds Final_Report.docx
├── data/
│   └── scenarios.json      # 10 scenarios + human reference emails
├── src/
│   ├── llm_client.py       # provider-agnostic wrapper (Groq / Anthropic / OpenAI) + retries
│   ├── prompts.py          # BASIC vs. ADVANCED prompt templates
│   ├── generator.py        # (intent, facts, tone) -> email
│   ├── metrics.py          # the 3 custom metrics + robust JSON judge
│   └── evaluator.py        # one scenario -> scored record
├── tests/
│   ├── test_unit.py        # offline unit tests
│   └── calibrate.py        # metric calibration (great vs. bad email)
└── results/                # generated outputs (CSV / JSON / comparison)
```

---

## 10. Swapping models / providers

The harness is provider-agnostic — the rest of the code only sees `client.complete()`.
Switch via env vars or CLI flags:

```bash
# Different Groq models
python run_evaluation.py --judge-model llama-3.3-70b-versatile

# Cross-vendor comparison (requires the relevant API key in .env)
python run_evaluation.py --gen-provider openai --gen-model gpt-4o-mini
```

Env vars: `GEN_PROVIDER`, `GEN_MODEL`, `JUDGE_PROVIDER`, `JUDGE_MODEL`,
`GEN_REASONING_EFFORT`, `JUDGE_REASONING_EFFORT`, `JUDGE_MAX_TOKENS`.

---

## 11. Limitations

- **LLM-judge variance** — a single judge at N=10 carries noise; the conciseness metric
  guards against verbosity bias, but averaging multiple runs would tighten confidence.
- **Generation temperature 0.4** — emails differ run-to-run, though the *strategy ranking*
  is stable.
- **Single provider by default** — the primary axis is prompt strategy, not vendor; the
  harness supports cross-model comparison but it is not the headline experiment.
