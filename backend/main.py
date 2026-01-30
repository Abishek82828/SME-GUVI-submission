from __future__ import annotations

import math
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.db import Base, engine, get_db
from backend.models import Assessment
from backend.schemas import AssessmentCreateResponse, AssessmentGetResponse
from backend.service import run_assessment
from backend.settings import settings
from backend.storage import new_assessment_dir, save_upload

app = FastAPI(title="SME Financial Health Assessment API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def json_sanitize(x):
    if x is None:
        return None
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    if isinstance(x, dict):
        return {k: json_sanitize(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [json_sanitize(v) for v in x]
    return x


def normalize_industry(s: str) -> str:
    return (s or "").strip().lower()


@app.on_event("startup")
def _startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/assessments", response_model=AssessmentCreateResponse)
def create_assessment(
    company: str = Form(...),
    industry: str = Form(...),
    lang: str = Form("en"),
    map_ai: bool = Form(False),
    ai: bool = Form(False),
    gemini_model: str = Form("gemini-2.0-flash"),
    sales: UploadFile | None = File(None),
    expenses: UploadFile | None = File(None),
    ar: UploadFile | None = File(None),
    ap: UploadFile | None = File(None),
    loans: UploadFile | None = File(None),
    inventory: UploadFile | None = File(None),
    tax: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    base_dir = new_assessment_dir()

    paths = {
        "sales": save_upload(base_dir, "sales", sales),
        "expenses": save_upload(base_dir, "expenses", expenses),
        "ar": save_upload(base_dir, "ar", ar),
        "ap": save_upload(base_dir, "ap", ap),
        "loans": save_upload(base_dir, "loans", loans),
        "inventory": save_upload(base_dir, "inventory", inventory),
        "tax": save_upload(base_dir, "tax", tax),
    }

    company_clean = (company or "").strip()
    if not company_clean:
        raise HTTPException(status_code=422, detail="company is required")

    industry_clean = normalize_industry(industry)
    if not industry_clean:
        raise HTTPException(status_code=422, detail="industry is required")

    lang_clean = (lang or "en").strip() or "en"

    try:
        out = run_assessment(
            company=company_clean,
            industry=industry_clean,
            lang=lang_clean,
            map_ai=map_ai,
            ai=ai,
            gemini_model=gemini_model,
            files=paths,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Assessment failed: {e}")

    raw_result = out.get("result_json")
    safe_result = json_sanitize(raw_result)

    row = Assessment(
        company=company_clean,
        industry=industry_clean,
        lang=lang_clean,
        result_json=safe_result,
        report_md=out.get("report_md", "") or "",
        ai_md=out.get("ai_md", "") or "",
        storage_path=base_dir,
    )

    try:
        db.add(row)
        db.commit()
        db.refresh(row)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")

    return AssessmentCreateResponse(
        id=row.id,
        company=row.company,
        industry=row.industry,
        lang=row.lang,
        created_at=row.created_at,
        result_json=row.result_json,
    )


@app.get("/api/assessments/{assessment_id}", response_model=AssessmentGetResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    row = db.get(Assessment, assessment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    return AssessmentGetResponse(
        id=row.id,
        company=row.company,
        industry=row.industry,
        lang=row.lang,
        created_at=row.created_at,
        result_json=row.result_json,
        report_md=row.report_md,
        ai_md=row.ai_md or "",
        storage_path=row.storage_path or "",
    )


@app.get("/api/assessments/{assessment_id}/report")
def get_report_md(assessment_id: str, db: Session = Depends(get_db)):
    row = db.get(Assessment, assessment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": row.id, "report_md": row.report_md}


@app.get("/api/assessments/{assessment_id}/ai")
def get_ai_md(assessment_id: str, db: Session = Depends(get_db)):
    row = db.get(Assessment, assessment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": row.id, "ai_md": row.ai_md or ""}
