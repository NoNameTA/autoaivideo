"""Entry Desktop Agent (SPEC 05). Kết nối backend qua WS và thực thi step bằng adapter thật."""

from __future__ import annotations

import asyncio
import logging
import sys

from agent import __version__
from agent.config import get_agent_settings
from agent.connection import run_agent

reconfigure = getattr(sys.stdout, "reconfigure", None)
if callable(reconfigure):
    reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("agent")


def main() -> None:
    settings = get_agent_settings()
    log.info("AI Video Agent v%s -> %s", __version__, settings.backend_ws_url)
    try:
        asyncio.run(run_agent(settings))
    except KeyboardInterrupt:
        log.info("Agent dừng.")


if __name__ == "__main__":
    main()
