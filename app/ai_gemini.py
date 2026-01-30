from __future__ import annotations

import os
from typing import Any, Dict

from app.insights import build_ai_prompt

try:
    from google import genai
except Exception:
    genai = None


def gemini_generate_md(payload: Dict[str, Any], model: str, lang: str) -> str:
    if genai is None:
        return "# AI Insights & Next Steps\n\nGemini SDK not installed. Install with: `pip install -U google-genai`.\n"
    if not os.environ.get("GEMINI_API_KEY"):
        return "# AI Insights & Next Steps\n\nGEMINI_API_KEY is not set. Set it as an environment variable, then re-run with `--ai`.\n"

    client = genai.Client()
    prompt = build_ai_prompt(payload, lang)
    resp = client.models.generate_content(model=model, contents=prompt)
    text = (resp.text or "").strip()

    if not text:
        return "# AI Insights & Next Steps\n\nNo text returned from model.\n"

    if not text.lstrip().startswith("#"):
        text = "# AI Insights & Next Steps\n\n" + text

    return text + "\n"
