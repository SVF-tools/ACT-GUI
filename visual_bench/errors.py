"""Application errors shared by every module's services and routes.

Services raise AppError; server.py renders it as an ErrorResponse with the given HTTP status.
"""
from __future__ import annotations

from engine_bridge.contracts import BridgeError


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.retryable = status, code, message, retryable


def bridge_error(err: BridgeError, status: int = 422) -> AppError:
    return AppError(status, err.code, err.message, err.retryable)
