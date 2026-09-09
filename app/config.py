"""
Central config. Reads from .env (copy .env.example -> .env and fill in your key).
Nothing company-confidential is hardcoded here on purpose - see README ground rules.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    # SEC requires an identifying User-Agent with a contact email for filing access.
    sec_user_agent: str = ""

    # Default Opportunity Index weights. UI can override these per-request.
    oi_weight_unmet_need: float = 0.3
    oi_weight_sensitivity_gain: float = 0.2
    oi_weight_market: float = 0.3
    oi_weight_regulatory_burden: float = 0.2

    sqlite_path: str = "./data/opportunities.db"
    chroma_path: str = "./chroma_data"


settings = Settings()
