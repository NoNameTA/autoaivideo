"""Test cơ bản cho CDP/UIA driver (SPEC 05 §4) — không cần browser/desktop, chạy được trên CI."""

from __future__ import annotations

from agent.drivers.cdp import CdpDriver, find_browser
from agent.drivers.uia import UiaDriver


def test_find_browser_override() -> None:
    assert find_browser("chrome", "C:/x/chrome.exe") == "C:/x/chrome.exe"
    assert find_browser("edge", "C:/x/msedge.exe") == "C:/x/msedge.exe"


def test_find_browser_no_crash() -> None:
    result = find_browser("edge")
    assert result is None or isinstance(result, str)


def test_drivers_instantiate() -> None:
    assert CdpDriver("chrome.exe") is not None
    assert UiaDriver() is not None
