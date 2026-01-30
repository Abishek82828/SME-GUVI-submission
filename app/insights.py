from __future__ import annotations

import json
from typing import Any, Dict

import numpy as np
import pandas as pd


BENCH: Dict[str, Dict[str, float]] = {
    "retail": {"gross_margin": 0.20, "op_margin": 0.06, "dso": 15, "dpo": 30},
    "manufacturing": {"gross_margin": 0.28, "op_margin": 0.10, "dso": 45, "dpo": 60},
    "services": {"gross_margin": 0.45, "op_margin": 0.18, "dso": 30, "dpo": 30},
    "logistics": {"gross_margin": 0.18, "op_margin": 0.05, "dso": 45, "dpo": 45},
    "agriculture": {"gross_margin": 0.22, "op_margin": 0.08, "dso": 30, "dpo": 45},
    "ecommerce": {"gross_margin": 0.25, "op_margin": 0.07, "dso": 7, "dpo": 30},
}


def benchmark_compare(kpis: Dict[str, Any], industry: str) -> Dict[str, Any]:
    ind = str(industry).lower()
    b = BENCH.get(ind)
    if not b:
        return {"industry": industry, "available": False}
    return {
        "industry": industry,
        "available": True,
        "benchmarks": b,
        "your": {
            "operating_margin": kpis.get("operating_margin", np.nan),
            "dso_days": kpis.get("dso_days", np.nan),
            "dpo_days": kpis.get("dpo_days", np.nan),
        },
        "gaps": {
            "op_margin_gap": (kpis.get("operating_margin", np.nan) - b["op_margin"])
            if pd.notna(kpis.get("operating_margin", np.nan))
            else np.nan,
            "dso_gap_days": (kpis.get("dso_days", np.nan) - b["dso"])
            if pd.notna(kpis.get("dso_days", np.nan))
            else np.nan,
            "dpo_gap_days": (kpis.get("dpo_days", np.nan) - b["dpo"])
            if pd.notna(kpis.get("dpo_days", np.nan))
            else np.nan,
        },
    }


def build_ai_payload(company: str, industry: str, output: Any) -> Dict[str, Any]:
    from dataclasses import asdict

    return {
        "company": company,
        "industry": industry,
        "scores": asdict(output.scores),
        "kpis": output.kpis,
        "risks": output.risks,
        "rule_recommendations": output.recommendations,
        "benchmarks": output.benchmarks,
        "forecast": output.forecast,
        "breakdowns": output.breakdowns,
        "mappings": output.mappings,
        "notes": output.notes,
    }


def build_ai_prompt(payload: Dict[str, Any], lang: str) -> str:
    if str(lang).lower() == "hi":
        lang_rule = "Write in simple Hindi (easy words). Use INR formatting where relevant."
    else:
        lang_rule = "Write in simple English. Use INR formatting where relevant."

    return f"""
You are an SME finance assistant. Use only the JSON data below.
Do not invent numbers. If any metric looks unrealistic/extreme, call it out and suggest what data to verify.
Avoid repeating the rule_recommendations unless you are improving them.

{lang_rule}

Output Markdown with exactly:

# AI Insights & Next Steps
## 1) Executive Summary (5 bullets)
## 2) What the Data Means (interpret KPIs, breakdowns)
## 3) Deeper Risks (beyond rule-based) (max 7)
## 4) 30–60 Day Plan (prioritized checklist)
## 5) Cost Optimization (use expense breakdown if available)
## 6) Working Capital Optimization (AR/AP/Inventory)
## 7) Revenue Strategy (use revenue breakdown if available)
## 8) Tax & Compliance Notes (if tax data present)
## 9) Data Quality Checks (max 12)
## 10) What to Track Weekly (5 KPIs)

JSON:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()
