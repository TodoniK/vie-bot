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
}

SEARCH_PAYLOAD = {
    "limit": settings.search_limit,
    "skip": 0,
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


async def fetch_offer_ids(client: httpx.AsyncClient) -> list[int]:
    """Récupère tous les IDs d'offres depuis l'API de recherche."""
    resp = await client.post(
        settings.api_search_url,
        json=SEARCH_PAYLOAD,
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    offers = data.get("result", [])
    logger.info("API returned %d offers (total: %d)", len(offers), data.get("count", 0))
    return [offer["id"] for offer in offers]


async def fetch_offer_details(client: httpx.AsyncClient, offer_id: int) -> dict[str, Any] | None:
    """Récupère les détails d'une offre."""
    try:
        resp = await client.get(
            f"{settings.api_details_url}/{offer_id}",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch offer %d: %s", offer_id, e)
        return None


async def fetch_all_details(client: httpx.AsyncClient, offer_ids: list[int]) -> list[dict[str, Any]]:
    """Récupère les détails de plusieurs offres en parallèle (par batch de 10)."""
    results: list[dict[str, Any]] = []
    batch_size = 10

    for i in range(0, len(offer_ids), batch_size):
        batch = offer_ids[i : i + batch_size]
        import asyncio

        tasks = [fetch_offer_details(client, oid) for oid in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend([r for r in batch_results if r is not None])

    # Tri chronologique
    results.sort(key=lambda x: x.get("creationDate", ""))
    return results
