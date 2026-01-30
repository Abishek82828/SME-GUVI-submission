from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import numpy as np
import pandas as pd

from app.types import Outputs


def generate_report_md(company: str, industry: str, output: Outputs) -> str:
    kpis: Dict[str, Any] = output.kpis or {}
    scores = output.scores
    risks = output.risks or []
    recs = output.recommendations or []
    bench = output.benchmarks or {}
    fc = output.forecast or {}
    br = output.breakdowns or {}

    def pct(x: Any) -> str:
        if x is None or pd.isna(x):
            return "NA"
        return f"{float(x) * 100:.1f}%"

    lines = []
    lines.append(f"# Investor-Ready Financial Snapshot — {company}")
    lines.append(f"**Industry:** {industry}  \n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## 1) Scores")
    lines.append(f"- **Financial Health Score:** {scores.health_score}/100 ({scores.rating})")
    lines.append(f"- **Credit Readiness Score:** {scores.credit_readiness_score}/100")
    lines.append(f"- **Risk Score (higher = riskier):** {scores.risk_score}/100")
    lines.append("")
    lines.append("## 2) Key KPIs")
    lines.append(f"- **Total Revenue:** {float(kpis.get('total_revenue', 0.0)):,.2f}")
    lines.append(f"- **Total Expense:** {float(kpis.get('total_expense', 0.0)):,.2f}")
    lines.append(f"- **Operating Profit:** {float(kpis.get('total_operating_profit', 0.0)):,.2f}")
    lines.append(f"- **Operating Margin:** {pct(kpis.get('operating_margin', np.nan))}")

    if pd.notna(kpis.get("dso_days", np.nan)):
        lines.append(f"- **DSO (days):** {float(kpis.get('dso_days')):.0f}")
    else:
        lines.append("- **DSO (days):** NA")

    if pd.notna(kpis.get("dpo_days", np.nan)):
        lines.append(f"- **DPO (days):** {float(kpis.get('dpo_days')):.0f}")
    else:
        lines.append("- **DPO (days):** NA")

    if pd.notna(kpis.get("revenue_volatility", np.nan)):
        lines.append(f"- **Revenue Volatility (normalized):** {float(kpis.get('revenue_volatility')):.2f}")
    else:
        lines.append("- **Revenue Volatility:** NA")

    lines.append("")
    lines.append("## 3) Revenue & Expense Breakdown")

    rev = br.get("revenue", {}) or {}
    exp = br.get("expenses", {}) or {}

    if rev.get("available"):
        if "by_customer_top" in rev:
            lines.append("### Top Customers by Revenue")
            for r in (rev.get("by_customer_top") or [])[:10]:
                lines.append(f"- {r.get('customer','NA')}: {float(r.get('amount',0.0)):,.2f}")
        if "by_channel" in rev:
            lines.append("### Revenue by Channel")
            for r in (rev.get("by_channel") or [])[:10]:
                lines.append(f"- {r.get('channel','NA')}: {float(r.get('amount',0.0)):,.2f}")
        if "by_status" in rev:
            lines.append("### Revenue by Status")
            for r in (rev.get("by_status") or [])[:10]:
                lines.append(f"- {r.get('status','NA')}: {float(r.get('amount',0.0)):,.2f}")
        if "by_product_top" in rev:
            lines.append("### Top Products by Revenue")
            for r in (rev.get("by_product_top") or [])[:10]:
                lines.append(f"- {r.get('product','NA')}: {float(r.get('amount',0.0)):,.2f}")
    else:
        lines.append("- Revenue breakdown not available (missing optional columns like customer/status/channel).")

    if exp.get("available"):
        lines.append("### Top Expense Categories")
        for r in (exp.get("by_category_top") or [])[:10]:
            lines.append(f"- {r.get('category','NA')}: {float(r.get('amount',0.0)):,.2f}")
        lines.append("### Expense Super Categories")
        for r in (exp.get("by_super_category") or [])[:10]:
            lines.append(f"- {r.get('super_category','NA')}: {float(r.get('amount',0.0)):,.2f}")
    else:
        lines.append("- Expense breakdown not available (missing category).")

    lines.append("")
    lines.append("## 4) Risks & Red Flags")
    for r in risks[:8]:
        lines.append(f"- **[{r.get('severity','NA')}] {r.get('type','NA')}:** {r.get('signal','')} — {r.get('why','')}")

    lines.append("")
    lines.append("## 5) Rule-Based Recommendations (minimal)")
    for i, rec in enumerate(recs[:5], 1):
        lines.append(f"### {i}. {rec.get('title','')}")
        lines.append(f"- **Why:** {rec.get('why','')}")
        lines.append("- **Actions:**")
        for a in rec.get("actions", []) or []:
            lines.append(f"  - {a}")
        lines.append(f"- **Impact:** {rec.get('impact_estimate','')}")
        lines.append("")

    lines.append("## 6) Benchmarking")
    if bench.get("available"):
        b = bench.get("benchmarks", {}) or {}
        y = bench.get("your", {}) or {}
        lines.append(f"- Industry median operating margin: **{float(b.get('op_margin',0.0))*100:.1f}%** | Yours: **{pct(y.get('operating_margin', np.nan))}**")

        if pd.notna(y.get("dso_days", np.nan)):
            lines.append(f"- Industry DSO: **{int(b.get('dso',0))} days** | Yours: **{float(y.get('dso_days')):.0f} days**")
        else:
            lines.append("- Industry DSO: NA")

        if pd.notna(y.get("dpo_days", np.nan)):
            lines.append(f"- Industry DPO: **{int(b.get('dpo',0))} days** | Yours: **{float(y.get('dpo_days')):.0f} days**")
        else:
            lines.append("- Industry DPO: NA")
    else:
        lines.append("- Benchmarking not available for this industry label in MVP.")

    lines.append("")
    lines.append("## 7) Forecast (simple)")
    lines.append(f"- Method: `{fc.get('method')}` | Horizon: {fc.get('horizon_months')} months")
    for row in (fc.get("forecast", []) or [])[:6]:
        lines.append(
            f"  - {row.get('month')}: Rev {float(row.get('forecast_revenue',0.0)):.2f}, "
            f"Exp {float(row.get('forecast_expense',0.0)):.2f}, "
            f"OpProfit {float(row.get('forecast_operating_profit',0.0)):.2f}"
        )

    lines.append("")
    lines.append("## 8) Tax & Compliance (if provided)")
    tax = br.get("tax", {}) or {}
    if tax.get("available"):
        lines.append(f"- Total tax amount: {float(tax.get('total_tax_amount',0.0)):,.2f}")
        lines.append(f"- Pending amount: {float(tax.get('pending_amount',0.0)):,.2f}")
        lines.append(f"- Late items: {int(tax.get('late_items',0) or 0)}")
        lines.append("### Tax by Type (top)")
        for r in (tax.get("tax_by_type_top", []) or [])[:10]:
            lines.append(f"- {r.get('type','tax')}: {float(r.get('amount',0.0)):,.2f}")
    else:
        lines.append("- Tax data not provided or not mapped.")

    lines.append("")
    lines.append("## Notes")
    for n in (output.notes or []):
        lines.append(f"- {n}")
    lines.append("")
    return "\n".join(lines)
