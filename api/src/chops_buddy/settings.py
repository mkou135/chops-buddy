from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CB_", env_file=".env", extra="ignore")

    commit_sha: str = "dev"
    llm_api_key: str | None = None  # Anthropic API key; unset = engine only (DoD A4)
    llm_model: str = "claude-opus-5"

    # SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host:6543/postgres
    # For Supabase use the transaction-mode pooler; see db/base.py for the asyncpg flags.
    database_url: str = "postgresql+asyncpg://postgres@localhost:5432/postgres"

    # Supabase Auth. HS256 legacy secret for local/test; JWKS URL is added in M4.
    supabase_jwt_secret: str | None = None

    # Browser origins allowed to call the API (DECISIONS #28). Comma-separated in the env.
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
