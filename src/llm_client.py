"""Provider-agnostic LLM wrapper. The rest of the code only sees .complete()."""
import os
import time
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self, provider="anthropic", model=None, max_retries=3,
                 reasoning_effort="none"):
        self.provider = provider
        self.max_retries = max_retries
        self.reasoning_effort = reasoning_effort  # groq-only; "none"/"low"/"medium"/"high"

        if provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            self.model = model or "claude-haiku-4-5-20251001"
        elif provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            self.model = model or "gpt-4o-mini"
        elif provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=os.environ["GROQ_API_KEY"])
            self.model = model or "qwen/qwen3.6-27b"
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def complete(self, system, user, temperature=0.4, max_tokens=800):
        """Return the model's text response as a plain string, with retries."""
        last_err = None
        for attempt in range(self.max_retries):
            try:
                if self.provider == "anthropic":
                    resp = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system,
                        messages=[{"role": "user", "content": user}],
                    )
                    return resp.content[0].text.strip()
                elif self.provider == "groq":
                    resp = self.client.chat.completions.create(
                        model=self.model,
                        temperature=temperature,
                        max_completion_tokens=max_tokens,
                        top_p=0.95,
                        reasoning_effort=self.reasoning_effort,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    )
                    return (resp.choices[0].message.content or "").strip()
                else:  # openai
                    resp = self.client.chat.completions.create(
                        model=self.model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    )
                    return resp.choices[0].message.content.strip()
            except Exception as e:                      # noqa: BLE001
                last_err = e
                time.sleep(2 ** attempt)                # 1s, 2s, 4s backoff
        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_err}")
