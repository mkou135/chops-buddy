"""DECISIONS #28: the browser client on another origin must be allowed, others not."""

from httpx import AsyncClient

from chops_buddy.settings import settings


async def test_preflight_allows_configured_origin(client: AsyncClient) -> None:
    settings.cors_origins = ["https://mkou135.github.io"]
    r = await client.options(
        "/me",
        headers={
            "Origin": "https://mkou135.github.io",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "https://mkou135.github.io"
    assert "authorization" in r.headers.get("access-control-allow-headers", "").lower()


async def test_unlisted_origin_gets_no_cors_headers(client: AsyncClient) -> None:
    settings.cors_origins = ["https://mkou135.github.io"]
    r = await client.get("/health", headers={"Origin": "https://evil.example"})
    assert r.status_code == 200
    assert "access-control-allow-origin" not in r.headers
