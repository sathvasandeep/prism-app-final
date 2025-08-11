"""Lightweight models package initializer.

Avoid importing heavy ORM modules at import time to prevent optional
dependencies (like SQLAlchemy) from being required by modules that only
need lightweight utilities (e.g., phrase library).
"""

# Export names only when explicitly imported elsewhere.
__all__ = []