import time
import uuid
import math
from typing import List, Dict, Any, Optional
from src.telemetry.models import DriftReport, TelemetryAlert, AlertSeverity
from config import settings

class DriftDetector:
    """
    Real-Time Operational Anomaly & Cost Drift Detection Engine.
    Tracks latency distributions, token costs, error rates, and dispatches automated alerts.
    """
    def __init__(
        self,
        max_latency_ms: float = settings.MAX_LATENCY_THRESHOLD_MS,
        hourly_budget_usd: float = settings.MAX_HOURLY_BUDGET_USD
    ):
        self.max_latency_ms = max_latency_ms
        self.hourly_budget_usd = hourly_budget_usd
        self._latencies: List[float] = []
        self._costs: List[float] = []
        self._errors: int = 0
        self._total_requests: int = 0
        self._alerts: List[TelemetryAlert] = []

    def record_execution(self, latency_ms: float, cost_usd: float, is_error: bool = False):
        """Records an execution sample into telemetry buffers."""
        self._total_requests += 1
        self._latencies.append(latency_ms)
        self._costs.append(cost_usd)
        if is_error:
            self._errors += 1

        if len(self._latencies) > 1000:
            self._latencies.pop(0)
            self._costs.pop(0)

    def check_anomalies(self) -> DriftReport:
        """Evaluates operational metrics and fires alerts if thresholds are breached."""
        alerts: List[TelemetryAlert] = []
        
        # 1. Latency Percentiles
        sorted_lat = sorted(self._latencies) if self._latencies else [0.0]
        n = len(sorted_lat)
        p50_idx = int(n * 0.50)
        p95_idx = min(n - 1, max(0, int(math.ceil(n * 0.95)) - 1))
        
        p50 = sorted_lat[p50_idx]
        p95 = sorted_lat[p95_idx]
        max_lat = sorted_lat[-1]

        # Trigger on p95 breach or extreme tail latency outlier
        if p95 > self.max_latency_ms or max_lat > self.max_latency_ms * 1.5:
            val = p95 if p95 > self.max_latency_ms else max_lat
            alerts.append(TelemetryAlert(
                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                alert_type="LATENCY_TAIL_SPIKE",
                severity=AlertSeverity.WARNING if val < self.max_latency_ms * 1.5 else AlertSeverity.CRITICAL,
                message=f"Tail latency ({val}ms) breached maximum threshold of {self.max_latency_ms}ms.",
                metric_value=val,
                threshold=self.max_latency_ms
            ))

        # 2. Cumulative Budget Spend
        total_cost = sum(self._costs)
        if total_cost > self.hourly_budget_usd:
            alerts.append(TelemetryAlert(
                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                alert_type="BUDGET_CAP_BREACH",
                severity=AlertSeverity.CRITICAL,
                message=f"Cumulative spend (${round(total_cost, 4)}) exceeded hourly budget cap (${self.hourly_budget_usd}).",
                metric_value=total_cost,
                threshold=self.hourly_budget_usd
            ))

        # 3. Error Rate
        error_rate = round((self._errors / max(1, self._total_requests)) * 100, 2)
        if error_rate > 2.0:
            alerts.append(TelemetryAlert(
                alert_id=f"alert_{uuid.uuid4().hex[:8]}",
                alert_type="HIGH_ERROR_RATE",
                severity=AlertSeverity.CRITICAL,
                message=f"System error rate is {error_rate}% (>2.0% SLA limit).",
                metric_value=error_rate,
                threshold=2.0
            ))

        status = "CRITICAL" if any(a.severity == AlertSeverity.CRITICAL for a in alerts) else ("DEGRADED" if alerts else "HEALTHY")

        return DriftReport(
            total_requests=self._total_requests,
            error_count=self._errors,
            error_rate_pct=error_rate,
            cumulative_cost_usd=round(total_cost, 4),
            budget_limit_usd=self.hourly_budget_usd,
            latency_p50_ms=round(p50, 2),
            latency_p95_ms=round(p95, 2),
            active_alerts=alerts,
            status=status
        )

    def reset(self):
        self._latencies.clear()
        self._costs.clear()
        self._errors = 0
        self._total_requests = 0
        self._alerts.clear()

drift_detector = DriftDetector()
