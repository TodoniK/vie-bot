import asyncio
import logging
import signal
import sys

from vie_bot.config import settings
from vie_bot.discord import send_error_alert
from vie_bot.resilience import should_alert
from vie_bot.scheduler import check_new_offers
from vie_bot.storage import heartbeat_age


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # httpx journalise l'URL complète en INFO : le jeton du webhook Discord finirait dans les logs
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def _run() -> None:
    logger = logging.getLogger("vie_bot")
    logger.info("VIE Bot starting (interval: %ds)", settings.check_interval)

    # Boucle principale
    stop = asyncio.Event()
    consecutive_failures = 0

    def _handle_signal() -> None:
        logger.info("Shutdown signal received")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal)

    while not stop.is_set():
        try:
            await check_new_offers()
            if consecutive_failures:
                await send_error_alert(
                    "✅ Bot VIE rétabli",
                    f"Fonctionne de nouveau normalement après {consecutive_failures} "
                    f"échec(s) consécutif(s).",
                    color=0x2ECC71,
                )
            consecutive_failures = 0
        except Exception as e:
            logger.exception("Error during check cycle")
            consecutive_failures += 1
            if should_alert(consecutive_failures):
                await send_error_alert(
                    "🔴 Bot VIE en erreur",
                    f"```{e}```\n{consecutive_failures} échec(s) consécutif(s) "
                    f"depuis le début de l'incident.",
                )

        # Attente interruptible
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.check_interval)
        except asyncio.TimeoutError:
            pass

    logger.info("VIE Bot stopped")


def healthcheck() -> int:
    """0 si un cycle a réussi récemment (3 intervalles + 5 min de marge), sinon 1."""
    age = heartbeat_age()
    return 0 if age is not None and age < 3 * settings.check_interval + 300 else 1


def main() -> None:
    if sys.argv[1:] == ["healthcheck"]:
        sys.exit(healthcheck())
    _setup_logging()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
