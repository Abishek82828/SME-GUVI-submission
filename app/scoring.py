from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from app.cleaning import clip01


def score_system(kpis: Dict) -> "Scores":
    from app.types import Scores

    op_margin = kpis.get("operating_margin", np.nan)
    vol = kpis.get("revenue_volatility", np.nan)
    dso = kpis.get("dso_days", np.nan)
    emi_ratio = kpis.get("emi_to_monthly_revenue", np.nan)

    s_profit = clip01((op_margin - 0.02) / 0.18) if pd.notna(op_margin) else 0.0
    s_vol = clip01(1 - (vol / 0.6)) if pd.notna(vol) else 0.5
    s_dso = clip01(1 - (dso / 120)) if pd.notna(dso) else 0.5
    s_debt = clip01(1 - (emi_ratio / 0.35)) if pd.notna(emi_ratio) else 0.7

    health = (0.40 * s_profit + 0.30 * s_vol + 0.30 * s_dso) * 100
    credit = (0.45 * (health / 100) + 0.35 * s_debt + 0.20 * s_dso) * 100
    risk = (1 - (0.35 * s_profit + 0.30 * s_vol + 0.20 * s_dso + 0.15 * s_debt)) * 100

    def rating_from(h: float) -> str:
        if h >= 80:
            return "Strong"
        if h >= 65:
            return "Good"
        if h >= 50:
            return "Watch"
        return "High Risk"

    return Scores(
        health_score=int(round(health)),
        credit_readiness_score=int(round(credit)),
        risk_score=int(round(risk)),
        rating=rating_from(float(health)),
    )


def risk_engine(kpis: Dict) -> List[Dict]:
    risks: List[Dict] = []
    ar = kpis.get("ar", {}) or {}
    ap = kpis.get("ap", {}) or {}
    inv = kpis.get("inventory", {}) or {}
    vol = kpis.get("revenue_volatility", np.nan)
    op_margin = kpis.get("operating_margin", np.nan)
    dso = kpis.get("dso_days", np.nan)
    emi_ratio = kpis.get("emi_to_monthly_revenue", np.nan)

    if pd.notna(op_margin) and op_margin < 0.02:
        risks.append(
            {
                "type": "Profitability",
                "severity": "High",
                "signal": f"Operating margin is low ({op_margin:.1%}).",
                "why": "Low margin reduces buffer for shocks.",
            }
        )

    if pd.notna(vol) and vol > 0.35:
        risks.append(
            {
                "type": "Revenue Stability",
                "severity": "Medium",
                "signal": f"Revenue volatility is high ({vol:.2f}).",
                "why": "High variance increases cashflow uncertainty.",
            }
        )

    if pd.notna(dso) and dso > 60:
        risks.append(
            {
                "type": "Receivables",
                "severity": "High" if float(dso) > 90 else "Medium",
                "signal": f"DSO is high (~{dso:.0f} days).",
                "why": "Slow collections strain working capital.",
            }
        )

    if pd.notna(emi_ratio) and emi_ratio > 0.25:
        risks.append(
            {
                "type": "Debt Burden",
                "severity": "High",
                "signal": f"EMI burden is high ({emi_ratio:.1%} of monthly revenue).",
                "why": "High fixed outflow raises default risk.",
            }
        )

    ar90 = (ar.get("buckets", {}) or {}).get("90+", 0.0)
    if ar.get("total_outstanding", 0.0) > 0 and ar90 / max(float(ar.get("total_outstanding", 0.0)), 1e-9) > 0.25:
        risks.append(
            {
                "type": "Receivables Aging",
                "severity": "High",
                "signal": "Large share of AR is 90+ days.",
                "why": "Older receivables have lower recovery probability.",
            }
        )

    stale = int(inv.get("stale_items", 0) or 0)
    if stale > 0:
        risks.append(
            {
                "type": "Inventory",
                "severity": "Medium",
                "signal": f"{stale} items appear stale (no movement in 90+ days).",
                "why": "Dead stock locks cash and may require discounting.",
            }
        )

    ap90 = (ap.get("buckets", {}) or {}).get("90+", 0.0)
    if ap.get("total_outstanding", 0.0) > 0 and ap90 / max(float(ap.get("total_outstanding", 0.0)), 1e-9) > 0.20:
        risks.append(
            {
                "type": "Payables Aging",
                "severity": "Medium",
                "signal": "Notable AP is 90+ days overdue.",
                "why": "Vendor pressure may disrupt supply.",
            }
        )

    if not risks:
        risks.append(
            {
                "type": "General",
                "severity": "Low",
                "signal": "No major red flags detected from uploaded data.",
                "why": "Keep monitoring monthly.",
            }
        )

    return risks[:10]


def recommend_engine(kpis: Dict, scores: "Scores", industry: str) -> List[Dict]:
    recs: List[Dict] = []
    dso = kpis.get("dso_days", np.nan)
    op_margin = kpis.get("operating_margin", np.nan)
    emi_ratio = kpis.get("emi_to_monthly_revenue", np.nan)
    inv = kpis.get("inventory", {}) or {}
    stale = int(inv.get("stale_items", 0) or 0)

    if pd.notna(dso) and dso > 60:
        recs.append(
            {
                "title": "Improve collections (reduce DSO)",
                "why": f"DSO is high (~{dso:.0f} days), which traps cash in receivables.",
                "actions": [
                    "Send payment reminders before due date (3/7/14-day cycle)",
                    "Set a stop-credit rule for customers overdue >60 days",
                    "Ask new customers for partial advance payment",
                ],
                "impact_estimate": "Lower DSO improves cashflow and reduces risk.",
            }
        )

    if pd.notna(op_margin) and op_margin < 0.08:
        recs.append(
            {
                "title": "Cut controllable costs (raise operating margin)",
                "why": f"Operating margin is {op_margin:.1%}, leaving limited buffer.",
                "actions": [
                    "Remove unused subscriptions/tools",
                    "Negotiate rent/vendor pricing",
                    "Set monthly budgets per expense category",
                ],
                "impact_estimate": "A 3–5% cost reduction usually improves margin directly.",
            }
        )

    if pd.notna(emi_ratio) and emi_ratio > 0.20:
        recs.append(
            {
                "title": "Reduce fixed EMI pressure",
                "why": f"EMI is {emi_ratio:.1%} of monthly revenue, increasing default risk during low-sales months.",
                "actions": [
                    "Prioritize prepayment of highest-interest debt first",
                    "Avoid new fixed-cost borrowing until cashflow stabilizes",
                    "Consider restructuring tenure to reduce EMI (compare total interest)",
                ],
                "impact_estimate": "Lower EMI ratio increases credit readiness.",
            }
        )

    if stale > 0:
        recs.append(
            {
                "title": "Clear stale inventory",
                "why": f"{stale} items have no movement for 90+ days, locking cash.",
                "actions": [
                    "Run targeted discounts on dead stock",
                    "Stop reordering slow SKUs until stock normalizes",
                    "Track weekly aging inventory report",
                ],
                "impact_estimate": "Releasing dead stock improves working capital quickly.",
            }
        )

    if not recs:
        recs.append(
            {
                "title": "Maintain monthly finance discipline",
                "why": "No strong red flags triggered; keep tracking consistently.",
                "actions": [
                    "Close accounts monthly by day 5",
                    "Track weekly revenue, AR 30+, and cash buffer",
                ],
                "impact_estimate": "Consistency prevents surprises and improves decision-making.",
            }
        )

    return recs[:5]
