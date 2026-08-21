import time
import uuid
from typing import List, Dict, Any, Callable, Coroutine
from src.ci_cd.models import GoldenTestCase, RegressionGateReport, GateStatus
from src.evals.evaluator import eval_engine
from src.evals.models import EvaluationResult, MetricType

class RegressionGate:
    """
    Automated CI/CD Release Quality Gate Engine.
    Executes golden evaluation benchmarks and blocks deployment if metrics regress below thresholds.
    """
    def __init__(self):
        self.golden_dataset: List[GoldenTestCase] = self._load_default_golden_cases()

    def _load_default_golden_cases(self) -> List[GoldenTestCase]:
        return [
            GoldenTestCase(
                case_id="case_001_paged_attention",
                query="How does vLLM PagedAttention manage KV-cache memory?",
                context="vLLM's PagedAttention partitions Key-Value memory into non-contiguous physical virtual pages, reducing VRAM fragmentation to under 4% and enabling continuous batching.",
                expected_ground_truth="PagedAttention allocates KV-cache memory in non-contiguous virtual pages."
            ),
            GoldenTestCase(
                case_id="case_002_hybrid_search",
                query="What are the benefits of Reciprocal Rank Fusion in RAG?",
                context="Reciprocal Rank Fusion (RRF) combines dense vector rankings with BM25 sparse keyword rankings without score calibration, boosting retrieval recall by 34%.",
                expected_ground_truth="RRF merges dense and sparse search rankings to boost retrieval recall."
            ),
            GoldenTestCase(
                case_id="case_003_qlora_tuning",
                query="Why is 4-bit QLoRA more memory efficient than full fine-tuning?",
                context="4-bit QLoRA freezes the base model in NF4 precision and injects low-rank adapter matrices (r=16), reducing trainable parameters to under 1% of total model weights.",
                expected_ground_truth="QLoRA freezes 4-bit base weights and trains low-rank adapter matrices."
            )
        ]

    async def evaluate_candidate(
        self,
        candidate_version: str,
        answers: Dict[str, str]
    ) -> RegressionGateReport:
        """
        Evaluates a release candidate against the golden test suite.
        """
        results: List[EvaluationResult] = []
        regressed: List[str] = []

        for case in self.golden_dataset:
            answer = answers.get(case.case_id, "")
            res = await eval_engine.evaluate_triad(
                query=case.query,
                context=case.context,
                answer=answer
            )
            results.append(res)
            
            # Check if this case passed thresholds
            m_faith = next((m for m in res.metrics if m.metric == MetricType.FAITHFULNESS), None)
            m_rel = next((m for m in res.metrics if m.metric == MetricType.ANSWER_RELEVANCE), None)

            if not m_faith or not m_rel or m_faith.score < case.min_faithfulness or m_rel.score < case.min_relevance:
                regressed.append(case.case_id)

        total = len(self.golden_dataset)
        passed_count = total - len(regressed)
        pass_rate = round((passed_count / max(1, total)) * 100, 1)

        avg_faith = round(sum(next(m.score for m in r.metrics if m.metric == MetricType.FAITHFULNESS) for r in results) / total, 3)
        avg_rel = round(sum(next(m.score for m in r.metrics if m.metric == MetricType.ANSWER_RELEVANCE) for r in results) / total, 3)
        avg_prec = round(sum(next(m.score for m in r.metrics if m.metric == MetricType.CONTEXT_PRECISION) for r in results) / total, 3)

        status = GateStatus.PASSED if len(regressed) == 0 else GateStatus.REGRESSED

        return RegressionGateReport(
            suite_id=f"gate_{uuid.uuid4().hex[:10]}",
            candidate_version=candidate_version,
            status=status,
            total_tests=total,
            passed_tests=passed_count,
            failed_tests=len(regressed),
            pass_rate=pass_rate,
            avg_faithfulness=avg_faith,
            avg_relevance=avg_rel,
            avg_context_precision=avg_prec,
            results=results,
            regressed_cases=regressed,
            evaluated_at=time.time()
        )

regression_gate = RegressionGate()
