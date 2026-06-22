"""Ghi/đọc asset theo thư mục chuẩn (SPEC 07). Asset kèm checksum sha256."""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path


def step_output_dir(data_dir: str, job_id: str, step_id: str) -> Path:
    path = Path(data_dir) / "jobs" / job_id / "steps" / step_id / "outputs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def collect_assets(data_dir: str, out_dir: Path) -> list[dict]:
    base = Path(data_dir)
    assets: list[dict] = []
    for f in sorted(out_dir.rglob("*")):
        if not f.is_file():
            continue
        content = f.read_bytes()
        assets.append(
            {
                "kind": "other",
                "path": str(f.relative_to(base)).replace("\\", "/"),
                "mime": mimetypes.guess_type(f.name)[0],
                "size": len(content),
                "checksum": hashlib.sha256(content).hexdigest(),
            }
        )
    return assets
