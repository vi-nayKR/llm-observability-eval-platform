import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from config import settings
from src.tracing.collector import trace_collector
from src.evals.evaluator import eval_engine
from src.ci_cd.regression_gate import regression_gate
from src.telemetry.drift_detector import drift_detector

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise LLM Observability, Evaluation & Automated CI/CD Regression Guardrails Platform with OpenTelemetry, DeepEval, and Phoenix Telemetry."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def serve_ui():
    """Serves the OpenAI-standard observability web console."""
    ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "index.html")
    if os.path.exists(ui_path):
        with open(ui_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>LLM Observability & Evaluation Platform</h1>"

@app.get("/v1/traces", tags=["Tracing"])
async def get_traces():
    """Returns all captured OpenTelemetry distributed traces."""
    return trace_collector.get_all_traces()

@app.post("/v1/eval/triad", tags=["Evaluation"])
async def run_triad_evaluation(query: str, context: str, answer: str):
    """Evaluates a single query/context/answer triplet against the Ragas triad."""
    res = await eval_engine.evaluate_triad(query, context, answer)
    return res

@app.get("/v1/gate/status", tags=["CI/CD Gate"])
async def get_gate_status():
    """Returns current CI/CD regression gate report against golden test datasets."""
    sample_answers = {
        "case_001_paged_attention": "PagedAttention partitions KV cache into non-contiguous virtual pages.",
        "case_002_hybrid_search": "RRF combines dense and sparse search rankings.",
        "case_003_qlora_tuning": "QLoRA freezes base model weights and trains low-rank adapters."
    }
    report = await regression_gate.evaluate_candidate("v1.0.0", sample_answers)
    return report

@app.get("/v1/telemetry/drift", tags=["Telemetry"])
async def get_drift_report():
    """Returns real-time operational latency percentiles and cost anomalies."""
    return drift_detector.check_anomalies()

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "default_judge_model": settings.DEFAULT_JUDGE_MODEL
    }
