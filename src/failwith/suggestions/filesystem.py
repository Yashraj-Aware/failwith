"""
Suggestion handlers for FileNotFoundError and PermissionError.
"""

from __future__ import annotations

import re
from typing import Any, Optional, Type

from failwith.suggestions import Suggestion, register_builtin
from failwith.utils.fs import (
    find_similar_files,
    list_directory_contents,
    get_file_owner,
    get_current_user,
    get_file_permissions,
    get_working_directory,
)


def handle_file_not_found(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle FileNotFoundError with similar file suggestions."""
    msg = str(exc_value)

    # Extract file path
    match = re.search(r"'([^']+)'|\"([^\"]+)\"", msg)
    if not match:
        # Try the filename attribute
        path = getattr(exc_value, "filename", None)
        if not path:
            return None
    else:
        path = match.group(1) or match.group(2)

    if not path:
        path = getattr(exc_value, "filename", "")

    fixes = []
    title = f"File '{path}' does not exist"

    # Show working directory
    cwd = get_working_directory()
    fixes.append(f"Working dir:   {cwd}")

    # Find similar files
    similar = find_similar_files(path, max_results=3)
    if similar:
        fixes.append(f"Did you mean:  {similar[0]}")
        for s in similar[1:]:
            fixes.append(f"               {s}")

    # List directory contents
    import os
    parent = os.path.dirname(path) or "."
    if os.path.isdir(parent):
        contents = list_directory_contents(parent, max_items=8)
        if contents:
            fixes.append(f"Files in {parent}/: {', '.join(contents)}")
    else:
        fixes.append(f"Directory '{parent}' does not exist either")
        # Find the closest existing parent
        check = parent
        while check and not os.path.exists(check):
            check = os.path.dirname(check)
        if check:
            fixes.append(f"Closest existing parent: {check}")

    return Suggestion(title=title, fixes=fixes)


def handle_permission_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle PermissionError with ownership and chmod suggestions."""
    msg = str(exc_value)

    # Extract file path
    path = getattr(exc_value, "filename", None)
    if not path:
        match = re.search(r"'([^']+)'|\"([^\"]+)\"", msg)
        if match:
            path = match.group(1) or match.group(2)

    if not path:
        return Suggestion(
            title="Permission denied",
            fixes=[
                "You don't have permission to access this resource",
                "Try running with elevated permissions (not recommended for scripts)",
            ],
        )

    fixes = []
    title = f"Permission denied: '{path}'"
    current_user = get_current_user()

    # Check file owner
    owner = get_file_owner(path)
    if owner:
        fixes.append(f"File owner:    {owner}  (you are: {current_user})")

    # Check permissions
    perms = get_file_permissions(path)
    if perms:
        fixes.append(f"Permissions:   {perms}")

    # Suggest fixes
    import os
    if os.path.exists(path):
        fixes.append(f"Fix ownership: sudo chown {current_user} {path}")
        fixes.append(f"Fix perms:     sudo chmod 644 {path}")

        if os.path.isdir(path):
            fixes.append(f"For directory: sudo chmod 755 {path}")
    else:
        # Path doesn't exist — permission error on parent directory
        parent = os.path.dirname(path)
        fixes.append(f"The parent directory may not be writable")
        parent_owner = get_file_owner(parent)
        if parent_owner:
            fixes.append(f"Parent owner:  {parent_owner}")
        fixes.append(f"Fix parent:    sudo chmod 755 {parent}")

    return Suggestion(title=title, fixes=fixes)


def handle_is_a_directory(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle IsADirectoryError."""
    path = getattr(exc_value, "filename", "")
    return Suggestion(
        title=f"Expected a file but got a directory: '{path}'",
        fixes=[
            "You're trying to read/write a directory as if it were a file",
            f"Check the path — is '{path}' supposed to include a filename?",
            "If reading: iterate over files in the directory instead",
        ],
    )


# Register handlers
register_builtin(FileNotFoundError, handle_file_not_found)
register_builtin(PermissionError, handle_permission_error)
register_builtin(IsADirectoryError, handle_is_a_directory)
