from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.ai_gemini import gemini_generate_md
from app.insights import benchmark_compare, build_ai_payload
from app.io import load_table, normalize_cols_soft, preview_rows
from app.kpis import (
    ap_aging,
    ar_aging,
    build_monthly_expenses,
    build_monthly_sales,
    compute_kpis,
    expense_breakdown,
    inventory_summary,
    loan_summary,
    revenue_breakdown,
    simple_forecast,
    tax_summary,
)
from app.mapping import apply_mapping, fallback_mapping, gemini_map_columns
from app.report import generate_report_md
from app.scoring import recommend_engine, risk_engine, score_system
from app.types import Outputs


def main() -> None:
    ap = argparse.ArgumentParser(
        description="SME Financial Health Assessment (Uploads-only, flexible columns + AI mapping)"
    )
    ap.add_argument("--company", required=True)
    ap.add_argument("--industry", required=True, help="manufacturing|retail|agriculture|services|logistics|ecommerce")
    ap.add_argument("--sales", default=None)
    ap.add_argument("--expenses", default=None)
    ap.add_argument("--ar", default=None)
    ap.add_argument("--ap", dest="apfile", default=None)
    ap.add_argument("--loans", default=None)
    ap.add_argument("--inventory", default=None)
    ap.add_argument("--tax", default=None)
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--map_ai", action="store_true", help="Use Gemini to map columns from any headers")
    ap.add_argument("--ai", action="store_true", help="Generate Gemini AI suggestions markdown")
    ap.add_argument("--lang", default="en", help="en or hi")
    ap.add_argument("--gemini_model", default="gemini-2.0-flash")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    notes: List[str] = []
    mappings: Dict[str, Any] = {}

    def load_and_map(path: Optional[str], kind: str) -> Optional[pd.DataFrame]:
        if not path:
            return None

        df = load_table(path)

        if "pdf_text" in df.columns:
            notes.append(f"{kind}: PDF loaded as text blob; structured parsing not implemented.")
            mappings[kind] = {"mappings": {}, "confidence": 0.0, "notes": "pdf_text_only", "source_file": path}
            return df

        df = normalize_cols_soft(df)

        if args.map_ai:
            m = gemini_map_columns(kind, df, model=args.gemini_model)
        else:
            m = fallback_mapping(kind, df)

        mappings[kind] = {
            "source_file": path,
            "original_columns": list(df.columns),
            "preview_5_rows": preview_rows(df, 5),
            "mapping_result": m,
        }

        dfm = apply_mapping(df, m)
        if dfm.empty:
            notes.append(f"{kind}: could not map columns; provide clearer headers or use --map_ai with GEMINI_API_KEY.")
        return dfm

    sales = load_and_map(args.sales, "sales")
    expenses = load_and_map(args.expenses, "expenses")
    ar = load_and_map(args.ar, "ar")
    apdf = load_and_map(args.apfile, "ap")
    loans = load_and_map(args.loans, "loans")
    inv = load_and_map(args.inventory, "inventory")
    tax = load_and_map(args.tax, "tax")

    if sales is None or sales.empty:
        notes.append("Sales missing/empty: revenue analytics limited.")
    if expenses is None or expenses.empty:
        notes.append("Expenses missing/empty: cost analytics limited.")

    ms = build_monthly_sales(sales) if sales is not None else pd.DataFrame(columns=["month", "revenue"])
    me = build_monthly_expenses(expenses) if expenses is not None else pd.DataFrame(columns=["month", "expense"])

    ar_info = ar_aging(ar) if ar is not None else {"total_outstanding": 0.0, "buckets": {}}
    ap_info = ap_aging(apdf) if apdf is not None else {"total_outstanding": 0.0, "buckets": {}}
    loan_info = loan_summary(loans) if loans is not None else {"total_principal": 0.0, "total_emi": 0.0, "avg_interest_rate": np.nan}
    inv_info = inventory_summary(inv) if inv is not None else {"inventory_value": 0.0, "sku_count": 0, "stale_items": 0}

    kpis = compute_kpis(ms, me, ar_info, ap_info, loan_info, inv_info)
    scores = score_system(kpis)
    risks = risk_engine(kpis)
    bench = benchmark_compare(kpis, args.industry)
    fc = simple_forecast(ms, me, horizon=6)
    recs = recommend_engine(kpis, scores, args.industry)

    breakdowns = {
        "revenue": revenue_breakdown(sales) if sales is not None else {"available": False},
        "expenses": expense_breakdown(expenses) if expenses is not None else {"available": False},
        "tax": tax_summary(tax) if tax is not None else {"available": False},
    }

    output = Outputs(
        kpis=kpis,
        scores=scores,
        risks=risks,
        recommendations=recs,
        benchmarks=bench,
        forecast=fc,
        notes=notes,
        mappings=mappings,
        breakdowns=breakdowns,
    )

    out_json = os.path.join(args.outdir, "assessment.json")
    out_md = os.path.join(args.outdir, "investor_report.md")
    out_ai = os.path.join(args.outdir, f"ai_suggestions_{args.lang}.md")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(
            {"company": args.company, "industry": args.industry, **asdict(output)},
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    report_md = generate_report_md(args.company, args.industry, output)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(report_md + "\n")

    if args.ai:
        payload = build_ai_payload(args.company, args.industry, output)
        ai_md = gemini_generate_md(payload, model=args.gemini_model, lang=args.lang)
        with open(out_ai, "w", encoding="utf-8") as f:
            f.write(ai_md)
        print(f"✅ Done.\n- JSON: {out_json}\n- Report: {out_md}\n- AI: {out_ai}")
    else:
        print(f"✅ Done.\n- JSON: {out_json}\n- Report: {out_md}")


if __name__ == "__main__":
    main()
