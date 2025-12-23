from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 7777

    MISTRAL_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
