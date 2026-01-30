from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from app.cleaning import clean_amount, safe_div, to_dt
from app.mapping import compute_expense_super_category


def build_monthly_sales(sales: Optional[pd.DataFrame]) -> pd.DataFrame:
    if sales is None or sales.empty or "date" not in sales.columns or "amount" not in sales.columns:
        return pd.DataFrame(columns=["month", "revenue"])
    s = sales.copy()
    s["date"] = s["date"].apply(to_dt)
    s["amount"] = s["amount"].apply(clean_amount)
    s = s.dropna(subset=["date", "amount"])
    s["month"] = s["date"].dt.to_period("M").astype(str)
    m = s.groupby("month", as_index=False)["amount"].sum().rename(columns={"amount": "revenue"})
    return m.sort_values("month")


def build_monthly_expenses(expenses: Optional[pd.DataFrame]) -> pd.DataFrame:
    if expenses is None or expenses.empty or "date" not in expenses.columns or "amount" not in expenses.columns:
        return pd.DataFrame(columns=["month", "expense"])
    e = expenses.copy()
    e["date"] = e["date"].apply(to_dt)
    e["amount"] = e["amount"].apply(clean_amount)
    e = e.dropna(subset=["date", "amount"])
    e["month"] = e["date"].dt.to_period("M").astype(str)
    m = e.groupby("month", as_index=False)["amount"].sum().rename(columns={"amount": "expense"})
    return m.sort_values("month")


def ar_aging(ar: Optional[pd.DataFrame], as_of: Optional[pd.Timestamp] = None) -> Dict[str, Any]:
    if ar is None or ar.empty or "outstanding" not in ar.columns:
        return {"total_outstanding": 0.0, "buckets": {}}

    a = ar.copy()
    if "invoice_date" in a.columns:
        a["invoice_date"] = a["invoice_date"].apply(to_dt)
    else:
        a["invoice_date"] = pd.NaT

    if "due_date" in a.columns:
        a["due_date"] = a["due_date"].apply(to_dt)
    else:
        a["due_date"] = pd.NaT

    a["outstanding"] = a["outstanding"].apply(clean_amount)
    a = a.dropna(subset=["outstanding"])

    if as_of is None:
        as_of = pd.Timestamp.today().normalize()

    base = a["due_date"].fillna(a["invoice_date"])
    days = (as_of - base).dt.days.fillna(0)
    a["age"] = days

    buckets = {
        "0-30": float(a.loc[(a["age"] <= 30), "outstanding"].sum()),
        "31-60": float(a.loc[(a["age"] > 30) & (a["age"] <= 60), "outstanding"].sum()),
        "61-90": float(a.loc[(a["age"] > 60) & (a["age"] <= 90), "outstanding"].sum()),
        "90+": float(a.loc[(a["age"] > 90), "outstanding"].sum()),
    }
    return {"total_outstanding": float(a["outstanding"].sum()), "buckets": buckets}


def ap_aging(ap: Optional[pd.DataFrame], as_of: Optional[pd.Timestamp] = None) -> Dict[str, Any]:
    if ap is None or ap.empty or "outstanding" not in ap.columns:
        return {"total_outstanding": 0.0, "buckets": {}}

    p = ap.copy()
    if "bill_date" in p.columns:
        p["bill_date"] = p["bill_date"].apply(to_dt)
    else:
        p["bill_date"] = pd.NaT

    if "due_date" in p.columns:
        p["due_date"] = p["due_date"].apply(to_dt)
    else:
        p["due_date"] = pd.NaT

    p["outstanding"] = p["outstanding"].apply(clean_amount)
    p = p.dropna(subset=["outstanding"])

    if as_of is None:
        as_of = pd.Timestamp.today().normalize()

    base = p["due_date"].fillna(p["bill_date"])
    days = (as_of - base).dt.days.fillna(0)
    p["age"] = days

    buckets = {
        "0-30": float(p.loc[(p["age"] <= 30), "outstanding"].sum()),
        "31-60": float(p.loc[(p["age"] > 30) & (p["age"] <= 60), "outstanding"].sum()),
        "61-90": float(p.loc[(p["age"] > 60) & (p["age"] <= 90), "outstanding"].sum()),
        "90+": float(p.loc[(p["age"] > 90), "outstanding"].sum()),
    }
    return {"total_outstanding": float(p["outstanding"].sum()), "buckets": buckets}


def loan_summary(loans: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if loans is None or loans.empty:
        return {"total_principal": 0.0, "total_emi": 0.0, "avg_interest_rate": np.nan}

    l = loans.copy()
    for c in ["principal", "emi", "interest_rate"]:
        if c in l.columns:
            l[c] = l[c].apply(clean_amount)

    total_principal = float(l["principal"].sum()) if "principal" in l.columns else 0.0
    total_emi = float(l["emi"].sum()) if "emi" in l.columns else 0.0
    avg_rate = float(l["interest_rate"].mean()) if "interest_rate" in l.columns else np.nan
    return {"total_principal": total_principal, "total_emi": total_emi, "avg_interest_rate": avg_rate}


def inventory_summary(inv: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if inv is None or inv.empty:
        return {"inventory_value": 0.0, "sku_count": 0, "stale_items": 0}

    i = inv.copy()
    if "value" in i.columns:
        i["value"] = i["value"].apply(clean_amount)
    if "last_movement_date" in i.columns:
        i["last_movement_date"] = i["last_movement_date"].apply(to_dt)

    inventory_value = float(i["value"].sum()) if "value" in i.columns else 0.0
    sku_count = int(i["sku"].nunique()) if "sku" in i.columns else len(i)

    stale_items = 0
    if "last_movement_date" in i.columns:
        cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=90)
        stale_items = int((i["last_movement_date"] < cutoff).sum())

    return {"inventory_value": inventory_value, "sku_count": sku_count, "stale_items": stale_items}


def tax_summary(tax: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if tax is None or tax.empty or "amount" not in tax.columns:
        return {"available": False}

    t = tax.copy()
    if "date" in t.columns:
        t["date"] = t["date"].apply(to_dt)
    t["amount"] = t["amount"].apply(clean_amount)
    t = t.dropna(subset=["amount"])

    if "period" not in t.columns or t["period"].isna().all():
        if "date" in t.columns:
            t["period"] = t["date"].dt.to_period("M").astype(str)
        else:
            t["period"] = "UNKNOWN"

    if "type" not in t.columns:
        t["type"] = "tax"
    if "status" not in t.columns:
        t["status"] = "unknown"

    t["type"] = t["type"].astype(str).str.lower()
    t["status"] = t["status"].astype(str).str.lower()

    total = float(t["amount"].sum())
    by_type = (
        t.groupby("type", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(10)
    )
    by_period = t.groupby("period", as_index=False)["amount"].sum().sort_values("period")

    pending = (
        float(t.loc[t["status"].isin(["pending", "unpaid", "due"]), "amount"].sum())
        if "status" in t.columns
        else 0.0
    )
    late_cnt = int(t["status"].isin(["late", "overdue"]).sum()) if "status" in t.columns else 0

    return {
        "available": True,
        "total_tax_amount": total,
        "pending_amount": pending,
        "late_items": late_cnt,
        "tax_by_type_top": by_type.to_dict(orient="records"),
        "tax_by_period": by_period.to_dict(orient="records"),
    }


def expense_breakdown(expenses: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if expenses is None or expenses.empty or "amount" not in expenses.columns:
        return {"available": False}

    e = expenses.copy()
    e["amount"] = e["amount"].apply(clean_amount)
    e = e.dropna(subset=["amount"])

    if "category" not in e.columns:
        e["category"] = "other"
    e["category"] = e["category"].astype(str)

    e["super_category"] = e["category"].map(compute_expense_super_category)

    by_cat = (
        e.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(12)
    )
    by_super = (
        e.groupby("super_category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )

    return {
        "available": True,
        "by_category_top": by_cat.to_dict(orient="records"),
        "by_super_category": by_super.to_dict(orient="records"),
    }


def revenue_breakdown(sales: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if sales is None or sales.empty or "amount" not in sales.columns:
        return {"available": False}

    s = sales.copy()
    s["amount"] = s["amount"].apply(clean_amount)
    s = s.dropna(subset=["amount"])

    out: Dict[str, Any] = {"available": True}

    if "customer" in s.columns:
        by_cust = (
            s.groupby("customer", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
            .head(12)
        )
        out["by_customer_top"] = by_cust.to_dict(orient="records")

    if "status" in s.columns:
        by_status = (
            s.groupby("status", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        out["by_status"] = by_status.to_dict(orient="records")

    if "product" in s.columns:
        by_prod = (
            s.groupby("product", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
            .head(12)
        )
        out["by_product_top"] = by_prod.to_dict(orient="records")

    if "channel" in s.columns:
        by_ch = (
            s.groupby("channel", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        out["by_channel"] = by_ch.to_dict(orient="records")

    return out


def compute_kpis(
    monthly_sales: pd.DataFrame,
    monthly_exp: pd.DataFrame,
    ar_info: Dict[str, Any],
    ap_info: Dict[str, Any],
    loan_info: Dict[str, Any],
    inv_info: Dict[str, Any],
) -> Dict[str, Any]:
    ms = monthly_sales.set_index("month") if not monthly_sales.empty else pd.DataFrame(index=[])
    me = monthly_exp.set_index("month") if not monthly_exp.empty else pd.DataFrame(index=[])

    idx = sorted(set(ms.index.tolist()) | set(me.index.tolist()))
    df = pd.DataFrame(index=idx)

    df["revenue"] = ms["revenue"] if "revenue" in ms.columns else 0.0
    df["expense"] = me["expense"] if "expense" in me.columns else 0.0
    df = df.fillna(0.0)
    df["operating_profit"] = df["revenue"] - df["expense"]

    last3 = df.tail(3) if len(df) >= 3 else df
    last6 = df.tail(6) if len(df) >= 6 else df

    revenue = float(df["revenue"].sum())
    expense = float(df["expense"].sum())
    op_profit = float(df["operating_profit"].sum())

    avg_rev_m = float(last3["revenue"].mean()) if len(last3) else 0.0
    avg_exp_m = float(last3["expense"].mean()) if len(last3) else 0.0

    op_margin = safe_div(op_profit, revenue)

    rev_vol = float(last6["revenue"].std()) if len(last6) >= 2 else 0.0
    rev_vol_norm = safe_div(rev_vol, float(last6["revenue"].mean()) if len(last6) else 1.0)
    rev_vol_norm = float(rev_vol_norm) if pd.notna(rev_vol_norm) else 0.0

    runway_months = np.nan
    if avg_exp_m and avg_exp_m > 0:
        net_wc = float(ar_info.get("total_outstanding", 0.0)) - float(ap_info.get("total_outstanding", 0.0))
        runway_months = safe_div(max(net_wc, 0.0), avg_exp_m)

    dso = np.nan
    if avg_rev_m and avg_rev_m > 0:
        dso = safe_div(float(ar_info.get("total_outstanding", 0.0)), avg_rev_m) * 30.0

    dpo = np.nan
    if avg_exp_m and avg_exp_m > 0:
        dpo = safe_div(float(ap_info.get("total_outstanding", 0.0)), avg_exp_m) * 30.0

    emi = float(loan_info.get("total_emi", 0.0) or 0.0)
    emi_to_rev = safe_div(emi, avg_rev_m) if avg_rev_m else np.nan

    return {
        "timeline_months": df.reset_index().rename(columns={"index": "month"}).to_dict(orient="records"),
        "total_revenue": revenue,
        "total_expense": expense,
        "total_operating_profit": op_profit,
        "avg_monthly_revenue_last3": avg_rev_m,
        "avg_monthly_expense_last3": avg_exp_m,
        "operating_margin": op_margin,
        "revenue_volatility": rev_vol_norm,
        "ar": ar_info,
        "ap": ap_info,
        "inventory": inv_info,
        "loans": loan_info,
        "dso_days": dso,
        "dpo_days": dpo,
        "runway_months_proxy": runway_months,
        "emi_to_monthly_revenue": emi_to_rev,
    }


def simple_forecast(monthly_sales: pd.DataFrame, monthly_exp: pd.DataFrame, horizon: int = 6) -> Dict[str, Any]:
    if monthly_sales.empty and monthly_exp.empty:
        return {"horizon_months": horizon, "forecast": [], "method": "insufficient_data"}

    def prep(mdf: pd.DataFrame, col: str) -> pd.Series:
        if mdf.empty:
            return pd.Series(dtype=float)
        s = mdf.set_index("month")[col].astype(float)
        s.index = pd.PeriodIndex(s.index, freq="M")
        return s.sort_index()

    s_rev = prep(monthly_sales, "revenue")
    s_exp = prep(monthly_exp, "expense")

    last_period = None
    if len(s_rev):
        last_period = s_rev.index.max()
    if len(s_exp):
        last_period = max(last_period, s_exp.index.max()) if last_period else s_exp.index.max()

    if last_period is None:
        return {"horizon_months": horizon, "forecast": [], "method": "insufficient_data"}

    def trend(series: pd.Series) -> tuple[float, float]:
        if len(series) < 3:
            mu = float(series.mean()) if len(series) else 0.0
            return mu, 0.0
        tail = series.tail(6)
        y = tail.values
        x = np.arange(len(y))
        slope = float(np.polyfit(x, y, 1)[0])
        base = float(y[-1])
        return base, slope

    rev_base, rev_slope = trend(s_rev)
    exp_base, exp_slope = trend(s_exp)

    fc = []
    for i in range(1, horizon + 1):
        p = (last_period + i).strftime("%Y-%m")
        rev = max(0.0, rev_base + rev_slope * i)
        exp = max(0.0, exp_base + exp_slope * i)
        fc.append(
            {
                "month": p,
                "forecast_revenue": float(rev),
                "forecast_expense": float(exp),
                "forecast_operating_profit": float(rev - exp),
            }
        )

    return {"horizon_months": horizon, "forecast": fc, "method": "mean+trend_last6"}
