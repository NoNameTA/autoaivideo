"""Enum trạng thái dùng chung cho ORM + schema (SPEC 02 §3, 10)."""

from __future__ import annotations

from enum import StrEnum


class BatchStatus(StrEnum):
    created = "created"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StepStatus(StrEnum):
    queued = "queued"
    assigned = "assigned"
    running = "running"
    completed = "completed"
    failed = "failed"
    retrying = "retrying"
    cancelled = "cancelled"


class AgentStatus(StrEnum):
    online = "online"
    offline = "offline"
    busy = "busy"


class AssetKind(StrEnum):
    script = "script"
    audio = "audio"
    image = "image"
    subtitle = "subtitle"
    video = "video"
    export = "export"
    screenshot = "screenshot"
    other = "other"


class QueueState(StrEnum):
    pending = "pending"
    leased = "leased"
    done = "done"
