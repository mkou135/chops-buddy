from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CB_", env_file=".env", extra="ignore")

    commit_sha: str = "dev"
    llm_api_key: str | None = None


settings = Settings()
