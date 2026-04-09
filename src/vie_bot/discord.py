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


def _build_embed(offer: dict) -> dict:
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

    color = 0x2ECC71 if offer.get("teleworkingAvailable") else 0x0055A4
    reference = offer.get("reference", f"VIE{offer_id}")
    pub_date = _format_date(offer.get("creationDate"))

    return {
        "embeds": [
            {
                "author": {"name": f"🏢  {offer.get('organizationName', 'Entreprise')}"},
                "title": offer.get("missionTitle", "Sans titre"),
                "url": bf_url,
                "description": description,
                "fields": fields,
                "color": color,
                "footer": {"text": f"📆 Publiée le {pub_date}  •  {reference}"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }


# ── Sender ───────────────────────────────────────────────


async def send_notification(client: httpx.AsyncClient, offer: dict) -> bool:
    """Envoie une notification Discord pour une offre."""
    payload = _build_embed(offer)
    try:
        resp = await client.post(
            settings.discord_webhook_url,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Sent notification for offer %s", offer["id"])
        return True
    except httpx.HTTPError as e:
        logger.error("Failed to send notification for offer %s: %s", offer["id"], e)
        return False
