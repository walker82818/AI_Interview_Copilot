import sys

from loguru import logger

from src.core.config import settings


def setup_logger() -> None:
    logger.remove()
    level = "DEBUG" if settings.debug else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
    )


setup_logger()
