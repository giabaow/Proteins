"""
Central config. Reads from .env (copy .env.example -> .env and fill in your keys).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    # Only needed if the key above is an ORG-level key not scoped to a workspace
    # (the API then requires the workspace id). A workspace-scoped key needs none.
    anthropic_workspace_id: str = ""
    # Optional: Serper.dev Google Search API key. Enables the primary path in
    # search_web(); empty falls back to the no-key DuckDuckGo/Bing chain.
    serper_api_key: str = ""
    # SEC requires an identifying User-Agent with a contact email for filing access.
    sec_user_agent: str = ""

    # Fresh, single-purpose stores for the EU platform-competitor census.
    sqlite_path: str = "./data/eu_competitors.db"
    chroma_path: str = "./chroma_data"


settings = Settings()
