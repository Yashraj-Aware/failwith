"""
Suggestion handlers for ModuleNotFoundError and ImportError.
"""

from __future__ import annotations

import sys
import re
from typing import Any, Optional, Type

from failwith.suggestions import Suggestion, register_builtin
from failwith.data.import_map import lookup_package
from failwith.utils.env import get_venv_info
from failwith.utils.fuzzy import closest_matches


def handle_module_not_found(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle ModuleNotFoundError with install suggestions."""
    msg = str(exc_value)

    # Extract module name from "No module named 'xxx'" or "No module named 'xxx.yyy'"
    match = re.search(r"No module named '([^']+)'", msg)
    if not match:
        return None

    module_name = match.group(1)
    root_module = module_name.split(".")[0]

    fixes = []
    title = f"Module '{module_name}' is not installed"

    # Check import -> package mapping
    pkg_info = lookup_package(module_name) or lookup_package(root_module)

    if pkg_info:
        package_name, notes = pkg_info
        if package_name.lower() != root_module.lower():
            title = f"'{root_module}' is from the '{package_name}' package (import name ≠ package name)"
        fixes.append(f"Install it:    pip install {package_name}")
        if notes:
            fixes.append(f"Note:          {notes}")
    else:
        fixes.append(f"Install it:    pip install {root_module}")

    # Check venv context
    venv = get_venv_info()
    if venv:
        fixes.append(f"Active venv:   {venv}")
    else:
        fixes.append(f"No venv active — you may be installing to the wrong Python")
        fixes.append(f"Current Python: {sys.executable}")

    # Check if the module name shadows a local file
    _check_local_shadow(root_module, fixes)

    # Check for common submodule patterns
    if "." in module_name:
        base = module_name.split(".")[0]
        fixes.append(f"Is '{base}' installed? pip show {base}")

    env_info = [f"Python: {sys.executable}"]

    return Suggestion(
        title=title,
        fixes=fixes,
        env_info=env_info,
        docs_url="https://docs.python.org/3/library/importlib.html",
    )


def handle_import_error(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle ImportError (cannot import name X from Y)."""
    msg = str(exc_value)

    # "cannot import name 'X' from 'Y'"
    match = re.search(r"cannot import name '([^']+)' from '([^']+)'", msg)
    if not match:
        return None

    name = match.group(1)
    module = match.group(2)

    fixes = []
    title = f"Cannot import '{name}' from '{module}'"

    # Try to import the module and check available names
    try:
        mod = sys.modules.get(module)
        if mod is None:
            import importlib
            mod = importlib.import_module(module)

        available = [n for n in dir(mod) if not n.startswith("_")]
        matches = closest_matches(name, available, n=3)

        if matches:
            fixes.append(f"Did you mean:  {matches[0]}")
            if len(matches) > 1:
                fixes.append(f"Also similar:  {', '.join(matches[1:])}")
    except Exception:
        pass

    # Check for circular import hints
    if "partially initialized module" in msg or "circular" in msg.lower():
        fixes.append("This looks like a circular import")
        fixes.append("Move the import inside the function that uses it")
        fixes.append("Or restructure: extract shared code into a third module")
    else:
        fixes.append(f"The name may have been removed or renamed in a newer version")
        fixes.append(f"Check version:  pip show {module.split('.')[0]}")

    return Suggestion(title=title, fixes=fixes)


def _check_local_shadow(module_name: str, fixes: list) -> None:
    """Check if a local file is shadowing the module."""
    import os
    cwd = os.getcwd()
    shadow_file = os.path.join(cwd, f"{module_name}.py")
    shadow_dir = os.path.join(cwd, module_name)

    if os.path.exists(shadow_file):
        fixes.append(f"⚠ Local file '{module_name}.py' may be shadowing the installed package")
        fixes.append(f"  Rename it:   mv {module_name}.py {module_name}_local.py")
    elif os.path.isdir(shadow_dir) and os.path.exists(os.path.join(shadow_dir, "__init__.py")):
        fixes.append(f"⚠ Local package '{module_name}/' may be shadowing the installed package")


# Register handlers
register_builtin(ModuleNotFoundError, handle_module_not_found)
register_builtin(ImportError, handle_import_error)
