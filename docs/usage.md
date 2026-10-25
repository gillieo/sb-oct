# Usage

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

## Running

The CLI exposes three subcommands so far:

```bash
uv run second_brain new "My brilliant idea"   # save a note as markdown
uv run second_brain list                      # list notes (newest first)
uv run second_brain show 1                    # print the contents of note 1
```

Notes are plain markdown files named `YYYY-MM-DD-<slug>.md`. Each contains the
title as a heading followed by an ISO timestamp. If a file with that name
already exists, `-1`, `-2`, … is appended instead of overwriting it.

### Multi-line notes

Add a body with `--body` (short: `-b`), or `--body -` to read it from stdin:

```bash
uv run second_brain new "Caching idea" --body $'Use an LRU.\n\nCheck memory limits.'
cat draft.md | uv run second_brain new "Draft" --body -
```

If the title contains newlines, only its first line is used as the heading and
the filename slug; the remaining lines are put at the start of the body. `\r\n`
line endings are normalised to `\n`. The note is written as the heading, the
body (if any) and the timestamp, separated by blank lines.

With dev settings loaded:

```bash
uv run --env-file .env second_brain new "My brilliant idea"
```

Or as a Python module:

```bash
uv run python -m second_brain new "My brilliant idea"
```

`list` prints the full path of the notes directory followed by a numbered list of
the note filenames, newest first. `show N` prints the content of note `N` from that list; an
unknown number, an empty or missing notes directory exits with status 1 and an
error on stderr.

## Built-in help

Every command describes itself, with examples, so people and agents can
discover how to use it without reading the docs:

```bash
uv run second_brain --help          # overview, workflow, environment variable
uv run second_brain new --help      # titles, --body, stdin, multi-line examples
uv run second_brain list --help
uv run second_brain show --help     # numbering and error behaviour
```

Command results (paths, listings, note contents) are written to stdout; log
lines and errors go to stderr, so stdout can be piped or captured safely.

## Environment Variables

| Variable           | Default            | Description                        |
|--------------------|--------------------|------------------------------------|
| `LOG_LEVEL`        | `INFO`             | Console log level (DEBUG, INFO, …) |
| `LOG_FILE`         | `app.log`          | Path to the log file               |
| `SECOND_BRAIN_DIR` | `~/second_brain/`  | Directory where notes are stored   |

Copy `.env.example` to `.env` for development defaults, then run with `uv run --env-file .env`.

## Log Format

Console (stderr) output uses a compact format:

```
2026-10-24 19:45:00 | INF | second_brain.app:main:29 | Hello from second_brain!
```

Fields: timestamp (no milliseconds) · level · `module:function:line` · message.
Levels are shown as three-letter abbreviations:

| Level      | Shown as |
|------------|----------|
| `TRACE`    | `TRC`    |
| `DEBUG`    | `DBG`    |
| `INFO`     | `INF`    |
| `SUCCESS`  | `SUC`    |
| `WARNING`  | `WRN`    |
| `ERROR`    | `ERR`    |
| `CRITICAL` | `CRT`    |

Custom levels show the first three characters of their name. Output is
colorized when stderr is a terminal and plain otherwise (e.g. when piped).

The log file (`LOG_FILE`) keeps loguru's default, more detailed format with
milliseconds and full level names.
