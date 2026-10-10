import pytest

from vie_bot import scheduler, storage


@pytest.mark.asyncio
async def test_first_run_is_silent_then_notifies_only_new(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "db.sqlite")
    monkeypatch.setattr(storage, "HEARTBEAT_PATH", tmp_path / "heartbeat")
    offers = [{"id": 1, "missionTitle": "DevOps Engineer", "countryId": "US"}]
    posted, alerts = [], []

    async def fetch(_client):
        return list(offers)

    async def send(_client, items):
        posted.extend(o["id"] for o, _ in items)
        return [o["id"] for o, _ in items]

    async def alert(title, *_a, **_k):
        alerts.append(title)

    monkeypatch.setattr(scheduler, "fetch_all_offers", fetch)
    monkeypatch.setattr(scheduler, "send_offers", send)
    monkeypatch.setattr(scheduler, "send_error_alert", alert)

    await scheduler.check_new_offers()
    assert posted == [] and len(alerts) == 1 and storage.heartbeat_age() is not None

    offers.append({"id": 2, "missionTitle": "Cloud Engineer", "countryId": "CA"})
    offers.append({"id": 3, "missionTitle": "Comptable", "countryId": "US"})
    await scheduler.check_new_offers()
    assert posted == [2]
    assert storage.get_seen_ids() == {1, 2, 3}
