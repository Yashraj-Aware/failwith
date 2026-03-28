"""
Suggestion model and handler registry.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Dict, List, Optional, Type


@dataclasses.dataclass
class Suggestion:
    """An actionable fix suggestion for a Python error."""

    title: str
    fixes: List[str]
    env_info: Optional[List[str]] = None
    docs_url: Optional[str] = None

    def __bool__(self):
        return bool(self.fixes)


# Type alias for suggestion handler functions
SuggestionHandler = Callable[
    [Type[BaseException], BaseException, Any, dict],
    Optional[Suggestion],
]

# Registry: exception type -> list of handler functions
_handlers: Dict[Type[BaseException], List[SuggestionHandler]] = {}

# Custom user-registered handlers (highest priority)
_custom_handlers: Dict[Type[BaseException], List[SuggestionHandler]] = {}


def register(exc_type: Type[BaseException]):
    """
    Decorator to register a custom suggestion handler for an exception type.

    Usage:
        @failwith.register(MyDatabaseError)
        def handle_db_error(exc_type, exc_value, exc_tb, config):
            return failwith.Suggestion(
                title="Database connection failed",
                fixes=["Check DATABASE_URL in .env"],
            )
    """
    def decorator(func: SuggestionHandler) -> SuggestionHandler:
        if exc_type not in _custom_handlers:
            _custom_handlers[exc_type] = []
        _custom_handlers[exc_type].append(func)
        return func
    return decorator


def register_builtin(exc_type: Type[BaseException], handler: SuggestionHandler) -> None:
    """Register a built-in suggestion handler (internal use)."""
    if exc_type not in _handlers:
        _handlers[exc_type] = []
    _handlers[exc_type].append(handler)


def get_handlers(exc_type: Type[BaseException]) -> List[SuggestionHandler]:
    """
    Get all handlers for an exception type, checking MRO for inheritance.

    Custom handlers are checked first, then built-in handlers.
    Walks the MRO so a handler for OSError also catches ConnectionRefusedError.
    """
    handlers = []

    # Check custom handlers first (user-registered, highest priority)
    for cls in exc_type.__mro__:
        if cls in _custom_handlers:
            handlers.extend(_custom_handlers[cls])

    # Then built-in handlers
    for cls in exc_type.__mro__:
        if cls in _handlers:
            handlers.extend(_handlers[cls])

    return handlers
