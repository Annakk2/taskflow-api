"""Domain-level exceptions raised by the service layer.

Routers never construct HTTPException themselves for these cases; a single
exception handler in main.py translates each of these into the appropriate
HTTP response. This keeps status-code decisions in one place.
"""


class NotFoundError(Exception):
    """Requested resource does not exist."""


class DuplicateError(Exception):
    """A uniqueness constraint would be violated (e.g. duplicate email)."""
