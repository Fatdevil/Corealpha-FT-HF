from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = Field(default="dev")
    API_BASE_URL: str = Field(default="http://localhost:8000")
    LLM_PROVIDER: str = Field(default="fingpt")
    FINGPT_BASE_URL: str = Field(default="")
    FINGPT_API_KEY: str = Field(default="")
    HTTP_TIMEOUT_SECONDS: float = Field(default=20.0)
    HTTP_MAX_RETRIES: int = Field(default=2)
    CACHE_TTL_SECONDS: int = Field(default=60)
    NEWS_API_KEY: str = Field(default="")
    MARKET_API_KEY: str = Field(default="")
    USE_STUB_SUMMARY: bool = Field(default=True)
    USE_STUB_SENTIMENT: bool = Field(default=True)
    USE_STUB_AGENTS: bool = Field(default=True)
    VOTING_METHOD: str = Field(default="WSUM")

    class Config:
        env_file = ".env"


settings = Settings()
