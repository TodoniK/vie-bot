import json

import httpx
import pytest

from vie_bot import api


def test_extract_api_key_decodes_js_escapes():
    html = '<script>window.__NUXT__={config:{X:1,API_KEY:"ab\\u002Fcd+ef==",GMAPS_API_KEY:"zz"}}</script>'
    assert api.extract_api_key(html) == "ab/cd+ef=="
    assert api.extract_api_key("<html></html>") is None


@pytest.mark.asyncio
async def test_search_refreshes_key_on_401(monkeypatch):
    monkeypatch.setattr(api, "_api_key", "stale")
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, text='{a:1,API_KEY:"fresh"}')
        calls.append(request.headers["X-API-KEY"])
        if request.headers["X-API-KEY"] != "fresh":
            return httpx.Response(401)
        body = json.loads(request.content)
        return httpx.Response(200, json={"count": 1, "result": [{"id": 1}]} if body["skip"] == 0 else {"count": 1, "result": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        offers = await api.fetch_all_offers(client)

    assert offers == [{"id": 1}]
    assert calls == ["stale", "fresh"]
