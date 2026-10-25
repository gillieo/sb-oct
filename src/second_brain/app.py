import sys

from loguru import logger

LEVEL_SHORT_NAMES = {
    "TRACE": "TRC",
    "DEBUG": "DBG",
    "INFO": "INF",
    "SUCCESS": "SUC",
    "WARNING": "WRN",
    "ERROR": "ERR",
    "CRITICAL": "CRT",
}


def stderr_format(record: dict) -> str:
    """Build the compact loguru format template for the stderr sink.

    Produces lines like
    `2026-10-24 19:45:00 | INF | second_brain.app:main:29 | Hello!`.
    Built-in levels map to three-letter names via `LEVEL_SHORT_NAMES`; custom
    levels fall back to the first three characters of their name.

    Args:
        record: The loguru record dict of the message being logged.

    Returns:
        A format template ending with `\\n{exception}`, as loguru requires
            for callable formats.
    """
    # Unknown names are substituted at render time rather than embedded in the
    # template, so braces or markup tags in a custom level name stay literal.
    short = LEVEL_SHORT_NAMES.get(record["level"].name, "{level.name:.3}")
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        f"<level>{short}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>\n{exception}"
    )


def configure_logging():
    """Configure loguru for console and file logging.

    Removes the default handler and sets up:
    - stderr handler at LOG_LEVEL (default: INFO, configurable via env var),
      using the compact `stderr_format`
    - File handler at DEBUG level writing to LOG_FILE (default: app.log),
      using loguru's default format
    """
    import os

    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_file = os.environ.get("LOG_FILE", "app.log")
    logger.remove()
    logger.add(sys.stderr, level=log_level, format=stderr_format)
    logger.add(log_file, level="DEBUG", rotation="50 KB", retention=1)


@logger.catch
def main():
    """Run the application.

    Configures logging and prints a greeting to verify the setup works.
    """
    configure_logging()
    logger.info("Hello from second_brain!")
