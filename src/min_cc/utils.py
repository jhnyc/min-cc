import os
from typing import Any, Dict, Union

import requests

from .constants import SYSTEM_PROMPT, TRIM_TOOL_CALL_ARGS


def get_model_context_length(model_id: str) -> Union[int, str]:
    """
    Retrieves the context length for a specific model from the OpenRouter API.
    """
    url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for model in data.get("data", []):
            if model.get("id") == model_id:
                return model.get("context_length", 0)

        return f"Model '{model_id}' not found."
    except Exception as e:
        return f"An error occurred: {e}"


def trim_tool_call_args(args: Dict[str, Any]):
    return {
        k: (
            v[:TRIM_TOOL_CALL_ARGS] + "..."
            if isinstance(v, str) and len(v) > TRIM_TOOL_CALL_ARGS
            else v
        )
        for k, v in args.items()
    }


def format_number(n: int) -> str:
    """Formats large numbers with k or M suffixes."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0", "")
    if n >= 1_000:
        return f"{n / 1_000:.1f}k".replace(".0", "")
    return str(n)


def get_full_system_prompt() -> str:
    full_prompt = SYSTEM_PROMPT
    if os.path.exists("Min-CC.md"):
        try:
            with open("Min-CC.md", "r") as f:
                content = f.read()
                content = content.replace("Min-CC.md\n", "").strip()
                full_prompt += f"\n\n<codebase_context>\n{content}</codebase_context>"
        except Exception:
            pass
    return full_prompt
