"""Media Check (ffprobe sau Download) — test phần thuần (không cần ffmpeg)."""
from __future__ import annotations

from app.models.asset import Asset
from app.services import media_check as mc


def test_probe_missing_file_invalid() -> None:
    assert mc.probe("") == mc.INVALID
    assert mc.probe(r"C:\khong\ton\tai\abc.mp4") == mc.INVALID


def test_probe_zero_byte_invalid(tmp_path) -> None:
    f = tmp_path / "empty.mp4"
    f.write_bytes(b"")
    assert mc.probe(str(f)) == mc.INVALID


def test_constants() -> None:
    assert (mc.VIDEO, mc.AUDIO_ONLY, mc.INVALID) == ("video", "audio_only", "invalid")


def test_pick_asset_prefers_video_ext_largest() -> None:
    assets = [
        Asset(job_id="j", path="a/audio.m4a", size=500),
        Asset(job_id="j", path="a/clip.mp4", size=10),
        Asset(job_id="j", path="a/big.mp4", size=999),
    ]
    a = mc.pick_asset(assets)
    assert a is not None and a.path == "a/big.mp4"


def test_pick_asset_none_when_empty() -> None:
    assert mc.pick_asset([]) is None
    assert mc.pick_asset([Asset(job_id="j", path="", size=0)]) is None


def test_resolve_asset_path_absolute() -> None:
    import os

    out = mc.resolve_asset_path("jobs/j1/steps/s1/outputs/v.mp4")
    assert os.path.isabs(out)
    assert out.endswith(os.path.normpath("jobs/j1/steps/s1/outputs/v.mp4"))
