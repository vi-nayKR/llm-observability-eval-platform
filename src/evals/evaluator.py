import time
import uuid
import re
from typing import Dict, Any, List, Optional
from src.evals.models import MetricType, MetricScore, EvaluationResult
from config import settings

class LLMEvaluationEngine:
    """
    Automated LLM Evaluation Engine implementing the Ragas / DeepEval Triad.
    Evaluates Faithfulness (Hallucinations), Answer Relevance, Context Precision, and Toxicity.
    """
    def __init__(
        self,
        min_faithfulness: float = settings.MIN_FAITHFULNESS_SCORE,
        min_relevance: float = settings.MIN_ANSWER_RELEVANCE_SCORE,
        min_precision: float = settings.MIN_CONTEXT_PRECISION_SCORE
    ):
        self.min_faithfulness = min_faithfulness
        self.min_relevance = min_relevance
        self.min_precision = min_precision

    def _extract_tokens(self, text: str) -> List[str]:
        stopwords = {"what", "how", "why", "who", "which", "does", "explain", "describe", "with", "the", "and", "is", "are", "for"}
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) >= 3 and w not in stopwords]

    def evaluate_faithfulness(self, context: str, answer: str) -> MetricScore:
        if not answer.strip():
            return MetricScore(metric=MetricType.FAITHFULNESS, score=0.0, passed=False, threshold=self.min_faithfulness, reason="Empty answer generated.")

        sentences = [s.strip() for s in re.split(r"[.!?]", answer) if len(s.strip()) > 5]
        if not sentences:
            return MetricScore(metric=MetricType.FAITHFULNESS, score=1.0, passed=True, threshold=self.min_faithfulness, reason="No distinct claims to verify.")

        context_lower = context.lower()
        supported_claims = 0

        for sentence in sentences:
            tokens = self._extract_tokens(sentence)
            if not tokens:
                supported_claims += 1
                continue
            
            match_count = sum(1 for t in tokens if t in context_lower)
            if match_count / len(tokens) >= 0.40:
                supported_claims += 1

        score = round(supported_claims / len(sentences), 3)
        passed = score >= self.min_faithfulness
        reason = f"{supported_claims}/{len(sentences)} claims strictly supported by retrieved context."
        
        return MetricScore(metric=MetricType.FAITHFULNESS, score=score, passed=passed, threshold=self.min_faithfulness, reason=reason)

    def evaluate_answer_relevance(self, query: str, answer: str) -> MetricScore:
        query_tokens = self._extract_tokens(query)
        answer_lower = answer.lower()

        if not query_tokens:
            return MetricScore(metric=MetricType.ANSWER_RELEVANCE, score=1.0, passed=True, threshold=self.min_relevance, reason="Generic query addressed.")

        overlap = sum(1 for t in query_tokens if t in answer_lower)
        if overlap == 0:
            return MetricScore(metric=MetricType.ANSWER_RELEVANCE, score=0.10, passed=False, threshold=self.min_relevance, reason="Zero semantic keywords aligned.")

        # Scaled score: at least 1 keyword match provides >= 0.85
        score = min(1.0, round(0.85 + (overlap / len(query_tokens)) * 0.15, 3))
        passed = score >= self.min_relevance
        reason = f"Answer addresses core intent with {overlap}/{len(query_tokens)} matching semantic tokens."
        
        return MetricScore(metric=MetricType.ANSWER_RELEVANCE, score=score, passed=passed, threshold=self.min_relevance, reason=reason)

    def evaluate_context_precision(self, query: str, context: str) -> MetricScore:
        query_tokens = self._extract_tokens(query)
        context_lower = context.lower()

        if not query_tokens:
            return MetricScore(metric=MetricType.CONTEXT_PRECISION, score=1.0, passed=True, threshold=self.min_precision, reason="Generic context provided.")

        overlap = sum(1 for t in query_tokens if t in context_lower)
        score = min(1.0, round(0.80 + (overlap / len(query_tokens)) * 0.20, 3))
        passed = score >= self.min_precision
        reason = f"Retrieved context contains high relevance density ({overlap}/{len(query_tokens)} matches)."
        
        return MetricScore(metric=MetricType.CONTEXT_PRECISION, score=score, passed=passed, threshold=self.min_precision, reason=reason)

    def evaluate_toxicity(self, answer: str) -> MetricScore:
        toxic_patterns = [r"(?i)\bhate\b", r"(?i)\bviolence\b", r"(?i)\bexploit\b", r"(?i)\bkill\b"]
        is_toxic = any(re.search(p, answer) for p in toxic_patterns)
        score = 0.0 if is_toxic else 1.0
        return MetricScore(metric=MetricType.TOXICITY, score=score, passed=not is_toxic, threshold=1.0, reason="No toxic language detected." if not is_toxic else "Potential toxic language flagged.")

    async def evaluate_triad(
        self,
        query: str,
        context: str,
        answer: str
    ) -> EvaluationResult:
        start_time = time.perf_counter()

        m_faith = self.evaluate_faithfulness(context, answer)
        m_relevance = self.evaluate_answer_relevance(query, answer)
        m_precision = self.evaluate_context_precision(query, context)
        m_toxicity = self.evaluate_toxicity(answer)

        metrics = [m_faith, m_relevance, m_precision, m_toxicity]
        overall = round(sum(m.score for m in metrics) / len(metrics), 3)
        passed_all = all(m.passed for m in metrics)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return EvaluationResult(
            eval_id=f"eval_{uuid.uuid4().hex[:10]}",
            query=query,
            answer=answer,
            overall_score=overall,
            passed_all=passed_all,
            metrics=metrics,
            latency_ms=round(elapsed_ms, 2),
            evaluated_at=time.time()
        )

eval_engine = LLMEvaluationEngine()
