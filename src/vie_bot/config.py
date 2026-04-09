from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discord_webhook_url: str
    check_interval: int = 60
    search_limit: int = 5000
    data_dir: str = "/app/data"
    log_level: str = "INFO"

    # API Business France
    api_base_url: str = "https://civiweb-api-prd.azurewebsites.net/api"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def api_search_url(self) -> str:
        return f"{self.api_base_url}/Offers/search"

    @property
    def api_details_url(self) -> str:
        return f"{self.api_base_url}/Offers/details"


settings = Settings()
