import pytest
import asyncio
from src.tracing.models import SpanKind, SpanStatus
from src.tracing.collector import trace_collector

@pytest.mark.asyncio
async def test_trace_span_lifecycle():
    trace = trace_collector.create_trace("test_agent_run")
    
    async with trace_collector.span(trace.trace_id, "retrieve_context", SpanKind.RETRIEVER) as s:
        await asyncio.sleep(0.01)
        s.outputs = {"chunks_retrieved": 4}

    retrieved_trace = trace_collector.get_trace(trace.trace_id)
    assert retrieved_trace is not None
    assert len(retrieved_trace.spans) == 1
    assert retrieved_trace.spans[0].name == "retrieve_context"
    assert retrieved_trace.spans[0].status == SpanStatus.OK
    assert retrieved_trace.spans[0].duration_ms >= 9.0

@pytest.mark.asyncio
async def test_hierarchical_parent_child_spans():
    trace = trace_collector.create_trace("multi_agent_workflow")
    
    async with trace_collector.span(trace.trace_id, "supervisor_agent", SpanKind.AGENT) as parent:
        async with trace_collector.span(trace.trace_id, "llm_generate", SpanKind.LLM, parent_span_id=parent.span_id) as child:
            trace_collector.record_llm_tokens(child, prompt_tokens=150, completion_tokens=300)

    t = trace_collector.get_trace(trace.trace_id)
    assert len(t.spans) == 2
    llm_span = next(s for s in t.spans if s.kind == SpanKind.LLM)
    assert llm_span.parent_span_id is not None
    assert t.total_tokens.total_tokens == 450
    assert t.total_tokens.estimated_cost_usd > 0.0

@pytest.mark.asyncio
async def test_token_aggregation():
    trace = trace_collector.create_trace("token_test")
    
    async with trace_collector.span(trace.trace_id, "call_1", SpanKind.LLM) as s1:
        trace_collector.record_llm_tokens(s1, prompt_tokens=100, completion_tokens=100)
        
    async with trace_collector.span(trace.trace_id, "call_2", SpanKind.LLM) as s2:
        trace_collector.record_llm_tokens(s2, prompt_tokens=200, completion_tokens=200)

    t = trace_collector.get_trace(trace.trace_id)
    assert t.total_tokens.prompt_tokens == 300
    assert t.total_tokens.completion_tokens == 300
    assert t.total_tokens.total_tokens == 600

@pytest.mark.asyncio
async def test_error_state_capture():
    trace = trace_collector.create_trace("error_trace")
    
    with pytest.raises(ValueError):
        async with trace_collector.span(trace.trace_id, "failing_tool", SpanKind.TOOL) as s:
            raise ValueError("Tool connection timeout")

    t = trace_collector.get_trace(trace.trace_id)
    assert len(t.spans) == 1
    assert t.spans[0].status == SpanStatus.ERROR
    assert "Tool connection timeout" in t.spans[0].error_message
