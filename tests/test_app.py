import io
import os
import re

import pytest
from loguru import logger

from second_brain.app import configure_logging, main, stderr_format

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
