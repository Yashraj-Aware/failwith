"""
failwith — Actionable error intelligence for Python.

When Python tells you what broke, failwith tells you why and how to fix it.

Usage:
    import failwith
    failwith.install()

That's it. Every unhandled exception now gets actionable fix suggestions.
"""

__version__ = "0.1.0"

from failwith.core.interceptor import install, uninstall, catch
from failwith.suggestions.base import Suggestion, register

__all__ = [
    "install",
    "uninstall",
    "catch",
    "register",
    "Suggestion",
    "__version__",
]
