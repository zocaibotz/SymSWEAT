from __future__ import annotations

from typing import Protocol

from src.sweat_v2.state import SweatRunState


class Middleware(Protocol):
    name: str

    def before_stage(self, state: SweatRunState) -> SweatRunState:
        ...

    def before_complete(self, state: SweatRunState) -> SweatRunState:
        ...

    def after_stage(self, state: SweatRunState) -> SweatRunState:
        ...
