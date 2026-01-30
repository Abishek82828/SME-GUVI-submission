from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Scores:
    health_score: int
    credit_readiness_score: int
    risk_score: int
    rating: str


@dataclass
class Outputs:
    kpis: Dict[str, Any]
    scores: Scores
    risks: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    benchmarks: Dict[str, Any]
    forecast: Dict[str, Any]
    notes: List[str]
    mappings: Dict[str, Any]
    breakdowns: Dict[str, Any]
