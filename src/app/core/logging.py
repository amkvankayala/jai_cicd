"""Central logging configuration."""

import logging


def configure_logging() -> logging.Logger:
    """Configure the application logger once and return it."""
    logger = logging.getLogger("stock_insights")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    logger.debug("Application logger configured")
    return logger


logger = configure_logging()
