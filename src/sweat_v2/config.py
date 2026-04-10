from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class V2Flags:
    enabled: bool = False
    shadow_mode: bool = True
    cutover_stage: str = "planning"


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_v2_flags() -> V2Flags:
    return V2Flags(
        enabled=_as_bool(os.getenv("SWEAT_V2_ENABLED"), False),
        shadow_mode=_as_bool(os.getenv("SWEAT_V2_SHADOW_MODE"), True),
        cutover_stage=os.getenv("SWEAT_V2_CUTOVER_STAGE", "planning").strip() or "planning",
    )
