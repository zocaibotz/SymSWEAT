from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolStatus(str, Enum):
    success = "success"
    retryable_error = "retryable_error"
    fatal_error = "fatal_error"


class ToolError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ToolResult(BaseModel):
    status: ToolStatus
    summary: str = ""
    artifacts: Dict[str, str] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    errors: List[ToolError] = Field(default_factory=list)


def ok(summary: str = "", **kwargs: Any) -> ToolResult:
    return ToolResult(status=ToolStatus.success, summary=summary, **kwargs)


def retryable_error(code: str, message: str, summary: str = "") -> ToolResult:
    return ToolResult(
        status=ToolStatus.retryable_error,
        summary=summary or message,
        errors=[ToolError(code=code, message=message, retryable=True)],
    )


def fatal_error(code: str, message: str, summary: str = "") -> ToolResult:
    return ToolResult(
        status=ToolStatus.fatal_error,
        summary=summary or message,
        errors=[ToolError(code=code, message=message, retryable=False)],
    )
