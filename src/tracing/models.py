import time
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SpanKind(str, Enum):
    AGENT = "agent"
    CHAIN = "chain"
    LLM = "llm"
    RETRIEVER = "retriever"
    TOOL = "tool"
    GUARDRAIL = "guardrail"

class SpanStatus(str, Enum):
    OK = "OK"
    ERROR = "ERROR"

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: f"span_{uuid.uuid4().hex[:10]}")
    parent_span_id: Optional[str] = None
    name: str
    kind: SpanKind
    status: SpanStatus = SpanStatus.OK
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    tokens: TokenUsage = Field(default_factory=TokenUsage)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def finish(self, status: SpanStatus = SpanStatus.OK, error: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        self.status = status
        self.error_message = error

class TraceRecord(BaseModel):
    trace_id: str = Field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:12]}")
    root_span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    total_tokens: TokenUsage = Field(default_factory=TokenUsage)
    spans: List[TraceSpan] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def aggregate_metrics(self):
        """Computes aggregate token usage and total latency across all child spans."""
        if self.spans:
            earliest = min(s.start_time for s in self.spans)
            latest = max((s.end_time or s.start_time) for s in self.spans)
            self.start_time = earliest
            self.end_time = latest
            self.total_duration_ms = round((latest - earliest) * 1000.0, 2)

            prompt_toks = sum(s.tokens.prompt_tokens for s in self.spans)
            comp_toks = sum(s.tokens.completion_tokens for s in self.spans)
            cost = sum(s.tokens.estimated_cost_usd for s in self.spans)
            
            self.total_tokens = TokenUsage(
                prompt_tokens=prompt_toks,
                completion_tokens=comp_toks,
                total_tokens=prompt_toks + comp_toks,
                estimated_cost_usd=round(cost, 6)
            )
