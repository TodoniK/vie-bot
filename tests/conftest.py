import os
import tempfile

# Settings est instancié à l'import : environnement de test avant tout import de vie_bot
os.environ.setdefault("DISCORD_WEBHOOK_URL", "https://discord.test/webhook")
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="vie-bot-test-")
