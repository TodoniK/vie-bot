import httpx
import pytest

from vie_bot import discord


def _offer(i: int, desc_len: int = 50) -> dict:
    return {"id": i, "missionTitle": f"Dev {i}", "countryId": "US", "countryName": "USA",
            "missionDescription": "x " * desc_len, "contactEmail": "a@b.c"}


def test_batches_respect_discord_limits():
    items = [(i, discord._build_embed(_offer(i, 400), "it")) for i in range(25)]
    batches = discord.batch_embeds(items)
    assert sum(len(b) for b in batches) == 25
    for b in batches:
        assert len(b) <= discord.MAX_EMBEDS
        assert sum(discord._embed_size(e) for _, e in b) <= discord.MAX_CHARS


@pytest.mark.asyncio
async def test_post_retries_after_429(monkeypatch):
    monkeypatch.setattr(discord.asyncio, "sleep", lambda s: _noop())
    responses = iter([httpx.Response(429, json={"retry_after": 0.2}), httpx.Response(204)])
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: next(responses))) as client:
        sent = await discord.send_offers(client, [(_offer(1), "it"), (_offer(2), "hr")])
    assert sent == [1, 2]


async def _noop():
    return None
