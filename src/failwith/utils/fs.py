"""
File system helpers — find similar files, check permissions, etc.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import pwd
    import grp
    _HAS_UNIX_PERMS = True
except ImportError:
    _HAS_UNIX_PERMS = False

from failwith.utils.fuzzy import closest_matches


def find_similar_files(target_path: str, max_results: int = 5) -> List[str]:
    """
    Find files with similar names in the same directory.
    """
    path = Path(target_path)
    parent = path.parent
    target_name = path.name

    if not parent.exists():
        # Try walking up to find an existing parent
        for p in path.parents:
            if p.exists():
                parent = p
                break
        else:
            return []

    try:
        existing_files = [f.name for f in parent.iterdir() if not f.name.startswith(".")]
    except PermissionError:
        return []

    matches = closest_matches(target_name, existing_files, n=max_results, cutoff=0.3)
    return [str(parent / m) for m in matches]


def list_directory_contents(dir_path: str, max_items: int = 10) -> List[str]:
    """List files in a directory, up to max_items."""
    try:
        path = Path(dir_path)
        if not path.is_dir():
            path = path.parent
        if not path.exists():
            return []

        items = sorted(
            [f.name for f in path.iterdir() if not f.name.startswith(".")],
        )
        return items[:max_items]
    except (PermissionError, OSError):
        return []


def get_file_owner(file_path: str) -> Optional[str]:
    """Get the owner of a file. Returns 'user:group' or None."""
    if not _HAS_UNIX_PERMS:
        return None
    try:
        st = os.stat(file_path)
        try:
            user = pwd.getpwuid(st.st_uid).pw_name
        except KeyError:
            user = str(st.st_uid)
        try:
            group = grp.getgrgid(st.st_gid).gr_name
        except KeyError:
            group = str(st.st_gid)
        return f"{user}:{group}"
    except (FileNotFoundError, OSError):
        return None


def get_current_user() -> str:
    """Get the current user's username."""
    try:
        return os.getlogin()
    except OSError:
        import getpass
        return getpass.getuser()


def get_file_permissions(file_path: str) -> Optional[str]:
    """Get file permissions as octal string (e.g., '644')."""
    try:
        st = os.stat(file_path)
        return oct(stat.S_IMODE(st.st_mode))[2:]
    except (FileNotFoundError, OSError):
        return None


def get_working_directory() -> str:
    """Get the current working directory."""
    return os.getcwd()
