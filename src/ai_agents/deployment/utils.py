"""Shared utilities - no business logic."""
import os
from pathlib import Path
from typing import Optional


def get_actual_user() -> str:
    """Get actual user (not root when using sudo)."""
    return os.getenv("SUDO_USER") or os.getenv("USER") or "root"


def get_user_home() -> Path:
    """Get actual user's home directory."""
    user = get_actual_user()
    if user and user != "root":
        import pwd

        try:
            return Path(pwd.getpwnam(user).pw_dir)
        except KeyError:
            pass
    return Path.home()


def get_user_uid() -> int:
    """Get actual user's UID."""
    user = get_actual_user()
    if user and user != "root":
        import pwd

        try:
            return pwd.getpwnam(user).pw_uid
        except KeyError:
            pass
    return os.getuid()


def get_user_gid() -> int:
    """Get actual user's GID."""
    user = get_actual_user()
    if user and user != "root":
        import pwd

        try:
            return pwd.getpwnam(user).pw_gid
        except KeyError:
            pass
    return os.getgid()


def is_running_as_root() -> bool:
    """Check if running with root privileges."""
    return os.geteuid() == 0
