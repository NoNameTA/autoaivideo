"""Adapter Bulk Video Studio (capability video.bulkauto).

Chỉnh video bằng BỘ CÔNG CỤ của app Bulk Video Studio — KHÔNG lái app trực tiếp ở đây, mà gọi
HTTP sang **agent BulkAuto** (https://github.com/TranQA28/bulk-video-studio-automation) đang chạy
local (mặc định http://127.0.0.1:8787). BulkAuto lái BVS qua CDP/window.api + render bằng ffmpeg.

Luồng: copy video nguồn -> thư mục input tạm -> POST /api/run -> poll /api/status tới khi xong ->
thu file đã chỉnh (results[].output) về output_dir của step. Chỉ dùng stdlib (urllib) — không thêm dep.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

from agent.sdk import Adapter, PermanentError, StepContext, TransientError

_DEFAULT_URL = "http://127.0.0.1:8787"
_POLL_SECONDS = 3


def _as_pct(prog: object) -> int:
    """BulkAuto trả progress dạng dict {index,total,video,pct} hoặc số -> ép về int %% an toàn."""
    if isinstance(prog, dict):
        if prog.get("pct") is not None:
            return int(prog["pct"])
        total = prog.get("total") or 0
        return int(prog.get("index", 0) / total * 100) if total else 0
    if isinstance(prog, (int, float)):
        return int(prog)
    return 0


def _get(url: str, timeout: int = 15) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 - localhost
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, body: dict, timeout: int = 30) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - localhost
        return json.loads(resp.read().decode("utf-8"))


class BulkAutoAdapter(Adapter):
    capability = "video.bulkauto"

    def validate_config(self, config: dict) -> None:
        pass  # source/url đến từ inputs lúc chạy

    async def run(self, ctx: StepContext) -> None:
        await asyncio.to_thread(self._run_sync, ctx)

    def _run_sync(self, ctx: StepContext) -> None:
        base = (ctx.inputs.get("bulkauto_url") or ctx.config.get("bulkauto_url") or _DEFAULT_URL).rstrip("/")
        source = ctx.inputs.get("source") or ctx.config.get("source")
        if not source:
            raise PermanentError("Thiếu 'source' (video nguồn) để chỉnh bằng BVS")
        src = Path(source)
        full = src if src.is_absolute() else Path(ctx.data_dir) / src
        if not full.is_file():
            raise PermanentError(f"Không tìm thấy video nguồn: {source}")

        # 1) BulkAuto phải đang chạy.
        try:
            _get(f"{base}/api/health", timeout=8)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise TransientError(
                f"Chưa kết nối được Bulk Video Studio agent ở {base} "
                f"(mở 'web.py' hoặc BulkAutoStudio.exe rồi thử lại): {type(e).__name__}"
            ) from None

        # 2) (tuỳ chọn) cấu hình bộ chỉnh (logo/intro/outro/nhạc/speed/phụ đề) qua /api/config.
        bvs_config = ctx.inputs.get("bvs_config") or ctx.config.get("bvs_config") or {}
        if bvs_config:
            try:
                _post(f"{base}/api/config", bvs_config)
            except (urllib.error.URLError, OSError) as e:  # noqa: BLE001
                raise PermanentError(f"Cấu hình BVS lỗi: {type(e).__name__}") from None

        # 3) Thư mục input tạm chỉ chứa 1 video -> tránh BVS xử lý nhầm file khác.
        tmp_in = ctx.output_dir / "_bvs_input"
        tmp_in.mkdir(parents=True, exist_ok=True)
        shutil.copy2(full, tmp_in / full.name)

        # 4) Chạy.
        try:
            res = _post(f"{base}/api/run", {"input_dir": str(tmp_in)})
        except (urllib.error.URLError, OSError) as e:
            raise TransientError(f"Gọi /api/run lỗi: {type(e).__name__}") from None
        if isinstance(res, dict) and res.get("ok") is False:
            err = str(res.get("error", ""))
            # BVS chỉ chạy 1 video/lúc — bận thì RETRY (TransientError) chứ không fail hẳn.
            if "đang chạy" in err.lower() or "running" in err.lower():
                raise TransientError(f"BulkAuto đang bận (sẽ thử lại): {err}")
            raise PermanentError(f"BulkAuto từ chối chạy: {err}")

        # 5) Poll status tới khi xong (giới hạn theo timeout của step).
        deadline = time.time() + max(ctx.timeout - 5, 30)
        status = "running"
        snap: dict = {}
        last_msg = ""
        while time.time() < deadline:
            try:
                snap = _get(f"{base}/api/status", timeout=10)
            except (urllib.error.URLError, OSError):
                time.sleep(_POLL_SECONDS)
                continue
            status = str(snap.get("status", ""))
            msg = str(snap.get("message", ""))
            if msg and msg != last_msg:
                ctx.progress(_as_pct(snap.get("progress")), msg[:120])
                last_msg = msg
            if status in ("done", "stopped", "error"):
                break
            time.sleep(_POLL_SECONDS)

        if status == "error":
            raise PermanentError(f"BVS chỉnh lỗi: {snap.get('message', 'không rõ')}")

        # 6) Thu file đã chỉnh từ results -> output_dir của step (thành asset).
        results = snap.get("results") or []
        out_path = next(
            (r.get("output") for r in results if r.get("status") == "completed" and r.get("output")),
            None,
        )
        if not out_path or not Path(out_path).is_file():
            raise PermanentError("BVS không tạo được video đã chỉnh (kiểm tra cấu hình BVS/ffmpeg)")
        shutil.copy2(out_path, ctx.output_dir / f"bvs_{Path(out_path).name}")
        shutil.rmtree(tmp_in, ignore_errors=True)
