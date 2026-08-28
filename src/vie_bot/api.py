import logging
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
    "X-API-KEY": settings.civiweb_api_key,
}

# L'API plafonne "limit" à 200 (400 Bad Request au-delà) : on paginle.
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

        payload = {**BASE_PAYLOAD, "limit": PAGE_SIZE, "skip": skip}
        resp = await client.post(
            settings.api_search_url,
            json=payload,
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        page = data.get("result", [])
        total = data.get("count", 0)
        offers.extend(page)
        skip += PAGE_SIZE

        if not page:
            break

    logger.info("API returned %d offers (total: %s)", len(offers), total)
    return offers
