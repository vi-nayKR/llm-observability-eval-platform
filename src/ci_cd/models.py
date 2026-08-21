from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.evals.models import EvaluationResult

class GateStatus(str, Enum):
    PASSED = "PASSED"
    REGRESSED = "REGRESSED"
    BLOCKED = "BLOCKED"

class GoldenTestCase(BaseModel):
    case_id: str
    query: str
    context: str
    expected_ground_truth: str
    min_faithfulness: float = 0.85
    min_relevance: float = 0.85

class RegressionGateReport(BaseModel):
    suite_id: str
    candidate_version: str
    status: GateStatus
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    avg_faithfulness: float
    avg_relevance: float
    avg_context_precision: float
    results: List[EvaluationResult] = Field(default_factory=list)
    regressed_cases: List[str] = Field(default_factory=list)
    evaluated_at: float
