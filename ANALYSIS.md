# Comparative Analysis (Section 3)

**Experiment:** the same 10 scenarios and 3 metrics were run against two prompting
strategies on an identical generator model (`qwen/qwen3.6-27b`, temperature 0.4) and an
identical judge (`openai/gpt-oss-120b`, reasoning = medium, temperature 0). The only
variable is the prompt, so any difference is attributable to prompt engineering.

## Average scores

| strategy | fact_coverage | tone_alignment | conciseness_fluency | overall |
|----------|--------------:|---------------:|--------------------:|--------:|
| **advanced** | 1.000 | 1.000 | 0.838 | **0.946** |
| basic | 0.983 | 0.975 | 0.610 | 0.856 |
| **delta (adv − basic)** | +0.017 | +0.025 | **+0.228** | **+0.090** |

## Which strategy performed better?

The **advanced** prompt won on every metric, with an overall lead of **+0.090
(0.946 vs. 0.856)**. It was perfect on Fact Coverage (1.000) and Tone Alignment (1.000),
and it won decisively on Conciseness & Fluency (0.838 vs. 0.610). The advanced prompt was
also more *consistent*: 8 of its 10 emails scored ≥0.917, whereas the basic prompt ranged
from 0.775 to 0.958.

## Biggest failure mode of the loser (basic)

The basic prompt's dominant weakness was **verbosity and padding**, captured by the
Conciseness & Fluency metric, where it dropped **0.228** below advanced — by far the
largest gap. Left without a format lock or a "be concise" instruction, the basic prompt
reliably produced:

- **Filler openers** — "I hope this message finds you well", "Hope you're having a great week!"
- **Unrequested placeholder fields** — `[Your Job Title]`, `[Your Phone Number]`,
  `[Your Company Name]`, `[Dana Okafor's Email Address]` — i.e. it *invented* slots that
  were never in the facts.
- **Redundant restatement** — re-explaining the same point across multiple paragraphs.

The clearest example is **S08 (thank a client for renewing)**: the basic email ran long and
padded, scoring **conciseness 0.325 / overall 0.775**, while the advanced email conveyed all
five facts tightly at **conciseness 0.875 / overall 0.958**. A second instance is **S02**
(basic conciseness 0.475 vs. advanced 0.875).

The basic prompt also showed a secondary failure: it occasionally **dropped a specific
fact**. In **S09 (critical bug report)** it scored fact_coverage **0.833** (5 of 6 facts) —
losing a required detail — whereas the advanced prompt's explicit "include EVERY key fact +
silently verify" step held it at 1.000 across all scenarios. It also slipped once on tone
(S05, 0.75) where the advanced prompt held the diplomatic register.

## Production recommendation

**Adopt the advanced prompt for production.** It delivers measurably better emails on every
dimension that matters for this assistant — complete facts, correct tone, and concise,
send-ready copy — and it does so *more reliably*. Critically, it avoids the basic prompt's
habit of emitting placeholder fields and filler, which in a real product would require
human cleanup before sending and erode user trust.

**Cost / latency trade-off:** the advanced prompt is longer (persona + worked example +
planning steps ≈ a few hundred extra input tokens per generation), so it costs marginally
more per call and adds slight latency. Given the large quality gain and the fact that
generation runs on a cheap, fast model, this is an easy trade to justify. At scale, the
example and persona can be cached/condensed to recover most of the overhead.

**Caveats:** results come from a single judge at N=10, so there is judge variance; the
conciseness metric deliberately counterbalances the LLM-judge's known bias toward verbose
text. Averaging multiple runs and (optionally) a second judge would tighten the confidence
interval, but the direction and magnitude of the result are clear and stable.
