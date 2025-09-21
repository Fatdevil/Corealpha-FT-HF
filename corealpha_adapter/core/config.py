from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = Field(default="dev")
    API_BASE_URL: str = Field(default="http://localhost:8000")
    FINGPT_BASE_URL: str = Field(default="")
    NEWS_API_KEY: str = Field(default="")
    MARKET_API_KEY: str = Field(default="")
    USE_STUB_SUMMARY: bool = Field(default=True)
    USE_STUB_SENTIMENT: bool = Field(default=True)
    USE_STUB_AGENTS: bool = Field(default=True)
    VOTING_METHOD: str = Field(default="WSUM")

    class Config:
        env_file = ".env"


settings = Settings()
