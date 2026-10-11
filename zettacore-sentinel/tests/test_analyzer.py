import pytest
from fastapi.testclient import TestClient

from app.main import analyze, app, normalize_url

client = TestClient(app)


def test_normalizes_host_and_does_not_return_path_or_query():
    assert normalize_url("Example.COM/path?token=SECRET") == "https://example.com/"
    result = analyze("https://example.com/path?token=SECRET")
    assert "SECRET" not in str(result)
    assert result["hostname"] == "example.com"


def test_http_is_signal_not_automatic_phishing_verdict():
    result = analyze("http://example.com")
    assert any(item["id"] == "http" for item in result["findings"])
    assert result["risk"] == "low"


def test_userinfo_is_flagged():
    assert any(item["id"] == "userinfo" for item in analyze("https://paypal.com@evil.example/login")["findings"])


def test_genuine_official_subdomain_not_flagged_as_brand_impersonation():
    result = analyze("https://login.microsoft.com")
    assert not any(item["id"].startswith("brand_") for item in result["findings"])


def test_brand_in_unrelated_domain_is_flagged():
    assert any(item["id"] == "brand_impersonation_microsoft" for item in analyze("https://microsoft-login.example")["findings"])


def test_common_digit_lookalike_is_flagged():
    assert any(item["id"] == "brand_typo_microsoft" for item in analyze("https://micros0ft-login.com")["findings"])


def test_local_ip_is_flagged_without_being_visited():
    result = analyze("http://127.0.0.1:8000/admin")
    assert any(item["id"] == "nonpublic_ip" for item in result["findings"])
    assert result["target_fetched"] is False


@pytest.mark.parametrize("value", [
    "javascript:alert(1)",
    "data:text/html,hi",
    "https://example.com\\@evil.example",
    "https://exa mple.com",
    "https://example.com:99999",
])
def test_rejects_ambiguous_or_unsupported_urls(value):
    with pytest.raises(ValueError):
        normalize_url(value)


def test_no_signals_are_labelled_unverified_not_safe():
    result = analyze("https://example.org")
    assert result["risk"] == "unverified"
    assert "no verificado" in result["risk_label"].lower()


def test_api_emits_security_headers():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert "'unsafe-inline'" not in response.headers["content-security-policy"]
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_api_returns_validation_error_for_bad_scheme():
    response = client.post("/api/analyze", json={"url": "javascript:alert(1)"})
    assert response.status_code == 422


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.3.0"



def test_external_lookup_is_not_requested_without_explicit_consent():
    response = client.post("/api/analyze", json={"url": "https://example.com/path?token=SECRET"})
    data = response.json()
    assert data["external_intelligence"]["status"] == "not_requested"
    assert data["external_reputation_checked"] is False
    assert "SECRET" not in response.text


def test_external_match_is_explained_without_echoing_full_url(monkeypatch):
    async def fake_lookup(url):
        assert url == "https://example.com/path?token=SECRET"
        return {
            "provider": "URLhaus",
            "status": "listed",
            "checked": True,
            "summary": "Matched listing",
            "url_status": "online",
        }

    monkeypatch.setattr("app.main.lookup_urlhaus", fake_lookup)
    response = client.post("/api/analyze", json={
        "url": "https://example.com/path?token=SECRET",
        "external_lookup_consent": True,
    })
    data = response.json()
    assert response.status_code == 200
    assert data["risk"] == "high"
    assert any(item["id"] == "external_urlhaus_match" for item in data["findings"])
    assert "SECRET" not in response.text


def test_external_lookup_skips_urls_with_userinfo(monkeypatch):
    async def should_not_run(_url):
        raise AssertionError("Sensitive URL must not be shared externally")

    monkeypatch.setattr("app.main.lookup_urlhaus", should_not_run)
    response = client.post("/api/analyze", json={
        "url": "https://user:secret@example.com/private",
        "external_lookup_consent": True,
    })
    data = response.json()
    assert response.status_code == 200
    assert data["external_intelligence"]["status"] == "skipped_sensitive_url"
    assert "secret" not in response.text



def test_urlhaus_adapter_is_gated_by_server_configuration(monkeypatch):
    from app.intel import lookup_urlhaus

    monkeypatch.delenv("URLHAUS_AUTH_KEY", raising=False)
    result = client.post("/api/analyze", json={
        "url": "https://example.com/path",
        "external_lookup_consent": True,
    }).json()
    assert result["external_intelligence"]["status"] == "not_configured"
    assert result["external_reputation_checked"] is False
