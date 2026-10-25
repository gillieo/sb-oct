import os
import sys
from pathlib import Path

from loguru import logger

from second_brain.notes import notes_dir

DEFAULT_LOG_FILE = "app.log"

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


def log_file_path() -> Path:
    """Return the log file path, from `LOG_FILE` or `app.log` in the notes dir.

    Read lazily on every call so the environment stays authoritative. An empty
    `LOG_FILE` counts as unset. A leading `~` is expanded, an absolute path is
    used as-is, and a relative path is resolved against the notes directory
    (never the current working directory).

    Returns:
        The path the file handler should write to.
    """
    path = Path(os.environ.get("LOG_FILE") or DEFAULT_LOG_FILE).expanduser()
    return path if path.is_absolute() else notes_dir() / path


def configure_logging():
    """Configure loguru for console and file logging.

    Removes the default handler and sets up:
    - stderr handler at LOG_LEVEL (default: INFO, configurable via env var),
      using the compact `stderr_format`
    - File handler at DEBUG level writing to `log_file_path` (default:
      `app.log` in the notes directory), using loguru's default format. The
      file's parent directory is created if it is missing.

    If the log file cannot be created or opened (for example a read-only notes
    directory), a warning goes to stderr and logging continues without the
    file handler, so read-only commands such as `list` still work.
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_file = log_file_path()
    logger.remove()
    logger.add(sys.stderr, level=log_level, format=stderr_format)
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(log_file, level="DEBUG", rotation="50 KB", retention=1)
    except OSError as exc:
        logger.warning("File logging disabled: {}", exc)


@logger.catch
def main():
    """Run the application.

    Configures logging and prints a greeting to verify the setup works.
    """
    configure_logging()
    logger.info("Hello from second_brain!")
