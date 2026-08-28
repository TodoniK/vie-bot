import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from vie_bot.config import settings
from vie_bot.discord import send_error_alert
from vie_bot.resilience import should_alert
from vie_bot.scheduler import check_new_offers
from vie_bot.storage import import_from_txt


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


async def _run() -> None:
    logger = logging.getLogger("vie_bot")
    logger.info("VIE Bot starting (interval: %ds)", settings.check_interval)

    # Migration ids.txt → SQLite (si le fichier existe)
    legacy_path = Path(settings.data_dir) / "ids.txt"
    if legacy_path.exists():
        count = import_from_txt(str(legacy_path))
        if count:
            legacy_path.rename(legacy_path.with_suffix(".txt.bak"))
            logger.info("Migrated ids.txt → SQLite (%d IDs), backup: ids.txt.bak", count)

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


def main() -> None:
    _setup_logging()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
