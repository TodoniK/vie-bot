from pydantic_settings import BaseSettings


def csv(value: str) -> list[str]:
    """"a, b ,c" -> ["a", "b", "c"] (variables d'environnement lisibles dans Dokploy)."""
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings(BaseSettings):
    discord_webhook_url: str
    check_interval: int = 60
    search_limit: int = 5000
    data_dir: str = "/app/data"
    log_level: str = "INFO"

    # API Business France
    api_base_url: str = "https://civiweb-api-prd.azurewebsites.net/api"
    # Page publique dont le HTML embarque la clé X-API-KEY (API_KEY:"...")
    api_key_page_url: str = "https://mon-vie-via.businessfrance.fr/offres/recherche"
    # Facultatif : sans valeur (ou si la clé est refusée), le bot la relit sur api_key_page_url
    civiweb_api_key: str | None = None

    # Critères de classification (listes séparées par des virgules), voir classify.py
    it_countries: str = "US,CA,AU,NZ,PH,TH,VN,SG,MY,ID,KH,LA,MM,BN"
    it_extra_keywords: str = ""
    hr_extra_keywords: str = ""
    exclude_extra_keywords: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def api_search_url(self) -> str:
        return f"{self.api_base_url}/Offers/search"


settings = Settings()
