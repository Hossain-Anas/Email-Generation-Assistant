"""Central configuration: models, strategies, metric weights, paths."""
import os
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "scenarios.json"
RESULTS_DIR = ROOT / "results"

# --- Models -------------------------------------------------------------
# Use whatever you have access to. Generation = fast/cheap; judging = stronger.
GENERATOR_PROVIDER = os.getenv("GEN_PROVIDER", "groq")
GENERATOR_MODEL    = os.getenv("GEN_MODEL", "qwen/qwen3.6-27b")

JUDGE_PROVIDER = os.getenv("JUDGE_PROVIDER", "groq")
JUDGE_MODEL    = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")

# Groq reasoning effort per role: generator stays fast/cheap, judge reasons more.
GEN_REASONING_EFFORT   = os.getenv("GEN_REASONING_EFFORT", "none")
JUDGE_REASONING_EFFORT = os.getenv("JUDGE_REASONING_EFFORT", "medium")

# Judge token budget. Reasoning models count hidden reasoning against this, so
# keep it generous to ensure the JSON answer still fits after reasoning.
JUDGE_MAX_TOKENS = int(os.getenv("JUDGE_MAX_TOKENS", "4096"))

# --- Experiment axes ----------------------------------------------------
STRATEGIES = ["basic", "advanced"]   # the two "models" we compare

# --- Generation params --------------------------------------------------
GEN_TEMPERATURE = 0.4     # identical across strategies so prompt is the only variable
GEN_MAX_TOKENS  = 800

# --- Metric weighting for the blended Conciseness & Fluency score --------
LENGTH_WEIGHT  = 0.5
FLUENCY_WEIGHT = 0.5
# Word-count thresholds for the deterministic length component.
# Tightened to reward genuinely concise emails and penalize padded/verbose ones.
LENGTH_FULL_MARKS_MAX = 130   # <= this -> 1.0
LENGTH_PARTIAL_MAX    = 190   # <= this -> 0.7, else 0.4
