import os
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    class AppSettings(BaseSettings):
        APP_NAME: str = "Enterprise LLM Observability & Evaluation Platform"
        VERSION: str = "1.0.0"
        HOST: str = "0.0.0.0"
        PORT: int = 8000
        DEFAULT_JUDGE_MODEL: str = "gpt-4o-mini"
        MIN_FAITHFULNESS_SCORE: float = 0.85
        MIN_ANSWER_RELEVANCE_SCORE: float = 0.85
        MIN_CONTEXT_PRECISION_SCORE: float = 0.80
        MAX_LATENCY_THRESHOLD_MS: float = 2500.0
        MAX_HOURLY_BUDGET_USD: float = 50.0
        OPENAI_API_KEY: Optional[str] = None
        ANTHROPIC_API_KEY: Optional[str] = None
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    settings = AppSettings()
except ImportError:
    class StandaloneSettings:
        APP_NAME: str = "Enterprise LLM Observability & Evaluation Platform"
        VERSION: str = "1.0.0"
        HOST: str = "0.0.0.0"
        PORT: int = 8000
        DEFAULT_JUDGE_MODEL: str = "gpt-4o-mini"
        MIN_FAITHFULNESS_SCORE: float = 0.85
        MIN_ANSWER_RELEVANCE_SCORE: float = 0.85
        MIN_CONTEXT_PRECISION_SCORE: float = 0.80
        MAX_LATENCY_THRESHOLD_MS: float = 2500.0
        MAX_HOURLY_BUDGET_USD: float = 50.0
        OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    settings = StandaloneSettings()
