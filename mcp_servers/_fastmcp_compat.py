"""Fallback helpers for fastmcp so backend imports keep working.

The MCP servers use fastmcp when available (for stdio integration), but the
FastAPI backend only needs the plain coroutine functions. Some environments
may not ship fastmcp or may provide a build where `MCP` is exposed under a
different name. This module tries the real import first and otherwise exposes
no-op stand-ins that preserve the decorator semantics used in the servers.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

FASTMCP_AVAILABLE = True

try:
    from fastmcp import MCP, tool  # type: ignore
except Exception:  # pragma: no cover - executes only when fastmcp missing/broken
    FASTMCP_AVAILABLE = False

    _F = TypeVar("_F", bound=Callable[..., Any])

    def _identity(func: _F) -> _F:
        return func

    class MCP:  # type: ignore
        """Minimal stub to keep @app.tool decorators operational."""

        def __init__(self, name: str):
            self.name = name

        def tool(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            if args and callable(args[0]) and not kwargs:
                return args[0]  # decorator used without params
            return _identity

        def run_stdio(self) -> None:
            raise RuntimeError("fastmcp is not installed; stdio mode unavailable")

    def tool(*args: Any, **kwargs: Any):  # type: ignore
        if args and callable(args[0]) and not kwargs:
            return args[0]
        return _identity

