import logging
import sys

from app.config import get_settings


def configure_logging() -> None:
    """Configure application-wide logging. Called once at startup."""
    settings = get_settings()

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root.handlers.clear()
    root.addHandler(handler)

    # Quiet down noisy third-party loggers; app logs stay at the configured level.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
