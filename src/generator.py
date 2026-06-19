"""Turns (intent, facts, tone) into an email using the chosen strategy."""
from src.prompts import BASIC_SYSTEM, BASIC_USER, ADVANCED_SYSTEM, ADVANCED_USER


def _format_facts(facts):
    return "\n".join(f"- {f}" for f in facts)


def generate_email(client, intent, facts, tone, strategy="advanced",
                   temperature=0.4, max_tokens=800):
    facts_str = _format_facts(facts)

    if strategy == "advanced":
        system = ADVANCED_SYSTEM
        user = ADVANCED_USER.format(intent=intent, facts=facts_str, tone=tone)
    elif strategy == "basic":
        system = BASIC_SYSTEM
        user = BASIC_USER.format(intent=intent, facts=facts_str, tone=tone)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return client.complete(system, user, temperature=temperature, max_tokens=max_tokens)
