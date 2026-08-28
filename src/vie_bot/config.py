from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discord_webhook_url: str
    check_interval: int = 60
    search_limit: int = 5000
    data_dir: str = "/app/data"
    log_level: str = "INFO"

    # API Business France
    api_base_url: str = "https://civiweb-api-prd.azurewebsites.net/api"
    # Header X-API-KEY requis par l'API depuis fin août 2026.
    # À récupérer via le Network tab du navigateur sur mon-vie-via.businessfrance.fr
    # (peut changer si Business France redéploie son frontend).
    civiweb_api_key: str

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def api_search_url(self) -> str:
        return f"{self.api_base_url}/Offers/search"


settings = Settings()
