import time
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class TelemetryAlert(BaseModel):
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    metric_value: float
    threshold: float
    timestamp: float = Field(default_factory=time.time)

class DriftReport(BaseModel):
    total_requests: int
    error_count: int
    error_rate_pct: float
    cumulative_cost_usd: float
    budget_limit_usd: float
    latency_p50_ms: float
    latency_p95_ms: float
    active_alerts: List[TelemetryAlert] = Field(default_factory=list)
    status: str = "HEALTHY"
