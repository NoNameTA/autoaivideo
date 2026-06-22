"""Dựng message step.assign (SPEC 09 §4)."""

from __future__ import annotations

from app.api.ws.manager import envelope
from app.models.job import Job
from app.models.step import Step


def build_assign(step: Step, job: Job, timeout: int) -> dict:
    return envelope(
        "step.assign",
        {
            "step_id": step.id,
            "job_id": job.id,
            "capability": step.adapter,
            "adapter": step.adapter,
            "inputs": step.inputs,
            "config": step.config,
            "timeout": timeout,
        },
    )
