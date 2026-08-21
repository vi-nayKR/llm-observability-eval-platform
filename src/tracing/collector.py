import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from src.tracing.models import TraceRecord, TraceSpan, SpanKind, SpanStatus, TokenUsage

class TraceCollector:
    """
    OpenTelemetry & OpenInference Distributed Trace Collector.
    Captures hierarchical trace spans across LLM inference, retrieval, and tool execution.
    """
    def __init__(self):
        self._traces: Dict[str, TraceRecord] = {}
        self._active_spans: Dict[str, TraceSpan] = {}

    def create_trace(self, name: str, tags: Optional[List[str]] = None) -> TraceRecord:
        """Initializes a new root trace session."""
        root_id = f"span_{uuid.uuid4().hex[:10]}"
        trace = TraceRecord(
            root_span_id=root_id,
            name=name,
            start_time=time.time(),
            tags=tags or ["production", "llm-pipeline"]
        )
        self._traces[trace.trace_id] = trace
        return trace

    @asynccontextmanager
    async def span(
        self,
        trace_id: str,
        name: str,
        kind: SpanKind,
        parent_span_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Asynchronous context manager recording span execution and timing."""
        span_obj = TraceSpan(
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time=time.time(),
            inputs=inputs or {},
            metadata=metadata or {}
        )
        self._active_spans[span_obj.span_id] = span_obj

        try:
            yield span_obj
            span_obj.finish(status=SpanStatus.OK)
        except Exception as e:
            span_obj.finish(status=SpanStatus.ERROR, error=str(e))
            raise e
        finally:
            if trace_id in self._traces:
                self._traces[trace_id].spans.append(span_obj)
                self._traces[trace_id].aggregate_metrics()
            self._active_spans.pop(span_obj.span_id, None)

    def record_llm_tokens(
        self,
        span_obj: TraceSpan,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4o-mini"
    ):
        """Calculates token counts and estimated cost."""
        # Standard pricing: ~$0.15 / 1M prompt, ~$0.60 / 1M completion
        cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
        span_obj.tokens = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=round(cost, 6)
        )

    def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        return self._traces.get(trace_id)

    def get_all_traces(self) -> List[TraceRecord]:
        return list(self._traces.values())

    def clear(self):
        self._traces.clear()

trace_collector = TraceCollector()
