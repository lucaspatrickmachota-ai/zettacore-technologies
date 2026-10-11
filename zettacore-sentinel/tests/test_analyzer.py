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


def test_api_returns_validation_error_for_bad_scheme():
    response = client.post("/api/analyze", json={"url": "javascript:alert(1)"})
    assert response.status_code == 422


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.2.0"
