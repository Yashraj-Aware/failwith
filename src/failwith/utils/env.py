"""
Environment detection — OS, Python version, venv, installed packages.
"""

from __future__ import annotations

import os
import sys
import platform
import shutil
from typing import List, Optional


def get_python_info() -> str:
    """Get Python executable path and version."""
    return f"Python {platform.python_version()} ({sys.executable})"


def get_os_info() -> str:
    """Get OS name and version."""
    system = platform.system()
    if system == "Linux":
        try:
            import distro  # type: ignore
            return f"Linux ({distro.name()} {distro.version()})"
        except ImportError:
            # Try reading /etc/os-release
            try:
                with open("/etc/os-release") as f:
                    lines = f.readlines()
                    info = {}
                    for line in lines:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            info[k] = v.strip('"')
                    name = info.get("PRETTY_NAME", "Linux")
                    return name
            except (FileNotFoundError, PermissionError):
                return f"Linux ({platform.release()})"
    elif system == "Darwin":
        ver = platform.mac_ver()[0]
        return f"macOS {ver}" if ver else "macOS"
    elif system == "Windows":
        ver = platform.version()
        return f"Windows {ver}"
    return system


def get_venv_info() -> Optional[str]:
    """Detect active virtual environment."""
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        return venv

    # Check for conda
    conda = os.environ.get("CONDA_DEFAULT_ENV")
    if conda:
        return f"conda:{conda}"

    # Check sys.prefix vs sys.base_prefix
    if sys.prefix != sys.base_prefix:
        return sys.prefix

    return None


def is_command_available(cmd: str) -> bool:
    """Check if a command is available on PATH."""
    return shutil.which(cmd) is not None


def get_service_manager() -> str:
    """Detect the init/service manager on the system."""
    system = platform.system()

    if system == "Darwin":
        return "brew"
    elif system == "Windows":
        return "sc"
    elif system == "Linux":
        if is_command_available("systemctl"):
            return "systemctl"
        elif is_command_available("service"):
            return "service"
    return "manual"


def get_env_summary() -> List[str]:
    """Get a compact environment summary for the suggestion footer."""
    parts = []
    parts.append(f"Python {platform.python_version()}")

    venv = get_venv_info()
    if venv:
        # Show just the last directory name
        venv_name = os.path.basename(venv)
        parts.append(f"venv: {venv_name}")
    else:
        parts.append("venv: none")

    parts.append(get_os_info())
    return parts


def is_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed."""
    try:
        from importlib.metadata import distribution
        distribution(package_name)
        return True
    except Exception:
        return False


def get_installed_version(package_name: str) -> Optional[str]:
    """Get the installed version of a package, or None if not installed."""
    try:
        from importlib.metadata import distribution
        return distribution(package_name).version
    except Exception:
        return None
