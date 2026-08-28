import asyncio
import logging

import httpx

from vie_bot.api import fetch_all_offers
from vie_bot.classify import classify_offer
from vie_bot.discord import send_notification
from vie_bot.storage import get_seen_ids, mark_as_seen

logger = logging.getLogger(__name__)


async def check_new_offers() -> None:
    """Vérifie les nouvelles offres et envoie les notifications (IT/RH uniquement)."""
    async with httpx.AsyncClient() as client:
        # 1. Récupérer toutes les offres (données complètes, paginé)
        all_offers = await fetch_all_offers(client)
        if not all_offers:
            logger.info("No offers returned from API")
            return

        # 2. Filtrer les nouvelles
        seen_ids = get_seen_ids()
        new_offers = [o for o in all_offers if o["id"] not in seen_ids]

        if not new_offers:
            logger.info("No new offers")
            return

        new_offers.sort(key=lambda o: o.get("creationDate", ""))
        logger.info("Found %d new offer(s)", len(new_offers))

        # 3. Classifier : seules les offres IT (zone géo) ou RH sont notifiées
        classified = [(o, classify_offer(o)) for o in new_offers]
        to_notify = [(o, c) for o, c in classified if c]
        skipped_ids = [o["id"] for o, c in classified if not c]

        logger.info(
            "%d offer(s) match IT/HR criteria, %d skipped (hors critères)",
            len(to_notify),
            len(skipped_ids),
        )

        # 4. Envoyer les notifications
        success_ids: list[int] = []
        for i, (offer, category) in enumerate(to_notify, 1):
            if await send_notification(client, offer, category):
                success_ids.append(offer["id"])

            # Rate limit Discord (~5 req/s pour les webhooks)
            if i < len(to_notify):
                await asyncio.sleep(1.5)

        # 5. Sauvegarder les IDs traités (envoyés + hors critères, pas les échecs d'envoi)
        mark_as_seen(skipped_ids + success_ids)
        logger.info(
            "Done: %d/%d notification(s) sent, %d skipped",
            len(success_ids),
            len(to_notify),
            len(skipped_ids),
        )
