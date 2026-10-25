import io
import os
import re

import pytest
from loguru import logger

from second_brain.app import (
    configure_logging,
    log_file_path,
    main,
    stderr_format,
)

STDERR_LINE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| INF \| "
    r"second_brain\.app:main:\d+ \| Hello from second_brain!$"
)


def test_main_logs_greeting(capfd):
    main()
    captured = capfd.readouterr()
    assert "Hello from second_brain!" in captured.err


def test_stderr_line_format(capfd):
    main()
    lines = capfd.readouterr().err.splitlines()
    assert any(STDERR_LINE.match(line) for line in lines), lines


@pytest.mark.parametrize(
    ("level", "short"),
    [
        ("TRACE", "TRC"),
        ("DEBUG", "DBG"),
        ("INFO", "INF"),
        ("SUCCESS", "SUC"),
        ("WARNING", "WRN"),
        ("ERROR", "ERR"),
        ("CRITICAL", "CRT"),
    ],
)
def test_level_short_names(capfd, monkeypatch, level, short):
    monkeypatch.setenv("LOG_LEVEL", "TRACE")
    configure_logging()
    logger.log(level, "level check")
    err = capfd.readouterr().err
    assert f" | {short} | " in err
    assert f" | {level}" not in err


def test_custom_level_falls_back_to_first_three_chars(capfd):
    logger.level("NOTICE_T", no=25)
    configure_logging()
    logger.log("NOTICE_T", "custom level")
    assert " | NOT | " in capfd.readouterr().err


@pytest.mark.parametrize("name", ["{<x", "<b>X", "{0}"])
def test_custom_level_with_markup_chars_does_not_crash(capfd, name):
    logger.level(name, no=26)
    configure_logging()
    logger.log(name, "odd level")
    err = capfd.readouterr().err
    assert f" | {name[:3]} | " in err
    assert "odd level" in err


def test_exception_still_rendered(capfd):
    configure_logging()

    @logger.catch
    def boom():
        return 1 / 0

    boom()
    err = capfd.readouterr().err
    assert " | ERR | " in err
    assert "Traceback" in err
    assert "ZeroDivisionError" in err


def test_colors_on_tty_like_sink():
    sink = io.StringIO()
    logger.remove()
    logger.add(sink, format=stderr_format, colorize=True)
    logger.info("colored")
    assert "\x1b[" in sink.getvalue()


def test_no_colors_when_not_colorized():
    sink = io.StringIO()
    logger.remove()
    logger.add(sink, format=stderr_format, colorize=False)
    logger.info("plain")
    assert "\x1b[" not in sink.getvalue()


def test_log_file_format_unchanged():
    main()
    logger.remove()
    with open(os.environ["LOG_FILE"]) as f:
        content = f.read()
    assert re.search(
        r"\d{2}:\d{2}:\d{2}\.\d{3} \| INFO     \| "
        r"second_brain\.app:main:\d+ - Hello from second_brain!",
        content,
    ), content


# ---------------------------------------------------------------------------
# log file location
# ---------------------------------------------------------------------------


def test_log_file_path_defaults_to_notes_dir(tmp_note_dir, monkeypatch):
    monkeypatch.delenv("LOG_FILE")
    assert log_file_path() == tmp_note_dir / "app.log"


def test_log_file_path_empty_env_uses_default(tmp_note_dir, monkeypatch):
    monkeypatch.setenv("LOG_FILE", "")
    assert log_file_path() == tmp_note_dir / "app.log"


def test_log_file_path_absolute_used_as_is(tmp_path, tmp_note_dir, monkeypatch):
    target = tmp_path / "elsewhere" / "x.log"
    monkeypatch.setenv("LOG_FILE", str(target))
    assert log_file_path() == target


def test_log_file_path_relative_resolves_against_notes_dir(tmp_note_dir, monkeypatch):
    monkeypatch.setenv("LOG_FILE", "logs/debug.log")
    assert log_file_path() == tmp_note_dir / "logs" / "debug.log"


def test_log_file_path_expands_tilde(tmp_path, tmp_note_dir, monkeypatch):
    monkeypatch.setenv("LOG_FILE", "~/x.log")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert log_file_path() == tmp_path / "x.log"


def test_configure_logging_writes_default_log_in_notes_dir(tmp_note_dir, monkeypatch):
    monkeypatch.delenv("LOG_FILE")
    configure_logging()
    logger.info("default location check")
    logger.remove()
    assert "default location check" in (tmp_note_dir / "app.log").read_text()


def test_configure_logging_creates_missing_log_dir(tmp_note_dir, monkeypatch):
    monkeypatch.setenv("LOG_FILE", "logs/debug.log")
    configure_logging()
    logger.info("nested location check")
    logger.remove()
    log = tmp_note_dir / "logs" / "debug.log"
    assert "nested location check" in log.read_text()


def test_configure_logging_absolute_log_file_leaves_notes_dir_alone(tmp_note_dir):
    configure_logging()
    logger.remove()
    assert not tmp_note_dir.exists()


def test_configure_logging_survives_unusable_log_location(tmp_path, monkeypatch, capfd):
    """A log file that cannot be created must not stop the CLI from running."""
    blocker = tmp_path / "blocker"
    blocker.write_text("a file, not a directory")
    monkeypatch.setenv("LOG_FILE", str(blocker / "sub" / "x.log"))
    configure_logging()
    logger.info("still logging")
    logger.remove()
    err = capfd.readouterr().err
    assert "File logging disabled" in err
    assert "still logging" in err


def test_configure_logging_without_console_keeps_stderr_silent(capfd):
    configure_logging(console=False)
    logger.info("file only")
    logger.remove()
    assert capfd.readouterr().err == ""
    with open(os.environ["LOG_FILE"]) as f:
        assert "file only" in f.read()


def test_configure_logging_console_is_on_by_default(capfd):
    configure_logging()
    logger.info("to the console")
    logger.remove()
    assert "to the console" in capfd.readouterr().err
