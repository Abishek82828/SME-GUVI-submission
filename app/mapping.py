from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from app.io import preview_rows

try:
    from google import genai
except Exception:
    genai = None


CANON: Dict[str, Dict[str, List[str]]] = {
    "sales": {
        "required": ["date", "amount"],
        "optional": ["invoice_id", "customer", "status", "product", "channel", "payment_mode", "qty"],
    },
    "expenses": {
        "required": ["date", "amount"],
        "optional": ["vendor", "category", "description", "tax", "gst", "tds", "bill_id", "payment_mode"],
    },
    "ar": {
        "required": ["outstanding"],
        "optional": ["customer", "invoice_date", "due_date", "invoice_id", "status"],
    },
    "ap": {
        "required": ["outstanding"],
        "optional": ["vendor", "bill_date", "due_date", "bill_id", "status"],
    },
    "loans": {
        "required": [],
        "optional": ["lender", "principal", "emi", "interest_rate", "start_date", "end_date", "type"],
    },
    "inventory": {
        "required": [],
        "optional": ["sku", "qty", "value", "last_movement_date", "category", "location"],
    },
    "tax": {
        "required": ["amount"],
        "optional": ["date", "period", "type", "status", "reference", "notes"],
    },
}


EXPENSE_KEYWORDS: Dict[str, List[str]] = {
    "payroll": ["salary", "wages", "payroll", "staff", "employee"],
    "rent": ["rent", "lease"],
    "utilities": ["electric", "water", "internet", "phone", "utility"],
    "marketing": ["ads", "advert", "marketing", "facebook", "google", "instagram"],
    "logistics": ["shipping", "courier", "delivery", "fuel", "transport"],
    "software": ["saas", "subscription", "license", "cloud", "hosting"],
    "interest": ["interest", "emi", "loan"],
}


def compute_expense_super_category(category: str) -> str:
    if not isinstance(category, str):
        return "other"
    s = category.lower()
    for k, kws in EXPENSE_KEYWORDS.items():
        if any(w in s for w in kws):
            return k
    return "other"


def extract_json_from_text(t: str) -> Optional[Dict[str, Any]]:
    if not t:
        return None
    s = t.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    m = re.search(r"\{.*\}", s, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def fuzzy_pick(colnames: List[str], keywords: List[str]) -> Optional[str]:
    low = [(c, c.lower()) for c in colnames]
    for k in keywords:
        kk = str(k).lower()
        for c, cl in low:
            if kk in cl:
                return c
    return None


def fallback_mapping(kind: str, df: pd.DataFrame) -> Dict[str, Any]:
    cols = list(df.columns)
    req = CANON[kind]["required"]
    opt = CANON[kind]["optional"]
    targets = req + opt

    hints: Dict[str, List[str]] = {
        "date": ["date", "txn", "transaction", "bill date", "invoice date", "posted", "created", "time"],
        "amount": ["amount", "total", "value", "net", "gross", "paid", "credit", "debit", "amt"],
        "invoice_id": ["invoice", "inv", "bill no", "bill#", "ref", "reference", "doc"],
        "customer": ["customer", "client", "buyer", "party"],
        "vendor": ["vendor", "supplier", "seller", "party"],
        "category": ["category", "head", "account", "expense type", "type"],
        "description": ["description", "narration", "remarks", "note", "details"],
        "status": ["status", "state", "paid", "unpaid", "open", "closed"],
        "outstanding": ["outstanding", "due", "balance", "pending", "receivable", "payable"],
        "due_date": ["due", "due date"],
        "bill_date": ["bill date", "date"],
        "principal": ["principal", "loan amount", "sanction", "amount"],
        "emi": ["emi", "installment", "monthly", "repayment"],
        "interest_rate": ["interest", "rate", "roi"],
        "start_date": ["start", "disburse", "from"],
        "end_date": ["end", "maturity", "to"],
        "sku": ["sku", "item", "product code", "item code"],
        "qty": ["qty", "quantity", "stock", "units"],
        "last_movement_date": ["movement", "last", "updated", "last sale", "last purchase"],
        "period": ["period", "month", "fy", "quarter"],
        "type": ["type", "tax type", "gst", "tds", "tcs", "itc"],
        "tax": ["tax", "gst", "tds", "tcs"],
        "gst": ["gst"],
        "tds": ["tds"],
    }

    mapping: Dict[str, str] = {}
    for t in targets:
        if t in hints:
            pick = fuzzy_pick(cols, hints[t])
            if pick:
                mapping[t] = pick

    return {"mappings": mapping, "confidence": 0.25, "notes": "fallback_fuzzy"}


def gemini_map_columns(kind: str, df: pd.DataFrame, model: str) -> Dict[str, Any]:
    if genai is None or not os.environ.get("GEMINI_API_KEY"):
        return fallback_mapping(kind, df)

    cols = list(df.columns)
    sample = preview_rows(df, 5)
    canon = CANON[kind]

    prompt = f"""
You are a data-mapping assistant for SME finance analytics.
Task: Map unknown column names into a canonical schema for dataset kind = "{kind}".

Return ONLY valid JSON in this exact format:
{{
  "mappings": {{ "canonical_field": "actual_column_name", ... }},
  "confidence": 0.0,
  "notes": "short"
}}

Rules:
- Use the sample rows to infer meanings.
- Only map when you are reasonably sure.
- If multiple columns could match, choose the best and mention ambiguity in notes.
- Do not invent columns that are not present.
- Keep confidence between 0 and 1.

Canonical fields:
Required: {canon["required"]}
Optional: {canon["optional"]}

Actual columns:
{cols}

First 5 rows sample:
{json.dumps(sample, ensure_ascii=False, indent=2)}
""".strip()

    try:
        client = genai.Client()
        resp = client.models.generate_content(model=model, contents=prompt)
        data = extract_json_from_text((resp.text or "").strip())
        if not data or "mappings" not in data:
            return fallback_mapping(kind, df)

        m = data.get("mappings") or {}
        m2: Dict[str, str] = {}
        for k, v in m.items():
            if isinstance(k, str) and isinstance(v, str) and v in cols:
                m2[k] = v

        data["mappings"] = m2
        if "confidence" not in data:
            data["confidence"] = 0.5
        if "notes" not in data:
            data["notes"] = ""
        return data
    except Exception:
        return fallback_mapping(kind, df)


def apply_mapping(df: pd.DataFrame, mapping: Dict[str, Any]) -> pd.DataFrame:
    m = (mapping or {}).get("mappings") or {}
    out = pd.DataFrame()
    for canon_field, actual_col in m.items():
        if actual_col in df.columns:
            out[canon_field] = df[actual_col]
    out["_raw_columns"] = [", ".join([str(c) for c in df.columns])] * max(len(out), 1)
    return out
