import logging
import os

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", None)  # e.g. "app.log"

    handlers = [logging.StreamHandler()]  # console

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    # Suppress noisy third-party loggers
    for name in ("httpcore", "httpx", "anthropic", "mcp"):
        logging.getLogger(name).setLevel(logging.WARNING)