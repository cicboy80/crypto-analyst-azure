import json


def extract_json(raw: str) -> dict:
    """Parse a JSON object from LLM output, tolerating surrounding prose."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON found in model output.")
        return json.loads(raw[start : end + 1])
