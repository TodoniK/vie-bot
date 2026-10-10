import json
import logging
import re
from typing import Any

import httpx

from vie_bot.config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://mon-vie-via.businessfrance.fr",
    "Referer": "https://mon-vie-via.businessfrance.fr/",
    "User-Agent": "Mozilla/5.0",
}

# L'API plafonne "limit" à 200 (400 Bad Request au-delà) : on pagine.
PAGE_SIZE = 200

BASE_PAYLOAD = {
    "studiesLevelId": ["4"],
    "teletravail": ["0"],
    "porteEnv": ["0"],
    "activitySectorId": [],
    "missionsTypesIds": [],
    "missionsDurations": [],
    "geographicZones": [],
    "countriesIds": [],
    "companiesSizes": [],
    "specializationsIds": [],
    "entreprisesIds": [0],
}

# Clé courante : variable d'environnement, sinon relue sur la page publique
_api_key: str | None = settings.civiweb_api_key

# Le front Nuxt sérialise sa config publique : ...,API_KEY:"l+Kw\u002F...",...
_API_KEY_RE = re.compile(r'[,{]API_KEY:"((?:[^"\\]|\\.)*)"')


def extract_api_key(html: str) -> str | None:
    """Extrait la clé X-API-KEY du HTML de mon-vie-via (échappements JS décodés)."""
    m = _API_KEY_RE.search(html)
    return json.loads(f'"{m.group(1)}"') if m else None


async def refresh_api_key(client: httpx.AsyncClient) -> str:
    global _api_key
    resp = await client.get(settings.api_key_page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    key = extract_api_key(resp.text)
    if not key:
        raise RuntimeError(f"API_KEY introuvable dans {settings.api_key_page_url}")
    if key != _api_key:
        logger.info("Clé API Business France (re)chargée depuis la page publique")
    _api_key = key
    return key


async def _search(client: httpx.AsyncClient, skip: int) -> dict[str, Any]:
    if not _api_key:
        await refresh_api_key(client)
    payload = {**BASE_PAYLOAD, "limit": PAGE_SIZE, "skip": skip}
    for attempt in (1, 2):
        resp = await client.post(
            settings.api_search_url,
            json=payload,
            headers={**HEADERS, "X-API-KEY": _api_key or ""},
            timeout=30,
        )
        # Clé périmée (Business France a redéployé son front) : on la relit une fois
        if resp.status_code in (401, 403) and attempt == 1:
            logger.warning("API %s : rafraîchissement de la clé", resp.status_code)
            await refresh_api_key(client)
            continue
        resp.raise_for_status()
        return resp.json()
    raise AssertionError("unreachable")


async def fetch_all_offers(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Récupère toutes les offres (données complètes) depuis l'API de recherche, paginé.

    /api/Offers/search renvoie déjà toutes les données nécessaires à l'embed
    Discord (titre, pays, indemnité, dates, contact...) : pas besoin d'un
    second appel /details par offre.
    """
    offers: list[dict[str, Any]] = []
    skip = 0
    total = None

    while total is None or skip < total:
        if len(offers) >= settings.search_limit:
            logger.warning("search_limit (%d) atteint, arrêt de la pagination", settings.search_limit)
            break

        data = await _search(client, skip)
        page = data.get("result", [])
        total = data.get("count", 0)
        offers.extend(page)
        skip += PAGE_SIZE

        if not page:
            break

    logger.info("API returned %d offers (total: %s)", len(offers), total)
    return offers
