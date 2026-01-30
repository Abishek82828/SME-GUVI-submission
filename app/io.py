from __future__ import annotations

import os
from typing import Any, Dict, List

import pandas as pd

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


def read_pdf_text(path: str) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf not installed; cannot read PDFs.")
    reader = PdfReader(path)
    parts: List[str] = []
    for p in reader.pages:
        t = p.extract_text() or ""
        parts.append(t)
    return "\n".join(parts)


def load_table(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    if ext == ".pdf":
        text = read_pdf_text(path)
        return pd.DataFrame({"pdf_text": [text]})
    raise ValueError(f"Unsupported file type: {ext}")


def normalize_cols_soft(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def preview_rows(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    d = df.head(n).copy()
    for c in d.columns:
        d[c] = d[c].astype(str).map(lambda x: x[:160])
    return d.to_dict(orient="records")
