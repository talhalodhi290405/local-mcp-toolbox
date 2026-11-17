"""Non-sensitive platform and Python runtime information."""

from __future__ import annotations

import os
import platform


def get_system_info() -> dict[str, object]:
    """Return basic OS, architecture, Python, and CPU-count information.

    Deliberately excludes usernames, hostnames, environment variables, network
    addresses, running processes, and other potentially sensitive details.
    """

    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine() or "unknown",
        "python_version": platform.python_version(),
        "logical_cpu_count": os.cpu_count(),
    }


__all__ = ["get_system_info"]
