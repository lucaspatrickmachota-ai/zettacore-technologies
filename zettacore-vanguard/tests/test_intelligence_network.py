import json
from io import BytesIO

import pytest

from vanguard import intelligence


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._body = BytesIO(json.dumps(payload).encode("utf-8"))
        self.headers = {"Content-Length": str(len(self._body.getvalue()))}

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)


def test_fetch_cve_uses_configured_nvd_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_urlopen(request, timeout: int):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["user_agent"] = request.get_header("User-agent")
        return FakeResponse({"vulnerabilities": []})

    monkeypatch.setattr(intelligence, "urlopen", fake_urlopen)
    assert intelligence.fetch_cve("cve-2025-12345", timeout=4) == []
    assert seen["url"] == intelligence.NVD_CVE_API + "?cveId=CVE-2025-12345"
    assert seen["timeout"] == 4
    assert "ZettaCore-Vanguard" in str(seen["user_agent"])


def test_rejects_invalid_cve_ids_before_network_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_network(*args, **kwargs):
        raise AssertionError("network should not be called for invalid input")

    monkeypatch.setattr(intelligence, "urlopen", unexpected_network)
    for value in ("", "not-a-cve", "CVE-2025-x", "CVE-2025-12345-extra"):
        with pytest.raises(ValueError, match="CVE identifier"):
            intelligence.fetch_cve(value)


def test_rejects_unconfigured_urls() -> None:
    with pytest.raises(ValueError, match="configured NVD and CISA KEV"):
        intelligence.fetch_json("http://127.0.0.1/private")
