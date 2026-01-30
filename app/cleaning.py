from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from dateutil.parser import parse as dtparse


def to_dt(x: Any) -> pd.Timestamp:
    if pd.isna(x):
        return pd.NaT
    if isinstance(x, (datetime, np.datetime64, pd.Timestamp)):
        return pd.to_datetime(x, errors="coerce")
    try:
        return pd.to_datetime(dtparse(str(x), dayfirst=True), errors="coerce")
    except Exception:
        return pd.to_datetime(x, errors="coerce")


def clean_amount(x: Any) -> float:
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s == "":
        return np.nan
    s = s.replace(",", "")
    s = re.sub(r"[^\d\.\-\(\)]", "", s)
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except Exception:
        return np.nan


def safe_div(a: Any, b: Any) -> float:
    if b is None or b == 0 or pd.isna(b):
        return np.nan
    return float(a) / float(b)


def clip01(x: Any) -> float:
    if pd.isna(x):
        return np.nan
    return max(0.0, min(1.0, float(x)))
