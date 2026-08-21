import pytest
import asyncio
from src.evals.evaluator import eval_engine
from src.evals.models import MetricType

def test_faithful_answer_evaluation():
    context = "vLLM's PagedAttention partitions Key-Value memory into non-contiguous physical virtual pages, reducing VRAM fragmentation to under 4%."
    answer = "PagedAttention manages KV cache in non-contiguous virtual pages to eliminate memory fragmentation."
    
    score = eval_engine.evaluate_faithfulness(context, answer)
    assert score.score >= 0.85
    assert score.passed is True
    assert score.metric == MetricType.FAITHFULNESS

def test_hallucination_penalty():
    context = "PostgreSQL pgvector supports HNSW and IVFFlat indexes for approximate nearest neighbor search."
    # Fabricated answer stating it supports quantum encryption and blockchain mining
    hallucinated_answer = "PostgreSQL pgvector performs quantum cryptocurrency mining and blockchain consensus validation."
    
    score = eval_engine.evaluate_faithfulness(context, hallucinated_answer)
    assert score.score < 0.40
    assert score.passed is False

def test_answer_relevance():
    query = "How does continuous batching work in vLLM?"
    relevant_answer = "Continuous batching dynamically schedules incoming requests into active forward passes without waiting for previous requests to finish."
    off_topic_answer = "The capital of France is Paris."
    
    s_good = eval_engine.evaluate_answer_relevance(query, relevant_answer)
    s_bad = eval_engine.evaluate_answer_relevance(query, off_topic_answer)
    
    assert s_good.score > s_bad.score
    assert s_good.passed is True

@pytest.mark.asyncio
async def test_composite_triad_evaluation():
    query = "What is LoRA fine-tuning?"
    context = "Low-Rank Adaptation (LoRA) freezes base model weights and trains rank decomposition matrices (A and B) in attention layers."
    answer = "LoRA freezes base weights and trains low-rank adapter matrices in attention layers."
    
    result = await eval_engine.evaluate_triad(query, context, answer)
    assert result.overall_score >= 0.85
    assert result.passed_all is True
    assert len(result.metrics) == 4
