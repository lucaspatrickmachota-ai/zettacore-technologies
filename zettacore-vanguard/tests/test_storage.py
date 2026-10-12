from pathlib import Path

import pytest

from vanguard.storage import AssetStore


def test_add_and_list_asset(tmp_path: Path) -> None:
    store = AssetStore(tmp_path / "test.sqlite3")
    asset_id = store.add_asset(
        "Lab server",
        "Server",
        environment="lab",
        owner="IT",
        authorization_note="Owned test machine",
    )

    assets = store.list_assets()

    assert len(assets) == 1
    assert assets[0]["id"] == asset_id
    assert assets[0]["name"] == "Lab server"
    assert assets[0]["authorization_note"] == "Owned test machine"


def test_asset_name_is_required(tmp_path: Path) -> None:
    store = AssetStore(tmp_path / "test.sqlite3")

    with pytest.raises(ValueError, match="Asset name is required"):
        store.add_asset("   ", "Server")


def test_delete_asset(tmp_path: Path) -> None:
    store = AssetStore(tmp_path / "test.sqlite3")
    asset_id = store.add_asset("Lab workstation", "Workstation")

    assert store.delete_asset(asset_id) is True
    assert store.list_assets() == []
    assert store.delete_asset(asset_id) is False
