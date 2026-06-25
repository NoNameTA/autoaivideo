"""Suy ra OUTPUT PATH (đường dẫn video sau khi tải/Export) từ Asset — KHÔNG upload, KHÔNG URL.

Asset.path lưu TƯƠNG ĐỐI data_dir của Agent (vd `jobs/<id>/steps/<id>/outputs/video.mp4`).
- Nếu job có `dest_folder` (Backend đã nhúng từ Output Folders → Plugin đã copy file đích vào đó):
  Output Folder = dest_folder, Output Path = dest_folder/<tên file>.
- Nếu không: Output Path = đường dẫn TUYỆT ĐỐI thật trên máy = data_dir/asset.path.

Trả về dạng đường dẫn Windows (giữ dấu `\\`) để hiển thị/ghi Sheet đúng máy.
"""
from __future__ import annotations

import os

from app.core.config import get_settings
from app.models.asset import Asset

_VIDEO_EXT = (".mp4", ".webm", ".mkv", ".mov", ".m4v")


def pick_video_asset(assets: list[Asset]) -> Asset | None:
    """Chọn asset video lớn nhất (bỏ audio-only/file rác)."""
    vids = [
        a for a in assets
        if a.path and a.path.lower().endswith(_VIDEO_EXT) and (a.size or 0) > 0
    ]
    if vids:
        return max(vids, key=lambda a: a.size or 0)
    # Fallback: asset lớn nhất có path (nếu không nhận diện được đuôi video).
    withp = [a for a in assets if a.path]
    return max(withp, key=lambda a: a.size or 0) if withp else None


def resolve(asset_path: str, dest_folder: str | None = None) -> dict:
    """Trả {output_path, output_folder, output_filename} cho 1 asset path tương đối."""
    rel = (asset_path or "").replace("\\", "/")
    filename = rel.rsplit("/", 1)[-1] if rel else ""
    if dest_folder:
        folder = str(dest_folder).rstrip("/\\")
        full = os.path.join(folder, filename) if filename else folder
        return {
            "output_path": os.path.normpath(full),
            "output_folder": os.path.normpath(folder),
            "output_filename": filename,
        }
    base = get_settings().data_dir
    full = os.path.normpath(os.path.join(base, rel)) if rel else ""
    folder = os.path.dirname(full)
    return {"output_path": full, "output_folder": folder, "output_filename": filename}


def from_assets(assets: list[Asset], dest_folder: str | None = None) -> dict | None:
    """Suy Output Path từ danh sách asset của job. None nếu không có asset hợp lệ."""
    a = pick_video_asset(assets)
    if a is None:
        return None
    return resolve(a.path, dest_folder)
