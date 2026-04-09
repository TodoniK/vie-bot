import asyncio
import logging

import httpx

from vie_bot.api import fetch_all_details, fetch_offer_ids
from vie_bot.discord import send_notification
from vie_bot.storage import get_seen_ids, mark_as_seen

logger = logging.getLogger(__name__)


async def check_new_offers() -> None:
    """Vérifie les nouvelles offres et envoie les notifications."""
    async with httpx.AsyncClient() as client:
        # 1. Récupérer tous les IDs d'offres
        all_ids = await fetch_offer_ids(client)
        if not all_ids:
            logger.info("No offers returned from API")
            return

        # 2. Filtrer les nouvelles
        seen_ids = get_seen_ids()
        new_ids = [oid for oid in all_ids if oid not in seen_ids]

        if not new_ids:
            logger.info("No new offers")
            return

        logger.info("Found %d new offer(s)", len(new_ids))

        # 3. Récupérer les détails (en parallèle par batch)
        offers = await fetch_all_details(client, new_ids)
        if not offers:
            logger.warning("No valid offer details retrieved")
            return

        logger.info("Fetched details for %d offer(s), sending notifications...", len(offers))

        # 4. Envoyer les notifications
        success_ids: list[int] = []
        for i, offer in enumerate(offers, 1):
            if await send_notification(client, offer):
                success_ids.append(offer["id"])

            # Rate limit Discord (~5 req/s pour les webhooks)
            if i < len(offers):
                await asyncio.sleep(1.5)

        # 5. Sauvegarder les IDs traités
        mark_as_seen(success_ids)
        logger.info("Done: %d/%d notification(s) sent", len(success_ids), len(offers))
