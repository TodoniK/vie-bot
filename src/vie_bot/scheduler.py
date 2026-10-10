import logging

import httpx

from vie_bot.api import fetch_all_offers
from vie_bot.classify import classify_offer
from vie_bot.discord import send_error_alert, send_offers
from vie_bot.storage import count_seen, get_seen_ids, mark_as_seen, touch_heartbeat

logger = logging.getLogger(__name__)


async def check_new_offers() -> None:
    """Vérifie les nouvelles offres et envoie les notifications (IT/RH uniquement)."""
    async with httpx.AsyncClient() as client:
        # 1. Récupérer toutes les offres (données complètes, paginé)
        all_offers = await fetch_all_offers(client)
        if not all_offers:
            logger.info("No offers returned from API")
            touch_heartbeat()
            return

        # 2. Base vide (premier démarrage, volume neuf) : on mémorise l'existant sans rien poster
        if count_seen() == 0:
            mark_as_seen([o["id"] for o in all_offers])
            matching = sum(1 for o in all_offers if classify_offer(o))
            logger.info("Initial sync: %d offers memorized, nothing posted", len(all_offers))
            await send_error_alert(
                "🟢 Bot VIE démarré",
                f"Base initialisée avec {len(all_offers)} offres existantes "
                f"(dont {matching} IT/RH), non postées. Seules les nouvelles offres seront notifiées.",
                color=0x3498DB,
            )
            touch_heartbeat()
            return

        # 3. Filtrer les nouvelles
        seen_ids = get_seen_ids()
        new_offers = [o for o in all_offers if o["id"] not in seen_ids]
        if not new_offers:
            logger.info("No new offers")
            touch_heartbeat()
            return

        new_offers.sort(key=lambda o: o.get("creationDate", ""))

        # 4. Classifier : seules les offres IT (zone géo) ou RH sont notifiées
        classified = [(o, classify_offer(o)) for o in new_offers]
        to_notify = [(o, c) for o, c in classified if c]
        skipped_ids = [o["id"] for o, c in classified if not c]
        logger.info(
            "%d new offer(s): %d match IT/HR, %d skipped",
            len(new_offers),
            len(to_notify),
            len(skipped_ids),
        )

        # 5. Envoyer (par lots) puis mémoriser envoyées + hors critères (pas les échecs d'envoi)
        sent_ids = await send_offers(client, to_notify)
        mark_as_seen(skipped_ids + sent_ids)
        logger.info("Done: %d/%d notification(s) sent", len(sent_ids), len(to_notify))
        touch_heartbeat()
