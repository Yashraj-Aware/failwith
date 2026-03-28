"""
Suggestion handlers for encoding, memory, syntax, JSON, and OS errors.
"""

from __future__ import annotations

import re
from typing import Any, Optional, Type

from failwith.suggestions import Suggestion, register_builtin


# === Encoding Errors ===

def handle_unicode_decode(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle UnicodeDecodeError with encoding suggestions."""
    encoding = getattr(exc_value, "encoding", "unknown")
    reason = getattr(exc_value, "reason", "")

    title = f"Cannot decode bytes using '{encoding}' encoding"
    fixes = [
        f"Try a different encoding:",
        f"  open('file', encoding='utf-8')",
        f"  open('file', encoding='latin-1')    # catches most Western text",
        f"  open('file', encoding='cp1252')      # Windows default",
        f"Ignore errors:  open('file', encoding='utf-8', errors='ignore')",
        f"Replace errors: open('file', encoding='utf-8', errors='replace')",
        f"Detect encoding: pip install chardet, then:",
        f"  import chardet; chardet.detect(raw_bytes)",
    ]

    return Suggestion(title=title, fixes=fixes)


def handle_unicode_encode(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle UnicodeEncodeError."""
    encoding = getattr(exc_value, "encoding", "unknown")

    title = f"Cannot encode text using '{encoding}' encoding"
    fixes = [
        f"Use UTF-8:       text.encode('utf-8')",
        f"Ignore:          text.encode('{encoding}', errors='ignore')",
        f"Replace:         text.encode('{encoding}', errors='replace')",
        f"XML escape:      text.encode('{encoding}', errors='xmlcharrefreplace')",
    ]

    if encoding == "ascii":
        fixes.insert(0, "ASCII can't handle non-English characters — use UTF-8 instead")

    return Suggestion(title=title, fixes=fixes)


# === Memory & Recursion ===

def handle_recursion_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle RecursionError with stack analysis."""
    import sys
    limit = sys.getrecursionlimit()

    fixes = [
        f"Current recursion limit: {limit}",
        "Your function is calling itself without a proper base case",
        "Check: is the recursive call getting closer to the base case?",
        "Common causes:",
        "  - Missing or incorrect base case / termination condition",
        "  - __repr__ or __str__ referencing the object itself",
        "  - Circular references between objects",
        "  - Property getter calling itself",
        "Convert to iteration: use a loop + stack (list) instead of recursion",
    ]

    # Try to show the recursive function name from traceback
    if exc_tb:
        tb = exc_tb
        func_names = set()
        count = 0
        while tb and count < 50:
            func_names.add(tb.tb_frame.f_code.co_name)
            tb = tb.tb_next
            count += 1
        if func_names:
            fixes.insert(0, f"Recursive call chain involves: {', '.join(list(func_names)[:5])}")

    return Suggestion(
        title="Maximum recursion depth exceeded",
        fixes=fixes,
    )


def handle_memory_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle MemoryError."""
    return Suggestion(
        title="Out of memory",
        fixes=[
            "Your program is trying to allocate more memory than available",
            "Common causes:",
            "  - Loading entire large file into memory (use chunked reading)",
            "  - Creating very large lists/dicts (use generators instead)",
            "  - Memory leak from accumulating data in a loop",
            "For large files: use chunked I/O (pandas: chunksize=, open: readline())",
            "For large data:  use generators (yield) instead of building full lists",
            "Monitor memory:  pip install memory_profiler; @profile your function",
        ],
    )


# === Syntax Errors ===

def handle_syntax_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle SyntaxError with common fix patterns."""
    msg = str(exc_value)
    text = getattr(exc_value, "text", "") or ""
    lineno = getattr(exc_value, "lineno", None)
    filename = getattr(exc_value, "filename", None)

    fixes = []

    if "EOL while scanning string literal" in msg:
        title = "Unterminated string"
        fixes.extend([
            "A string is missing its closing quote",
            "Check for mismatched quotes (', \", ''', \"\"\")",
            "Multi-line string? Use triple quotes: '''text''' or \"\"\"text\"\"\"",
        ])
    elif "unexpected EOF" in msg or "expected an indented block" in msg:
        title = "Unexpected end of code"
        fixes.extend([
            "A code block is incomplete — missing body or closing bracket",
            "Check: empty function/class/if? Add 'pass' as placeholder",
            "Check: unclosed parentheses, brackets, or braces",
        ])
    elif "invalid syntax" in msg:
        title = "Invalid syntax"
        fixes.extend([
            "Common causes:",
            "  - Missing colon after if/for/def/class",
            "  - Using = instead of == in comparisons",
            "  - Missing comma between items",
            "  - Using Python 2 syntax (print vs print())",
        ])
        if text:
            if "print " in text and "print(" not in text:
                fixes.insert(0, "Use print() with parentheses (Python 3 syntax)")
    elif "perhaps you forgot a comma" in msg:
        title = "Missing comma"
        fixes.append("Add a comma between elements in your list, tuple, or dict")
    elif "f-string" in msg.lower():
        title = "Invalid f-string"
        fixes.extend([
            "Check f-string syntax: f\"text {expression} text\"",
            "Escape braces with double: f\"use {{literal braces}}\"",
            "No backslashes in f-string expressions (use a variable instead)",
        ])
    else:
        title = "Syntax error"
        fixes.append(msg)
        fixes.append("Check the line indicated and the line above it")

    if lineno and filename:
        fixes.append(f"Location: {filename}:{lineno}")

    return Suggestion(title=title, fixes=fixes)


# === JSON Errors ===

def handle_json_decode_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle json.JSONDecodeError."""
    import json

    msg = str(exc_value)
    fixes = []

    # Extract position info
    pos = getattr(exc_value, "pos", None)
    lineno = getattr(exc_value, "lineno", None)
    colno = getattr(exc_value, "colno", None)
    doc = getattr(exc_value, "doc", "")

    title = "Invalid JSON"

    if pos is not None and doc:
        # Show context around the error
        start = max(0, pos - 30)
        end = min(len(doc), pos + 30)
        context = doc[start:end]
        pointer = " " * (pos - start) + "^"
        fixes.append(f"Error near position {pos}:")
        fixes.append(f"  ...{context}...")
        fixes.append(f"     {pointer}")

    if "Expecting property name" in msg:
        fixes.append("Trailing comma before closing brace/bracket?")
    elif "Expecting ',' delimiter" in msg:
        fixes.append("Missing comma between items?")
    elif "Expecting value" in msg:
        fixes.append("Empty value or trailing comma")
    elif "Extra data" in msg:
        fixes.append("Multiple JSON objects in string — parse only the first")
        fixes.append("Or wrap them in an array: [{...}, {...}]")

    fixes.extend([
        "Common JSON issues:",
        "  - Single quotes instead of double quotes",
        "  - Trailing commas (not allowed in JSON)",
        "  - Comments (not allowed in JSON)",
        "  - Unquoted keys",
        "Validate online: https://jsonlint.com",
    ])

    return Suggestion(title=title, fixes=fixes)


# === OS Errors ===

def handle_os_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle generic OSError with errno-based suggestions."""
    import errno

    err_no = getattr(exc_value, "errno", None)
    msg = str(exc_value)

    if err_no == errno.ENOSPC:
        return Suggestion(
            title="No space left on device",
            fixes=[
                "Your disk is full",
                "Check usage:    df -h",
                "Find large files: du -sh /* | sort -rh | head -20",
                "Clean apt cache: sudo apt clean",
                "Clean pip cache: pip cache purge",
            ],
        )
    elif err_no == errno.EMFILE or err_no == errno.ENFILE:
        return Suggestion(
            title="Too many open files",
            fixes=[
                "You've exhausted the file descriptor limit",
                "Check limit:    ulimit -n",
                "Increase:       ulimit -n 65535",
                "Permanent fix:  Add to /etc/security/limits.conf",
                "Fix in code:    use 'with open()' to auto-close files",
                "Find leaks:     lsof -p <pid> | wc -l",
            ],
        )
    elif err_no == errno.EADDRINUSE:
        # Extract port
        port_match = re.search(r":(\d+)", msg)
        port = port_match.group(1) if port_match else "?"
        return Suggestion(
            title=f"Address already in use (port {port})",
            fixes=[
                f"Port {port} is already taken by another process",
                f"Find process:  lsof -i :{port}",
                f"Kill it:       kill $(lsof -t -i :{port})",
                f"Use a different port in your application config",
            ],
        )

    return None  # Let more specific handlers deal with it


def handle_stop_iteration(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle StopIteration."""
    return Suggestion(
        title="Iterator exhausted",
        fixes=[
            "next() was called on an exhausted iterator",
            "Use a default:  next(iterator, default_value)",
            "Or check first:  for item in iterator: ...",
            "Re-create the iterator if you need to iterate again",
        ],
    )


# Register handlers
register_builtin(UnicodeDecodeError, handle_unicode_decode)
register_builtin(UnicodeEncodeError, handle_unicode_encode)
register_builtin(RecursionError, handle_recursion_error)
register_builtin(MemoryError, handle_memory_error)
register_builtin(SyntaxError, handle_syntax_error)
register_builtin(OSError, handle_os_error)
register_builtin(StopIteration, handle_stop_iteration)

# JSON — need to handle import since json module might not define this in all versions
try:
    import json
    register_builtin(json.JSONDecodeError, handle_json_decode_error)
except (ImportError, AttributeError):
    pass
