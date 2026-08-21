import pytest
from src.telemetry.drift_detector import DriftDetector
from src.telemetry.models import AlertSeverity

def test_normal_traffic_baseline():
    detector = DriftDetector(max_latency_ms=2500.0, hourly_budget_usd=50.0)
    for _ in range(50):
        detector.record_execution(latency_ms=250.0, cost_usd=0.001, is_error=False)

    report = detector.check_anomalies()
    assert report.status == "HEALTHY"
    assert len(report.active_alerts) == 0
    assert report.error_rate_pct == 0.0

def test_latency_spike_detection():
    detector = DriftDetector(max_latency_ms=2000.0, hourly_budget_usd=50.0)
    for _ in range(20):
        detector.record_execution(latency_ms=300.0, cost_usd=0.001)
    
    # Inject tail latency spike (3,500ms)
    detector.record_execution(latency_ms=3500.0, cost_usd=0.005)

    report = detector.check_anomalies()
    assert report.status in ["DEGRADED", "CRITICAL"]
    assert any(a.alert_type == "LATENCY_TAIL_SPIKE" for a in report.active_alerts)

def test_budget_cap_breach():
    detector = DriftDetector(max_latency_ms=5000.0, hourly_budget_usd=10.0)
    # Inject large token cost
    detector.record_execution(latency_ms=200.0, cost_usd=12.50)

    report = detector.check_anomalies()
    assert report.status == "CRITICAL"
    assert any(a.alert_type == "BUDGET_CAP_BREACH" for a in report.active_alerts)
