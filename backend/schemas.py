from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel


class AssessmentCreateResponse(BaseModel):
    id: str
    company: str
    industry: str
    lang: str
    created_at: datetime
    result_json: Dict[str, Any]


class AssessmentGetResponse(BaseModel):
    id: str
    company: str
    industry: str
    lang: str
    created_at: datetime
    result_json: Dict[str, Any]
    report_md: str
    ai_md: str = ""
    storage_path: str = ""
