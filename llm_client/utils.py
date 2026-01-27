import re
import json


def extract_json(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("Empty response from LLM")

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in LLM output:\n{text}")

    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in LLM output: {e}") from e