"""
User access utilities for ENIAC.

Defines two roles: "student" and "guest" and provides helpers to get/set
roles and a route decorator for role-based access control.
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable, Optional
import json

from flask import session, abort


# Mirrors app.py's USERS_FILE location
USERS_FILE = "users.json"

# Supported roles
ROLE_STUDENT = "student"
ROLE_GUEST = "guest"
ROLE_ADMIN = "admin"
ROLES = {ROLE_STUDENT, ROLE_GUEST, ROLE_ADMIN}

# Default role for new accounts
DEFAULT_ROLE = ROLE_STUDENT


def _load_users() -> dict:
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_role(username: str, *, default: str = ROLE_GUEST) -> str:
    """Return the role for a username; fallback to ``default`` if missing."""
    users = _load_users()
    record = users.get(username) or {}
    role = record.get("role")
    if role in ROLES:
        return role
    return default


def set_role(username: str, role: str) -> None:
    """Set the role for an existing user.

    Raises:
        ValueError: if role is not one of the supported roles
        KeyError: if the user does not exist
    """
    if role not in ROLES:
        raise ValueError(f"Unsupported role: {role}. Allowed: {sorted(ROLES)}")
    users = _load_users()
    if username not in users:
        raise KeyError(f"Unknown user: {username}")
    users[username]["role"] = role
    _save_users(users)


def current_role(*, default: str = ROLE_GUEST) -> str:
    """Return the role for the current session.

    Not logged in => "guest".
    Logged in => defaults to "student" if user has no explicit role.
    """
    username = session.get("user")
    if not username:
        return default
    # When logged in, prefer student if no role saved
    return get_role(username, default=ROLE_STUDENT)


def is_student(username: Optional[str] = None) -> bool:
    if username is None:
        return current_role() == ROLE_STUDENT
    return get_role(username) == ROLE_STUDENT


def is_guest(username: Optional[str] = None) -> bool:
    if username is None:
        return current_role() == ROLE_GUEST
    return get_role(username) == ROLE_GUEST


def is_admin(username: Optional[str] = None) -> bool:
    if username is None:
        return current_role() == ROLE_ADMIN
    return get_role(username) == ROLE_ADMIN


def require_roles(*allowed_roles: Iterable[str]) -> Callable:
    """Flask view decorator to require one of the given roles.

    Example:
        @app.route('/students')
        @require_roles(ROLE_STUDENT)
        def students_only():
            ...
    """

    # Flatten in case someone passes a list/tuple
    flat_allowed = set()
    for r in allowed_roles:
        if isinstance(r, (list, tuple, set)):
            flat_allowed.update(r)
        else:
            flat_allowed.add(r)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = current_role()
            if role not in flat_allowed:
                # Not authorized
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
