"""
Core interceptor — hooks into sys.excepthook to append suggestions to tracebacks.
"""

from __future__ import annotations

import sys
import traceback
import functools
from typing import Any, Callable, Optional, Type

from failwith.core.analyzer import analyze_exception
from failwith.core.formatter import format_suggestion_block


_original_excepthook: Optional[Callable] = None
_config: dict = {}


def install(
    *,
    theme: str = "dark",
    show_locals: bool = False,
    max_suggestions: int = 3,
    include_docs_link: bool = False,
) -> None:
    """
    Install failwith as the global exception hook.

    After calling this, any unhandled exception will have actionable
    fix suggestions appended below the standard traceback.
    """
    global _original_excepthook, _config

    _config = {
        "theme": theme,
        "show_locals": show_locals,
        "max_suggestions": max_suggestions,
        "include_docs_link": include_docs_link,
    }

    if _original_excepthook is None:
        _original_excepthook = sys.excepthook

    sys.excepthook = _failwith_excepthook


def uninstall() -> None:
    """Restore the original exception hook."""
    global _original_excepthook
    if _original_excepthook is not None:
        sys.excepthook = _original_excepthook
        _original_excepthook = None


def _get_config() -> dict:
    """Get the current config, with defaults if not installed."""
    if _config:
        return _config
    return {
        "theme": "dark",
        "show_locals": False,
        "max_suggestions": 3,
        "include_docs_link": False,
    }


def _failwith_excepthook(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
) -> None:
    """Custom excepthook that appends suggestions after the standard traceback."""
    # Print the standard traceback first — never replace it
    if _original_excepthook:
        _original_excepthook(exc_type, exc_value, exc_tb)
    else:
        traceback.print_exception(exc_type, exc_value, exc_tb)

    # Analyze and suggest
    _print_suggestion(exc_type, exc_value, exc_tb)


def _print_suggestion(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
) -> None:
    """Analyze exception and print suggestion block. Never raises."""
    try:
        config = _get_config()
        suggestion = analyze_exception(exc_type, exc_value, exc_tb, config)
        if suggestion:
            output = format_suggestion_block(suggestion, config)
            sys.stderr.write("\n" + output + "\n")
    except Exception:
        # failwith must NEVER make things worse — silently degrade
        pass


class _CatchContext:
    """Dual-use context manager and decorator for failwith.catch()."""

    def __init__(self, reraise: bool = True):
        self.reraise = reraise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            return False

        # Print traceback
        traceback.print_exception(exc_type, exc_value, exc_tb)

        # Analyze and suggest
        _print_suggestion(exc_type, exc_value, exc_tb)

        # Suppress exception if reraise is False
        return not self.reraise

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with _CatchContext(reraise=self.reraise):
                return func(*args, **kwargs)
        return wrapper


def catch(*, reraise: bool = True) -> _CatchContext:
    """
    Context manager and decorator that catches exceptions and prints suggestions.

    Usage as context manager:
        with failwith.catch():
            risky_operation()

    Usage as decorator:
        @failwith.catch()
        def my_function():
            risky_operation()
    """
    return _CatchContext(reraise=reraise)
