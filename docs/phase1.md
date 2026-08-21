# Phase 1: OpenTelemetry Distributed Tracing & Span Collector

---

## 1. Overview & Objective

In multi-agent and RAG architectures, single user prompts trigger cascading asynchronous operations across **vector search retrievers, tool execution sandboxes, LLM generation nodes, and output guardrails**.
- Without distributed tracing, identifying the root cause of a 3-second latency spike or a hallucinated response requires manual, fragmented log inspection.
- Production observability demands **hierarchical trace spans** conforming to **OpenTelemetry & OpenInference standards** to capture exact execution timelines, prompt/completion payloads, token counts, and error states.

**Phase 1 Goal:** Build an **OpenTelemetry-Compatible Distributed Trace Collector** that:
1. Implements hierarchical span nesting (`AGENT` $\rightarrow$ `CHAIN` $\rightarrow$ `RETRIEVER` $\rightarrow$ `LLM` $\rightarrow$ `TOOL`).
2. Measures precise millisecond latency and token usage (prompt, completion, total) per span.
3. Provides asynchronous Python context managers for zero-overhead span instrumentation in production code.

---

## 2. Distributed Trace Hierarchy & Span Taxonomy

```

 HIERARCHICAL TRACE SPAN WATERFALL 

 Trace ID: tr_99a81b2c (Total Duration: 642ms | Total Tokens: 1,420) 
 
 [AGENT: Supervisor Graph] (642ms)
 
 [RETRIEVER: pgvector HNSW Search] (45ms) 
 Input: "What is PagedAttention?" | 4 Chunks Retrieved 
 
 [TOOL: Redis Semantic Cache Probe] (1.2ms) 
 Status: Cache Miss 
 
 [LLM: Llama-3.2-1B-Instruct] (580ms) 
 Tokens: Prompt=120, Completion=350 | Throughput=145 tok/s 

```

### Span Kinds & Semantic Attributes:
- **`SpanKind.AGENT`:** Top-level orchestration supervisor span.
- **`SpanKind.RETRIEVER`:** Vector search or hybrid BM25 query span with retrieved document chunk count.
- **`SpanKind.LLM`:** Direct model inference span with temperature, model name, and token usage metrics.
- **`SpanKind.TOOL`:** External tool or API call span (e.g. database query, calculator, web search).

---

## 3. Step-by-Step Code Walkthrough

### Step 1: Trace Data Models (`src/tracing/models.py`)
- `SpanKind`: Enum categorizing operation types.
- `TokenUsage`: Immutable counters for `prompt_tokens`, `completion_tokens`, `total_tokens`, and estimated USD cost.
- `TraceSpan`: Individual execution node recording `span_id`, `parent_span_id`, `start_time`, `end_time`, `duration_ms`, inputs, and outputs.
- `TraceRecord`: Root container aggregating all child spans for a single end-to-end user request.

### Step 2: Asynchronous Trace Collector (`src/tracing/collector.py`)
- **`start_trace(name)`:** Initializes a new root trace session.
- **`span(name, kind, ...)`:** Async context manager automatically timing block execution and recording errors on exception.
- **`get_trace(trace_id)`:** Retrieves full waterfall telemetry for visualization.

---

## 4. How to Run & Verify Phase 1

### Command:
```bash
./.venv/bin/pytest tests/test_tracing.py
```

### Expected Output:
```text
============================== 4 passed in 0.05s ==============================
```

### What the Tests Verify:
1. `test_trace_span_lifecycle`: Confirms start/end timing and duration calculation in milliseconds.
2. `test_hierarchical_parent_child_spans`: Asserts child spans correctly bind to root parent IDs.
3. `test_token_aggregation`: Validates that child LLM token counts sum accurately to root trace totals.
4. `test_error_state_capture`: Verifies exceptions inside spans mark `status="ERROR"` with stack traces.

---

## 5. Technical Questions & Architectural Explanations

### Q: Why decouple trace span collection from synchronous logging?
> **Answer:** Synchronous logging during inference adds I/O blocking overhead to generation loops. Asynchronous OpenTelemetry collectors buffer span telemetry in-memory and dispatch trace batches in background tasks via non-blocking queues, ensuring zero latency degradation on real-time token streaming.
