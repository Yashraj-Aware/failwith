"""
Exception analyzer — routes exceptions to the appropriate suggestion handler.
"""

from __future__ import annotations

from typing import Any, Optional, Type

from failwith.suggestions import Suggestion, get_handlers

# Import all suggestion modules to trigger registration
import failwith.suggestions.imports  # noqa: F401
import failwith.suggestions.connection  # noqa: F401
import failwith.suggestions.filesystem  # noqa: F401
import failwith.suggestions.types  # noqa: F401
import failwith.suggestions.misc  # noqa: F401


def analyze_exception(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """
    Analyze an exception and return an actionable Suggestion.

    Walks the handler registry (custom first, then built-in) and returns
    the first non-None suggestion. If no handler matches, returns None.
    """
    handlers = get_handlers(exc_type)

    for handler in handlers:
        try:
            suggestion = handler(exc_type, exc_value, exc_tb, config)
            if suggestion and suggestion.fixes:
                # Trim fixes to max_suggestions
                max_fixes = config.get("max_suggestions", 10)
                if len(suggestion.fixes) > max_fixes:
                    suggestion.fixes = suggestion.fixes[:max_fixes]

                # Attach environment info if not already set
                if suggestion.env_info is None:
                    try:
                        from failwith.utils.env import get_env_summary
                        suggestion.env_info = get_env_summary()
                    except Exception:
                        pass

                return suggestion
        except Exception:
            # Individual handler failure must never propagate
            continue

    return None
