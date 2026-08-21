# Phase 4: Real-Time Anomaly & Cost Drift Detector

---

## 1. Overview & Objective

In high-throughput production LLM deployments, infrastructure teams face sudden, unpredictable operational anomalies:
1. **Unbounded Prompt Expansion & Token Cost Drift:** Buggy user inputs or recursive multi-agent loops that consume millions of tokens in minutes, blowing through cloud budgets.
2. **Tail Latency Spikes ($p95, p99$):** Cold-start GPU bottlenecks, model queue congestion, or slow downstream vector database lookups.
3. **Elevated Upstream Error Rates:** Model provider rate-limiting (HTTP 429) or tool timeout failures.

**Phase 4 Goal:** Implement a real-time **Telemetry Anomaly & Cost Drift Detector** that:
- Maintains dynamic sliding-window statistics for latency percentiles and token spend velocity.
- Triggers automated alarms with severity levels (`WARNING`, `CRITICAL`) when latency deviates past normal distribution thresholds.
- Enforces real-time hourly budget caps, preventing cloud bill shock.

---

## 2. Anomaly Detection & Drift Mathematics

```

 REAL-TIME DRIFT & ANOMALY DETECTION 

 Incoming Trace Stream [ Sliding Window Telemetry Aggregator ] 
 
 
 
 [ Latency Outliers ] [ Budget Consumption ] [ Error Rate Spikes ] 
 (Z-Score > 3.0 or (Cumulative Spend vs (Errors > 2.0% of 
 Latency > Threshold) Hourly Budget Limit) Total Requests) 
 
 
 
 [ Automated P1/P2 Alert Dispatcher ] 

```

### A. Latency Z-Score Outlier Formulation
Given a sliding window of historical latencies with mean $\mu$ and standard deviation $\sigma$:
$$Z = \frac{x - \mu}{\sigma}$$
An execution is flagged as an outlier anomaly if $Z > 3.0$ or if $x > \text{Threshold}_{\text{max}}$.

---

## 3. Step-by-Step Code Walkthrough

### Step 1: Telemetry Data Models (`src/telemetry/models.py`)
- `AlertSeverity`: Enum (`INFO`, `WARNING`, `CRITICAL`).
- `TelemetryAlert`: Alert payload with `alert_type`, `severity`, `message`, `metric_value`, and `threshold`.
- `DriftReport`: Real-time operational report with cumulative token costs, p50/p95 latency, and active alerts.

### Step 2: Anomaly Detection Engine (`src/telemetry/drift_detector.py`)
- **`record_execution(latency_ms, cost_usd, is_error)`:** Ingests trace metrics into memory ring buffers.
- **`check_anomalies()`:** Evaluates cost caps, latency percentiles, and error rate thresholds.

---

## 4. How to Run & Verify Phase 4

### Command:
```bash
./.venv/bin/pytest tests/test_drift_detector.py
```

### Expected Output:
```text
============================== 3 passed in 0.04s ==============================
```

### What the Tests Verify:
1. `test_normal_traffic_baseline`: Confirms stable traffic produces zero false-positive alerts.
2. `test_latency_spike_detection`: Injects a $3,500\text{ms}$ delay and asserts a `WARNING`/`CRITICAL` alert fires.
3. `test_budget_cap_breach`: Validates that exceeding the hourly USD spend threshold triggers a `CRITICAL` budget alarm.

---

## 5. Technical Questions & Architectural Explanations

### Q: Why use sliding percentile windows instead of simple fixed threshold alerts for LLM latency?
> **Answer:** LLM generation latency naturally varies depending on output token lengths (a 10-token completion takes ~50ms, while a 500-token completion takes ~600ms). Evaluating sliding percentile windows ($p50, p95$) and per-token generation speeds captures true underlying system regressions without generating false alerts on legitimately long responses.
