"""Cookie Manager (đa nền tảng) — Backend quản lý METADATA, KHÔNG đọc/lưu nội dung cookie.

Cấu hình lưu ở 1 file JSON `<cookie_dir>/cookies.config.json` (cookie_dir mặc định
`C:\\AIVideoPlatform\\.secrets`, đổi được). Mỗi nền tảng: {name, hosts[], cookie_file}.
Plugin tự chọn cookie theo host URL (config-driven, không hard-code).

BẢO MẬT: KHÔNG bao giờ trả/ghi/log NỘI DUNG cookie. `test()` chỉ đọc file để suy STATUS
(tồn tại/quyền/hết hạn theo timestamp Netscape) rồi trả status — không lộ giá trị cookie.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_DEFAULT_DIR = r"C:\AIVideoPlatform\.secrets"
_CONFIG_NAME = "cookies.config.json"

# Nền tảng mặc định (mở rộng: thêm dòng ở đây HOẶC người dùng tự thêm trên web — không sửa plugin).
_DEFAULT_PLATFORMS = [
    {"name": "TikTok", "hosts": ["tiktok.com"], "cookie_file": "tiktok.cookies.txt"},
    {
        "name": "Facebook",
        "hosts": ["facebook.com", "fb.watch"],
        "cookie_file": "facebook.cookies.txt",
    },
    {"name": "YouTube", "hosts": ["youtube.com", "youtu.be"], "cookie_file": "youtube.cookies.txt"},
    {"name": "Instagram", "hosts": ["instagram.com"], "cookie_file": "instagram.cookies.txt"},
    {"name": "X (Twitter)", "hosts": ["x.com", "twitter.com"], "cookie_file": "x.cookies.txt"},
]


def _default_config() -> dict:
    return {"enabled": False, "cookie_dir": _DEFAULT_DIR, "platforms": _DEFAULT_PLATFORMS}


class CookieService:
    @staticmethod
    def _config_path(cookie_dir: str | None = None) -> Path:
        d = cookie_dir or _DEFAULT_DIR
        return Path(d) / _CONFIG_NAME

    @staticmethod
    def load() -> dict:
        """Đọc config (metadata). Tự dùng default nếu chưa có. Không đọc nội dung cookie."""
        # Tìm config ở thư mục mặc định trước; nếu có 'cookie_dir' khác thì tôn trọng.
        path = CookieService._config_path()
        cfg = _default_config()
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for k in ("enabled", "cookie_dir", "platforms"):
                    if k in data:
                        cfg[k] = data[k]
            except (json.JSONDecodeError, OSError):
                pass
        return cfg

    @staticmethod
    def save(cfg: dict) -> dict:
        """Lưu config vào <cookie_dir>/cookies.config.json. Chỉ metadata, KHÔNG nội dung cookie."""
        cookie_dir = (cfg.get("cookie_dir") or _DEFAULT_DIR).strip()
        Path(cookie_dir).mkdir(parents=True, exist_ok=True)
        out = {
            "enabled": bool(cfg.get("enabled")),
            "cookie_dir": cookie_dir,
            "platforms": [
                {
                    "name": str(p.get("name", "")).strip(),
                    "hosts": [
                        str(h).strip().lower() for h in (p.get("hosts") or []) if str(h).strip()
                    ],
                    "cookie_file": str(p.get("cookie_file", "")).strip(),
                }
                for p in (cfg.get("platforms") or [])
                if str(p.get("name", "")).strip()
            ],
        }
        CookieService._config_path(cookie_dir).write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return out

    @staticmethod
    def _resolve(cookie_dir: str, cookie_file: str) -> Path | None:
        if not cookie_file:
            return None
        p = Path(cookie_file)
        return p if p.is_absolute() else Path(cookie_dir) / p

    @staticmethod
    def list_cookie_files(cookie_dir: str | None = None) -> list[str]:
        """Liệt kê *tên file* .txt trong cookie_dir (cho nút Browse) — KHÔNG đọc nội dung."""
        d = Path(cookie_dir or CookieService.load().get("cookie_dir") or _DEFAULT_DIR)
        if not d.is_dir():
            return []
        return sorted(f.name for f in d.iterdir() if f.is_file() and f.suffix.lower() == ".txt")

    @staticmethod
    def status(cfg: dict | None = None) -> list[dict]:
        """Trạng thái mỗi nền tảng (metadata): exists + last_updated (mtime). KHÔNG đọc nội dung."""
        cfg = cfg or CookieService.load()
        cookie_dir = cfg.get("cookie_dir") or _DEFAULT_DIR
        out = []
        for p in cfg.get("platforms", []):
            full = CookieService._resolve(cookie_dir, p.get("cookie_file", ""))
            exists = bool(full and full.is_file())
            last = ""
            if exists:
                try:
                    last = time.strftime("%Y-%m-%d %H:%M", time.localtime(full.stat().st_mtime))
                except OSError:
                    last = ""
            out.append({**p, "status": "loaded" if exists else "missing", "last_updated": last})
        return out

    @staticmethod
    def _platform(cfg: dict, name: str) -> dict | None:
        return next((p for p in cfg.get("platforms", []) if p.get("name") == name), None)

    @staticmethod
    def test(name: str) -> dict:
        """KIỂM TRA THẬT (status-only): Missing/PermissionDenied/Invalid/Expired/Loaded + expires.

        Đọc file CHỈ để suy hết-hạn theo timestamp Netscape; KHÔNG trả/ghi/log giá trị cookie.
        """
        cfg = CookieService.load()
        p = CookieService._platform(cfg, name)
        if p is None:
            return {"status": "missing", "message": f"Chưa cấu hình nền tảng '{name}'"}
        cookie_dir = cfg.get("cookie_dir") or _DEFAULT_DIR
        full = CookieService._resolve(cookie_dir, p.get("cookie_file", ""))
        if not full or not full.is_file():
            return {"status": "missing", "message": "Chưa có file cookie"}
        if not os.access(full, os.R_OK):
            return {"status": "permission_denied", "message": "Không có quyền đọc file cookie"}
        try:
            text = full.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return {"status": "permission_denied", "message": f"Đọc file lỗi: {type(e).__name__}"}

        now = time.time()
        expiries: list[float] = []
        cookie_lines = 0
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split("\t")
            if len(parts) < 7:
                continue
            cookie_lines += 1
            try:
                exp = float(parts[4])
            except (ValueError, IndexError):
                continue
            if exp > 0:
                expiries.append(exp)
        if cookie_lines == 0:
            return {"status": "invalid", "message": "File không đúng định dạng cookie (Netscape)"}
        future = [e for e in expiries if e > now]
        if expiries and not future:
            soon = time.strftime("%Y-%m-%d", time.localtime(max(expiries)))
            return {"status": "expired", "message": "Cookie đã hết hạn", "expires": soon}
        expires = (
            time.strftime("%Y-%m-%d", time.localtime(min(future))) if future else ""
        )
        return {"status": "loaded", "message": "Cookie hợp lệ", "expires": expires}

    # ----- dùng cho download (nhúng vào job inputs) -----
    @staticmethod
    def platform_of_url(url: str, cfg: dict | None = None) -> dict | None:
        cfg = cfg or CookieService.load()
        host = (url or "").lower()
        for p in cfg.get("platforms", []):
            if any(h and h in host for h in p.get("hosts", [])):
                return p
        return None

    @staticmethod
    def cookie_map() -> dict:
        """Map nhúng job inputs: {enabled, entries:[{hosts, path}]} — path tuyệt đối nếu có file."""
        cfg = CookieService.load()
        if not cfg.get("enabled"):
            return {"enabled": False, "entries": []}
        cookie_dir = cfg.get("cookie_dir") or _DEFAULT_DIR
        entries = []
        for p in cfg.get("platforms", []):
            full = CookieService._resolve(cookie_dir, p.get("cookie_file", ""))
            if full and full.is_file():
                entries.append({"hosts": p.get("hosts", []), "path": str(full)})
        return {"enabled": True, "entries": entries}
