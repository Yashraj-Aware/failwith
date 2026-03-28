"""
Suggestion handlers for connection and network errors.
"""

from __future__ import annotations

import re
from typing import Any, Optional, Type

from failwith.suggestions import Suggestion, register_builtin
from failwith.data.port_map import identify_service
from failwith.utils.env import get_service_manager, is_command_available


def handle_connection_refused(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle ConnectionRefusedError with port-aware service suggestions."""
    msg = str(exc_value)

    # Extract port number from error message
    port = _extract_port(msg, exc_value)

    fixes = []

    if port:
        service = identify_service(port)
        if service:
            title = f"Connection refused on port {port} ({service['name']} default port)"
            fixes.extend(_service_start_commands(service))
        else:
            title = f"Connection refused on port {port}"
            fixes.append(f"Check if the service on port {port} is running")
            fixes.append(f"Verify port:   ss -tlnp | grep {port}")
    else:
        title = "Connection refused"
        fixes.append("The target service is not running or not accepting connections")

    # Generic network debugging
    fixes.append("Check firewall: sudo iptables -L -n | grep <port>")

    if is_command_available("docker"):
        fixes.append("Using Docker?  docker ps  (check if container is running)")

    return Suggestion(title=title, fixes=fixes)


def handle_connection_timeout(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle TimeoutError / socket.timeout."""
    msg = str(exc_value)
    port = _extract_port(msg, exc_value)

    title = "Connection timed out"
    fixes = []

    if port:
        service = identify_service(port)
        if service:
            title = f"Connection to {service['name']} (port {port}) timed out"
            fixes.append(f"Is {service['name']} running and reachable?")

    fixes.extend([
        "Check if the host is reachable:   ping <host>",
        "Check DNS resolution:             nslookup <host>",
        "Check if a firewall is blocking:  telnet <host> <port>",
        "Increase timeout in your code if the service is slow",
    ])

    return Suggestion(title=title, fixes=fixes)


def handle_connection_reset(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_tb: Any,
    config: dict,
) -> Optional[Suggestion]:
    """Handle ConnectionResetError."""
    return Suggestion(
        title="Connection was reset by the remote server",
        fixes=[
            "The server closed the connection unexpectedly",
            "Check server logs for errors or crashes",
            "You may be hitting rate limits or max connection limits",
            "Try adding retry logic with exponential backoff",
            "Check if SSL/TLS version mismatch is causing drops",
        ],
    )


def _extract_port(msg: str, exc_value: BaseException) -> Optional[int]:
    """Extract port number from error message or exception args."""
    # Try errno-style: [Errno 111] Connection refused  (port in args)
    if hasattr(exc_value, "args") and len(exc_value.args) >= 2:
        # OSError sometimes has (errno, message) or address tuple
        for arg in exc_value.args:
            if isinstance(arg, tuple) and len(arg) >= 2:
                # Address tuple like ('localhost', 5432)
                try:
                    return int(arg[1])
                except (ValueError, TypeError, IndexError):
                    pass

    # Try parsing from message string
    patterns = [
        r"port[:\s]+(\d+)",
        r":(\d+)\b",
        r"localhost:(\d+)",
        r"127\.0\.0\.1:(\d+)",
        r"\(.*?,\s*(\d+)\)",  # ('host', port) tuple in message
    ]

    for pattern in patterns:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            try:
                port = int(match.group(1))
                if 1 <= port <= 65535:
                    return port
            except ValueError:
                continue

    return None


def _service_start_commands(service: dict) -> list:
    """Generate OS-appropriate start commands for a service."""
    from failwith.utils.env import get_service_manager

    manager = get_service_manager()
    name = service["name"]
    fixes = []

    if manager == "systemctl" and service.get("systemctl"):
        svc = service["systemctl"]
        fixes.append(f"Start {name}:   sudo systemctl start {svc}")
        fixes.append(f"Check status:  sudo systemctl status {svc}")
    elif manager == "brew" and service.get("brew"):
        svc = service["brew"]
        fixes.append(f"Start {name}:   brew services start {svc}")
        fixes.append(f"Check status:  brew services list")
    elif manager == "service" and service.get("systemctl"):
        svc = service["systemctl"]
        fixes.append(f"Start {name}:   sudo service {svc} start")
        fixes.append(f"Check status:  sudo service {svc} status")
    else:
        fixes.append(f"Start {name} using your system's service manager")

    # Always add docker suggestion
    if service.get("docker"):
        fixes.append(f"Using Docker?  docker start {service['docker']}")

    # Add port check
    fixes.append(f"Verify port:   ss -tlnp | grep {service['port']}")

    return fixes


# Register handlers
register_builtin(ConnectionRefusedError, handle_connection_refused)
register_builtin(TimeoutError, handle_connection_timeout)
register_builtin(ConnectionResetError, handle_connection_reset)
