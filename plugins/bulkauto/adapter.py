"""Adapter Bulk Video Studio (capability video.bulkauto).

Chỉnh video bằng BỘ CÔNG CỤ của app Bulk Video Studio (reels/logo/intro/outro/nhạc/phụ đề/speed).

MẶC ĐỊNH = DIRECT: Agent **tự nạp lõi điều khiển** (mã core stdlib của BulkAuto — chỉ là cách KẾT
NỐI, KHÔNG sửa app BVS) rồi **tự mở BVS** + lái qua CDP/window.api + render. Không cần chạy web
`:8787` thủ công. (Tuỳ chọn: nếu inputs có `bulkauto_url` thì dùng HTTP tới web BulkAuto.)

Thu file đã chỉnh (output_path) về output_dir của step (thành asset). BVS chỉ chỉnh 1 video/lúc
nên có lock; bận -> TransientError (engine retry). Chỉ stdlib.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from agent.sdk import Adapter, PermanentError, StepContext, TransientError

_DEFAULT_BULKAUTO = r"C:\BulkAuto"
_DEFAULT_URL = "http://127.0.0.1:8787"
_POLL_SECONDS = 3
_LOCK = threading.Lock()  # BVS chỉ chỉnh 1 video tại 1 thời điểm


class _ProgressHandler(logging.Handler):
    """Chuyển log của orchestrator -> step.progress (giữ WS sống + hiện thông báo)."""

    def __init__(self, ctx: StepContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._last = ""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
            if msg and msg != self._last:
                self._ctx.progress(0, msg[:120])
                self._last = msg
        except Exception:  # noqa: BLE001 - log không được làm hỏng render
            pass


def _resolve_source(ctx: StepContext) -> Path:
    source = ctx.inputs.get("source") or ctx.config.get("source")
    if not source:
        raise PermanentError("Thiếu 'source' (video nguồn) để chỉnh bằng BVS")
    p = Path(source)
    full = p if p.is_absolute() else Path(ctx.data_dir) / p
    if not full.is_file():
        raise PermanentError(f"Không tìm thấy video nguồn: {source}")
    return full


class BulkAutoAdapter(Adapter):
    capability = "video.bulkauto"

    def validate_config(self, config: dict) -> None:
        pass

    async def run(self, ctx: StepContext) -> None:
        await asyncio.to_thread(self._run_sync, ctx)

    def _run_sync(self, ctx: StepContext) -> None:
        url = ctx.inputs.get("bulkauto_url") or ctx.config.get("bulkauto_url")
        if url:
            self._run_http(ctx, str(url).rstrip("/"))
        else:
            self._run_direct(ctx)

    # ---------------------------------------------------------------- DIRECT
    def _run_direct(self, ctx: StepContext) -> None:
        full = _resolve_source(ctx)
        bulk = ctx.inputs.get("bulkauto_path") or ctx.config.get("bulkauto_path") or _DEFAULT_BULKAUTO
        if not (Path(bulk) / "automation").is_dir():
            raise PermanentError(
                f"Không thấy lõi BulkAuto ở {bulk} "
                "(clone github.com/TranQA28/bulk-video-studio-automation về đây)"
            )
        if not _LOCK.acquire(timeout=5):
            raise TransientError("BVS đang bận (1 video/lúc) — sẽ thử lại sau")
        try:
            if bulk not in sys.path:
                sys.path.insert(0, bulk)
            from automation.config import Config
            from automation.workflow.affiliate_reels import AffiliateReelsOrchestrator

            tmp_in = ctx.output_dir / "_bvs_input"
            tmp_in.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full, tmp_in / full.name)

            cfg = Config.load()
            for k, v in (ctx.inputs.get("bvs_config") or {}).items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)

            logger = logging.getLogger(f"bvs.{ctx.step_id}")
            logger.setLevel(logging.INFO)
            logger.propagate = False
            handler = _ProgressHandler(ctx)
            logger.addHandler(handler)
            orch = AffiliateReelsOrchestrator(cfg, logger=logger)
            try:
                orch.prepare(backup=True)  # tự MỞ BVS + kết nối CDP
                videos = orch.scan(str(tmp_in))
                if not videos:
                    raise PermanentError("BVS: không thấy video trong thư mục input tạm")
                results = orch.run_all(videos)
            finally:
                try:
                    orch.close()
                except Exception:  # noqa: BLE001
                    pass
                logger.removeHandler(handler)

            done = [
                r for r in results
                if r.status == "completed" and r.output_path and Path(r.output_path).is_file()
            ]
            if not done:
                err = next((getattr(r, "error", None) for r in results if getattr(r, "error", None)), "không rõ")
                raise PermanentError(f"BVS chỉnh lỗi: {err}")
            out = done[0].output_path
            shutil.copy2(out, ctx.output_dir / f"bvs_{Path(out).name}")
            shutil.rmtree(tmp_in, ignore_errors=True)
        finally:
            _LOCK.release()

    # ------------------------------------------------------------------ HTTP
    def _run_http(self, ctx: StepContext, base: str) -> None:
        full = _resolve_source(ctx)
        try:
            _get(f"{base}/api/health", timeout=8)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise TransientError(
                f"Chưa kết nối được BulkAuto web ở {base} (mở web.py): {type(e).__name__}"
            ) from None
        bvs_config = ctx.inputs.get("bvs_config") or {}
        if bvs_config:
            _post(f"{base}/api/config", bvs_config)
        tmp_in = ctx.output_dir / "_bvs_input"
        tmp_in.mkdir(parents=True, exist_ok=True)
        shutil.copy2(full, tmp_in / full.name)
        res = _post(f"{base}/api/run", {"input_dir": str(tmp_in)})
        if isinstance(res, dict) and res.get("ok") is False:
            err = str(res.get("error", ""))
            if "đang chạy" in err.lower() or "running" in err.lower():
                raise TransientError(f"BulkAuto đang bận (sẽ thử lại): {err}")
            raise PermanentError(f"BulkAuto từ chối chạy: {err}")
        deadline = time.time() + max(ctx.timeout - 5, 30)
        status, snap, last = "running", {}, ""
        while time.time() < deadline:
            try:
                snap = _get(f"{base}/api/status", timeout=10)
            except (urllib.error.URLError, OSError):
                time.sleep(_POLL_SECONDS)
                continue
            status = str(snap.get("status", ""))
            msg = str(snap.get("message", ""))
            if msg and msg != last:
                ctx.progress(_as_pct(snap.get("progress")), msg[:120])
                last = msg
            if status in ("done", "stopped", "error"):
                break
            time.sleep(_POLL_SECONDS)
        if status == "error":
            raise PermanentError(f"BVS chỉnh lỗi: {snap.get('message', 'không rõ')}")
        out = next(
            (r.get("output") for r in (snap.get("results") or [])
             if r.get("status") == "completed" and r.get("output")),
            None,
        )
        if not out or not Path(out).is_file():
            raise PermanentError("BVS không tạo được video đã chỉnh")
        shutil.copy2(out, ctx.output_dir / f"bvs_{Path(out).name}")
        shutil.rmtree(tmp_in, ignore_errors=True)


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


def _as_pct(prog: object) -> int:
    if isinstance(prog, dict):
        if prog.get("pct") is not None:
            return int(prog["pct"])
        total = prog.get("total") or 0
        return int(prog.get("index", 0) / total * 100) if total else 0
    if isinstance(prog, (int, float)):
        return int(prog)
    return 0
