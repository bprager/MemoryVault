from __future__ import annotations

import logging
from pathlib import Path


LOGGER_NAME = "memoryvault"


def configure_logging(level: str = "WARNING", log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(_coerce_level(level))
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(stream_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    suffix = f".{name}" if name else ""
    return logging.getLogger(f"{LOGGER_NAME}{suffix}")


def _coerce_level(level: str) -> int:
    normalized = level.upper()
    if normalized == "DEBUG":
        return logging.DEBUG
    if normalized == "INFO":
        return logging.INFO
    if normalized == "ERROR":
        return logging.ERROR
    return logging.WARNING
