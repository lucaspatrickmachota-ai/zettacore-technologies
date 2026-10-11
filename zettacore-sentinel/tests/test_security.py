import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import MAX_BODY_BYTES, analyze, app
from app.security import BodySizeLimitMiddleware, SlidingWindowLimiter, client_ip

client = TestClient(app)


def _scope(peer="10.0.0.1", forwarded=None):
    headers = []
    if forwarded is not None:
        headers.append((b"x-forwarded-for", forwarded.encode()))
    return {"type": "http", "client": (peer, 5000), "headers": headers}


def test_client_ip_ignores_forwarded_header_by_default():
    assert client_ip(_scope(forwarded="1.2.3.4"), trusted_hops=0) == "10.0.0.1"


def test_client_ip_uses_configured_trusted_proxy_entry():
    scope = _scope(forwarded="6.6.6.6, 203.0.113.9")
    assert client_ip(scope, trusted_hops=1) == "203.0.113.9"


def test_client_ip_falls_back_for_missing_or_invalid_forwarded_header():
    assert client_ip(_scope(), trusted_hops=1) == "10.0.0.1"
    assert client_ip(_scope(forwarded="not-an-ip"), trusted_hops=1) == "10.0.0.1"


def test_limiter_blocks_and_recovers_after_window():
    limiter = SlidingWindowLimiter(window_seconds=60, max_requests=3, max_external=1)
    assert all(limiter.allow("a", now=0) for _ in range(3))
    assert not limiter.allow("a", now=1)
    assert limiter.allow("b", now=1)
    assert limiter.allow("a", now=61)


def test_limiter_has_separate_external_lookup_cap():
    limiter = SlidingWindowLimiter(window_seconds=60, max_requests=10, max_external=2)
    assert limiter.allow("a", external=True, now=0)
    assert limiter.allow("a", external=True, now=1)
    assert not limiter.allow("a", external=True, now=2)
    assert limiter.allow("a", external=False, now=2)


def test_limiter_memory_is_hard_bounded_even_with_many_active_clients():
    limiter = SlidingWindowLimiter(max_clients=3, max_requests=10)
    for i in range(20):
        assert limiter.allow(f"client-{i}", now=1)
        assert len(limiter.events) <= 3
    assert len(limiter.events) == 3


def _run_asgi(middleware, scope, messages):
    sent = []
    queue = list(messages)

    async def receive():
        return queue.pop(0) if queue else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(middleware(scope, receive, send))
    return sent


def _echo_app():
    async def app_(scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == "http.request" and not message.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})
    return app_


def test_body_limit_rejects_streamed_body_without_content_length():
    middleware = BodySizeLimitMiddleware(_echo_app(), max_bytes=10)
    chunks = [
        {"type": "http.request", "body": b"x" * 6, "more_body": True},
        {"type": "http.request", "body": b"x" * 6, "more_body": False},
    ]
    sent = _run_asgi(middleware, {"type": "http", "headers": []}, chunks)
    assert sent[0]["status"] == 413


def test_body_limit_rejects_declared_oversize_and_invalid_length():
    middleware = BodySizeLimitMiddleware(_echo_app(), max_bytes=10)
    too_big = {"type": "http", "headers": [(b"content-length", b"11")]}
    assert _run_asgi(middleware, too_big, [])[0]["status"] == 413
    invalid = {"type": "http", "headers": [(b"content-length", b"abc")]}
    assert _run_asgi(middleware, invalid, [])[0]["status"] == 400


def test_body_limit_allows_small_bodies():
    middleware = BodySizeLimitMiddleware(_echo_app(), max_bytes=10)
    chunks = [{"type": "http.request", "body": b"hello", "more_body": False}]
    assert _run_asgi(middleware, {"type": "http", "headers": []}, chunks)[0]["status"] == 200


def test_api_rejects_oversized_json_body_with_security_headers():
    response = client.post("/api/analyze", json={"url": "https://example.com/" + "a" * MAX_BODY_BYTES})
    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("url", [
    "https://pineapple.com/",
    "https://snapple.example/",
    "https://applepie.example/",
])
def test_short_brand_does_not_match_inside_unrelated_words(url):
    findings = analyze(url)["findings"]
    assert not any(item["id"].startswith("brand_") for item in findings)


@pytest.mark.parametrize("url", [
    "https://apple-support.example/",
    "https://id-apple.example/",
])
def test_short_brand_matches_hyphen_separated_word(url):
    findings = analyze(url)["findings"]
    assert any(item["id"] == "brand_impersonation_apple" for item in findings)


def test_static_files_work_independently_of_current_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
