"""Output Path (KHÔNG upload, KHÔNG URL) — resolve từ asset + Output Folders settings."""
from __future__ import annotations

import os

from app.models.asset import Asset
from app.services import output_path as op
from app.services.output_settings import OutputSettings


def test_resolve_with_dest_folder() -> None:
    """Có dest_folder (Plugin đã copy vào Output Folder) → Output Path = dest_folder/<file>."""
    dest = r"C:\Users\PC\Videos\video da sua"
    info = op.resolve("jobs/j1/steps/s1/outputs/video001.mp4", dest_folder=dest)
    assert info["output_filename"] == "video001.mp4"
    assert info["output_folder"] == os.path.normpath(dest)
    assert info["output_path"] == os.path.normpath(dest + r"\video001.mp4")
    assert "http" not in info["output_path"].lower()  # KHÔNG URL


def test_resolve_fallback_to_data_dir() -> None:
    """Không dest_folder → Output Path tuyệt đối từ data_dir + asset.path (đường dẫn thật)."""
    info = op.resolve("jobs/j1/steps/s1/outputs/clip.mp4", dest_folder=None)
    assert info["output_filename"] == "clip.mp4"
    assert info["output_path"].endswith(os.path.normpath("jobs/j1/steps/s1/outputs/clip.mp4"))


def test_pick_video_asset_largest() -> None:
    """Chọn asset video lớn nhất, bỏ audio/file rác."""
    assets = [
        Asset(job_id="j", path="a/audio.m4a", size=100),
        Asset(job_id="j", path="a/small.mp4", size=10),
        Asset(job_id="j", path="a/big.mp4", size=999),
    ]
    a = op.pick_video_asset(assets)
    assert a is not None and a.path == "a/big.mp4"


def test_from_assets_none_when_empty() -> None:
    assert op.from_assets([], None) is None


def test_folder_settings_defaults(tmp_path, monkeypatch) -> None:
    """Output Folders mặc định + lưu/đọc round-trip qua JSON (không đụng DB)."""
    from app.core import config

    settings = config.get_settings()
    monkeypatch.setattr(settings, "data_dir", str(tmp_path))
    cfg = OutputSettings.load()
    assert cfg["download_folder"] and cfg["export_folder"] and cfg["temp_folder"]
    saved = OutputSettings.save(
        {"download_folder": r"D:\dl", "export_folder": "", "temp_folder": r"D:\tmp"}
    )
    assert saved["download_folder"] == r"D:\dl"
    assert saved["export_folder"] == cfg["export_folder"]  # trống = giữ mặc định
    assert OutputSettings.load()["download_folder"] == r"D:\dl"
