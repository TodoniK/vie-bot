import asyncio
import json
import logging
import re
from datetime import datetime, timezone

import httpx

from vie_bot.config import settings

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────


def _country_code_to_flag(country_code: str | None) -> str:
    if not country_code or len(country_code) != 2:
        return "🌍"
    return "".join(chr(ord(c.upper()) + 127397) for c in country_code)


def _sanitize_markdown(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`~|>\[\]()#]", "", text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _truncate(text: str, max_len: int = 200) -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def _format_date(date_string: str | None) -> str:
    if not date_string:
        return "N/A"
    try:
        date_part = date_string.split("T")[0]
        return datetime.strptime(date_part, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, IndexError):
        return date_string


def _format_indemnite(amount: float | None) -> str:
    if not amount:
        return "N/A"
    integer_part = int(amount)
    decimal_part = int(round((amount - integer_part) * 100))
    formatted_int = f"{integer_part:,}".replace(",", "\u202f")
    return f"{formatted_int},{decimal_part:02d}"


def _clean_contact_name(name: str | None) -> str:
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"^(Madame|Monsieur)\s+", "", name, flags=re.IGNORECASE).strip()
    return name.replace(" ", "%20")


# ── Embed builder ────────────────────────────────────────


def _build_embed(offer: dict, category: str) -> dict:
    offer_id = str(offer["id"])
    contact_name = _clean_contact_name(offer.get("contactName", ""))
    linkedin_url = (
        f"https://www.linkedin.com/search/results/all/?keywords={contact_name}"
        if contact_name
        else None
    )
    bf_url = f"https://mon-vie-via.businessfrance.fr/offres/{offer_id}"

    # Location
    flag = _country_code_to_flag(offer.get("countryId", ""))
    city = (offer.get("cityName", "") or "").strip()
    country = offer.get("countryName", "N/A")
    location = f"{flag}  **{city}**, {country}" if city else f"{flag}  {country}"

    # Description excerpt
    raw_desc = (offer.get("missionDescription", "") or "").strip().lstrip(":").strip()
    excerpt_block = ""
    if raw_desc:
        excerpt = _sanitize_markdown(_truncate(raw_desc, 200))
        excerpt_block = f"\n> *{excerpt}*\n"

    # Metrics
    indemnite = _format_indemnite(offer.get("indemnite", 0))
    duration = offer.get("missionDuration", "—")
    start = _format_date(offer.get("missionStartDate"))
    end = _format_date(offer.get("missionEndDate"))
    telework = "✅ Oui" if offer.get("teleworkingAvailable") else "❌ Non"

    description = (
        f"{location}\n"
        f"{excerpt_block}\n"
        f"💵  **{indemnite} €** /mois\n"
        f"📅  **{duration} mois**  ─  {start} → {end}\n"
        f"🏠  Télétravail : {telework}\n"
    )

    # Links
    email = offer.get("contactEmail", "N/A")
    links = [f"[🌐 Voir l'offre]({bf_url})"]
    if linkedin_url:
        links.append(f"[🔍 LinkedIn]({linkedin_url})")

    fields = [
        {"name": "📧  Contact", "value": f"`{email}`" if email != "N/A" else "N/A", "inline": True},
        {"name": "🔗  Liens rapides", "value": "\n".join(links), "inline": True},
    ]

    color = 0xE67E22 if category == "it" else 0x9B59B6
    reference = offer.get("reference", f"VIE{offer_id}")
    pub_date = _format_date(offer.get("creationDate"))

    return {
        "author": {"name": f"🏢  {offer.get('organizationName', 'Entreprise')}"},
        "title": _truncate(offer.get("missionTitle", "Sans titre"), 250),
        "url": bf_url,
        "description": description,
        "fields": fields,
        "color": color,
        "footer": {"text": f"📆 Publiée le {pub_date}  •  {reference}"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Sender ───────────────────────────────────────────────

# Limites Discord par message : 10 embeds et 6 000 caractères cumulés
MAX_EMBEDS = 10
MAX_CHARS = 5500  # marge sous 6 000 (la taille JSON surestime le texte compté)


def _embed_size(embed: dict) -> int:
    return len(json.dumps(embed, ensure_ascii=False))


def batch_embeds(items: list[tuple[int, dict]]) -> list[list[tuple[int, dict]]]:
    """Regroupe (id, embed) en messages respectant les limites Discord."""
    batches: list[list[tuple[int, dict]]] = []
    current: list[tuple[int, dict]] = []
    size = 0
    for item in items:
        s = _embed_size(item[1])
        if current and (len(current) >= MAX_EMBEDS or size + s > MAX_CHARS):
            batches.append(current)
            current, size = [], 0
        current.append(item)
        size += s
    if current:
        batches.append(current)
    return batches


async def _post(client: httpx.AsyncClient, payload: dict, attempts: int = 5) -> None:
    """POST sur le webhook en respectant les 429 (retry_after) de Discord."""
    for _ in range(attempts):
        resp = await client.post(settings.discord_webhook_url, json=payload, timeout=10)
        if resp.status_code == 429:
            try:
                delay = float(resp.json().get("retry_after", 1))
            except ValueError:
                delay = float(resp.headers.get("Retry-After", 1))
            logger.warning("Discord 429, nouvel essai dans %.1fs", delay)
            await asyncio.sleep(min(delay, 60) + 0.1)
            continue
        resp.raise_for_status()
        return
    raise httpx.HTTPError("Discord : trop de 429 consécutifs")


async def send_offers(client: httpx.AsyncClient, offers: list[tuple[dict, str]]) -> list[int]:
    """Envoie les offres (offre, catégorie) par lots ; retourne les IDs effectivement envoyés."""
    items = [(o["id"], _build_embed(o, c)) for o, c in offers]
    sent: list[int] = []
    for batch in batch_embeds(items):
        try:
            await _post(client, {"embeds": [e for _, e in batch]})
            sent.extend(i for i, _ in batch)
            logger.info("Sent %d offer(s): %s", len(batch), [i for i, _ in batch])
        except httpx.HTTPError as e:
            logger.error("Failed to send offers %s: %s", [i for i, _ in batch], e)
        await asyncio.sleep(1)  # webhooks : ~5 req / 2 s
    return sent


async def send_error_alert(title: str, message: str, color: int = 0xE74C3C) -> None:
    """Envoie une alerte (erreur, rétablissement, info) au webhook Discord."""
    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            await _post(client, payload)
    except httpx.HTTPError as e:
        logger.error("Failed to send alert to Discord: %s", e)
