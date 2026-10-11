import pytest
from app.main import analyze, normalize_url

def test_normalizes_host_and_adds_scheme():
    assert normalize_url("Example.COM") == "https://example.com/"

def test_flags_http():
    assert any("HTTPS" in x["title"] for x in analyze("http://example.com")["findings"])

def test_flags_userinfo():
    assert any("Credenciales" in x["title"] for x in analyze("https://paypal.com@evil.example/login")["findings"])

def test_rejects_unsupported_scheme():
    with pytest.raises(ValueError): normalize_url("javascript:alert(1)")

def test_discloses_no_network_fetch():
    assert any("No se ha abierto" in x for x in analyze("https://example.com")["limitations"])
