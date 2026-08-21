import asyncio
import time
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tracing.collector import trace_collector
from src.tracing.models import SpanKind
from src.evals.evaluator import eval_engine
from src.telemetry.drift_detector import drift_detector

async def process_single_trace(worker_id: int) -> Dict[str, Any]:
 start_total = time.perf_counter()

 # 1. Start Trace & Nested Spans
 trace = trace_collector.create_trace(f"benchmark_pipeline_{worker_id}")
 
 async with trace_collector.span(trace.trace_id, "retriever_node", SpanKind.RETRIEVER) as s_ret:
 s_ret.outputs = {"chunks": 3}

 async with trace_collector.span(trace.trace_id, "llm_generate", SpanKind.LLM) as s_llm:
 trace_collector.record_llm_tokens(s_llm, prompt_tokens=120, completion_tokens=180)
 s_llm.outputs = {"answer": "vLLM PagedAttention partitions KV-cache to eliminate VRAM fragmentation."}

 # 2. Evaluate Triad
 query = "How does vLLM PagedAttention manage KV-cache memory?"
 context = "vLLM's PagedAttention partitions Key-Value memory into non-contiguous physical virtual pages, reducing VRAM fragmentation to under 4%."
 answer = "vLLM PagedAttention partitions KV-cache to eliminate VRAM fragmentation."
 
 eval_result = await eval_engine.evaluate_triad(query, context, answer)

 # 3. Record Drift Telemetry
 elapsed_ms = (time.perf_counter() - start_total) * 1000.0
 drift_detector.record_execution(
 latency_ms=elapsed_ms,
 cost_usd=trace.total_tokens.estimated_cost_usd,
 is_error=not eval_result.passed_all
 )

 return {
 "worker_id": worker_id,
 "elapsed_ms": round(elapsed_ms, 2),
 "passed": eval_result.passed_all,
 "overall_score": eval_result.overall_score,
 "total_spans": len(trace.spans)
 }

async def run_benchmark(concurrency: int = 50):
 print(f" Launching Observability & Evaluation Benchmark with {concurrency} concurrent workers...")
 
 start_bench = time.perf_counter()
 tasks = [process_single_trace(i) for i in range(1, concurrency + 1)]
 results = await asyncio.gather(*tasks)
 total_time_sec = time.perf_counter() - start_bench

 latencies = sorted([r["elapsed_ms"] for r in results])
 passed_count = sum(1 for r in results if r["passed"])
 total_spans = sum(r["total_spans"] for r in results)

 def p(arr, percentile):
 if not arr: return 0.0
 idx = int(len(arr) * percentile)
 return arr[min(idx, len(arr) - 1)]

 tps = round(len(results) / max(0.001, total_time_sec), 1)

 print("\n" + "=" * 70)
 print(" LLM OBSERVABILITY & EVALUATION — BENCHMARK RESULTS")
 print("=" * 70)
 print(f"Total Traces Processed: {len(results)}")
 print(f"Total Spans Ingested: {total_spans} spans")
 print(f"Concurrent Workers: {concurrency}")
 print(f"Triad Evaluation Pass Rate: {passed_count} / {len(results)} ({round(passed_count/len(results)*100, 1)}%)")
 print(f"Throughput (Traces/sec): {tps} traces/second")
 print("-" * 70)
 print("LATENCY BREAKDOWN (Per-Request Observability):")
 print(f" • Total Telemetry (p50): {p(latencies, 0.50):.2f} ms")
 print(f" • Total Telemetry (p95): {p(latencies, 0.95):.2f} ms")
 print(f" • Total Telemetry (p99): {p(latencies, 0.99):.2f} ms")
 print("=" * 70 + "\n")

if __name__ == "__main__":
 asyncio.run(run_benchmark())
