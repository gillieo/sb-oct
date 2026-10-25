# second-brain

## Installation

1. Clone the repository.
2. Install dependencies:

```bash
uv sync
```

## Usage

Run `uv run second_brain` for the interactive TUI (see below), or use the three subcommands:

```bash
uv run second_brain new "My brilliant idea"   # save a note as markdown
uv run second_brain new "Title" --body "More text"  # note with a multi-line body
uv run second_brain list                      # list notes (newest first)
uv run second_brain show 1                    # print the contents of note 1
```

Notes are plain markdown files named `YYYY-MM-DD-<slug>.md`, each starting with the title as a heading, then the optional body, then a timestamp.

Multi-line notes: pass `--body` (or `-b`), or `--body -` to read the body from stdin. If the title itself contains newlines, its first line is the heading and the rest is added to the body:

```bash
uv run second_brain new "Caching idea" --body $'Use an LRU.\n\nCheck memory limits.'
cat draft.md | uv run second_brain new "Draft" --body -
```

With the dev environment:

```bash
uv run --env-file .env second_brain new "My brilliant idea"
```

Via the Python module:

```bash
uv run python -m second_brain new "My brilliant idea"
```

The CLI documents itself, including examples. Start with `uv run second_brain --help`, then `uv run second_brain <command> --help` (`new`, `list`, `show`). Results go to stdout and log lines to stderr, so output can be piped or captured safely.

## Interactive TUI

Run `second_brain` with no arguments to open a terminal UI:

```bash
uv run second_brain
```

The left sidebar is a scrollable list of your notes (newest first) with a **Create** button at the bottom; the right side is a markdown editor. Selecting a note shows it read-only. **Create** opens an empty draft with **Save** and **Cancel** buttons: the first line is the title, the rest is the body, and a leading `# ` on the title is fine. While a draft is open the list is locked, so it can't be lost by clicking another note.

| Key      | Action                   |
|----------|--------------------------|
| `↑` `↓`  | Move through the notes   |
| `Ctrl+N` | Create a note            |
| `Ctrl+S` | Save the draft           |
| `Esc`    | Cancel the draft         |
| `Ctrl+Q` | Quit                     |

When there is no terminal (output piped or run from a script), `second_brain` prints its help instead of starting the TUI. Log lines never go to the screen in TUI mode; they only go to the log file.

## Environment Variables

`.env.example` is the template — copy it to `.env` for development:

```bash
cp .env.example .env
```

- `LOG_LEVEL` — default: `INFO`. Set to `DEBUG` in `.env` for verbose console output.
- `LOG_FILE` — default: `app.log` inside the notes directory (never the current directory). Path to the log file: an absolute path is used as-is, a relative one is resolved against `SECOND_BRAIN_DIR`. The directory is created if missing.
- `SECOND_BRAIN_DIR` — default: `~/second_brain/`. Directory where notes are stored.

Note that `uv run --env-file .env` loads the dev environment explicitly (no auto-loading).

## Log Format

Console (stderr) lines are compact, with three-letter level names (`TRC`, `DBG`, `INF`, `SUC`, `WRN`, `ERR`, `CRT`):

```
2026-10-24 19:45:00 | INF | second_brain.app:main:29 | Hello from second_brain!
```

The log file (`LOG_FILE`) keeps loguru's default format with milliseconds. See [docs/usage.md](docs/usage.md#log-format) for details.

## Testing

Run tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov
```

## Documentation

Preview docs locally:

```bash
uv run python scripts/serve_docs.py
```

Build static docs:

```bash
uv run mkdocs build
```
