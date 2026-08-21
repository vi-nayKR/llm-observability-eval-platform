import pytest
import asyncio
from src.ci_cd.regression_gate import regression_gate
from src.ci_cd.models import GateStatus

@pytest.mark.asyncio
async def test_passing_release_candidate():
    # Candidate providing faithful, relevant answers
    good_answers = {
        "case_001_paged_attention": "PagedAttention partitions KV cache into non-contiguous virtual pages to eliminate memory fragmentation.",
        "case_002_hybrid_search": "Reciprocal Rank Fusion fuses dense vector search with sparse keyword search to boost retrieval recall.",
        "case_003_qlora_tuning": "QLoRA freezes 4-bit base model weights and trains low-rank adapter matrices to save memory."
    }

    report = await regression_gate.evaluate_candidate("v2.1.0-rc1", good_answers)
    assert report.status == GateStatus.PASSED
    assert report.pass_rate == 100.0
    assert report.failed_tests == 0
    assert len(report.regressed_cases) == 0

@pytest.mark.asyncio
async def test_regressed_candidate_rejection():
    # Candidate providing hallucinated/bad answer on case 1
    regressed_answers = {
        "case_001_paged_attention": "PagedAttention is a cryptocurrency consensus protocol used for quantum blockchain mining.",
        "case_002_hybrid_search": "Reciprocal Rank Fusion fuses dense vector search with sparse keyword search to boost retrieval recall.",
        "case_003_qlora_tuning": "QLoRA freezes 4-bit base model weights and trains low-rank adapter matrices to save memory."
    }

    report = await regression_gate.evaluate_candidate("v2.1.0-bad-prompt", regressed_answers)
    assert report.status == GateStatus.REGRESSED
    assert report.failed_tests >= 1
    assert "case_001_paged_attention" in report.regressed_cases
    assert report.pass_rate < 100.0

@pytest.mark.asyncio
async def test_gate_report_generation():
    answers = {
        "case_001_paged_attention": "PagedAttention manages KV cache in non-contiguous virtual pages.",
        "case_002_hybrid_search": "RRF combines dense and sparse search rankings.",
        "case_003_qlora_tuning": "QLoRA freezes base model weights and trains low-rank adapters."
    }
    report = await regression_gate.evaluate_candidate("v2.0.0", answers)
    assert report.total_tests == 3
    assert report.avg_faithfulness >= 0.85
    assert report.avg_relevance >= 0.85
