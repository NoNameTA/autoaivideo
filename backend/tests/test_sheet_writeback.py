"""Test helper thuần của write-back (không I/O mạng)."""
from __future__ import annotations

from app.cloud.google_sheets import _col_letter, _q
from app.services.sheet_writeback import WRITEBACK_COLUMNS, _fmt_duration


def test_col_letter() -> None:
    assert _col_letter(0) == "A"
    assert _col_letter(25) == "Z"
    assert _col_letter(26) == "AA"
    assert _col_letter(27) == "AB"
    assert _col_letter(51) == "AZ"


def test_q_quotes_worksheet() -> None:
    assert _q(None, "A1") == "A1"
    assert _q("Trang tính1", "A1:Z1") == "'Trang tính1'!A1:Z1"
    assert _q("It's", "A1") == "'It''s'!A1"  # quote escape


def test_fmt_duration() -> None:
    assert _fmt_duration(None) == ""
    assert _fmt_duration(0) == ""
    assert _fmt_duration(1500) == "1.5s"
    assert _fmt_duration(65000) == "1m05s"


def test_writeback_columns_contract() -> None:
    # KHÔNG upload → Output Path/Filename, KHÔNG Output URL; có Media Type (ffprobe sau Download).
    assert WRITEBACK_COLUMNS == [
        "Status",
        "Media Type",
        "Output Path",
        "Output Filename",
        "Completed Time",
        "Duration",
        "Error",
    ]
    assert "Output URL" not in WRITEBACK_COLUMNS
