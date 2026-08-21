from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MetricType(str, Enum):
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCE = "answer_relevance"
    CONTEXT_PRECISION = "context_precision"
    TOXICITY = "toxicity"

class MetricScore(BaseModel):
    metric: MetricType
    score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    threshold: float
    reason: str

class EvaluationResult(BaseModel):
    eval_id: str
    query: str
    answer: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    passed_all: bool
    metrics: List[MetricScore] = Field(default_factory=list)
    latency_ms: float
    evaluated_at: float
