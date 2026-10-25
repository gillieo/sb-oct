"""CLI entry point using Click."""

from __future__ import annotations

import sys

import click
from loguru import logger

from second_brain.app import configure_logging
from second_brain.notes import create_note, list_note_files, notes_dir, read_note


def _interactive() -> bool:
    """Return True when stdin and stdout are both attached to a terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """second_brain -- capture and organise your thoughts.

    Notes are plain markdown files, stored in the directory named by the
    SECOND_BRAIN_DIR environment variable (default: ~/second_brain/).
    Run with no arguments to open the interactive TUI: notes on the left, a
    markdown editor on the right (Ctrl+N new note, Ctrl+S save, Esc cancel,
    Ctrl+Q quit). Without a terminal (piped or scripted) this help is printed
    instead.

    Commands print their result on stdout; log lines go to stderr. A debug
    log is also kept in app.log inside the notes directory; set LOG_FILE to
    move it (a relative path is resolved against the notes directory).

    \b
    Typical workflow:
      second_brain                        # open the TUI
      second_brain new "Caching idea"     # save a note, prints its path
      second_brain list                   # numbered list, newest first
      second_brain show 1                 # print note 1

    Run `second_brain COMMAND --help` for details and examples.
    """
    launch_tui = ctx.invoked_subcommand is None and _interactive()
    configure_logging(console=not launch_tui)
    if ctx.invoked_subcommand is None:
        if launch_tui:
            # Imported lazily so the plain commands never pay for Textual.
            from second_brain.tui import run

            run()
        else:
            click.echo(ctx.get_help())


@cli.command()
@click.argument("title")
@click.option(
    "--body",
    "-b",
    help="Note body (multi-line). Use '-' to read it from stdin.",
)
def new(title: str, body: str | None):
    """Create a new note with the given TITLE.

    Writes YYYY-MM-DD-<slug>.md to the notes directory and prints its path on
    stdout. An existing file is never overwritten; -1, -2, ... is appended.

    If TITLE contains newlines, the first line becomes the heading and the rest
    is added to the note body. Use --body for multi-line text, or `--body -`
    to read the body from stdin.

    \b
    Examples:
      second_brain new "Caching idea"
      second_brain new "Caching idea" --body $'Use an LRU.\\n\\nCheck limits.'
      cat draft.md | second_brain new "Draft" --body -
    """
    if body == "-":
        with click.open_file("-", encoding="utf-8") as stdin:
            body = stdin.read()
    base_dir = notes_dir()
    logger.debug("Creating note in {}", base_dir)
    path = create_note(title, base_dir, body=body)
    logger.info("Created note: {}", path)
    click.echo(path)


@cli.command("list")
def list_notes():
    """List all notes in the notes directory.

    Prints the notes directory, then one numbered line per note, newest first.
    Use these numbers with `second_brain show`.
    """
    base_dir = notes_dir()

    if not base_dir.is_dir():
        logger.warning("Notes directory does not exist: {}", base_dir)
        click.echo(f"Notes directory does not exist: {base_dir}")
        return

    files = list_note_files(base_dir)

    click.echo(f"Notes: {base_dir}")

    if not files:
        logger.info("No notes found in {}", base_dir)
        click.echo("No notes found.")
        return

    logger.debug("Found {} note(s) in {}", len(files), base_dir)
    for i, f in enumerate(files, 1):
        click.echo(f"{i}. {f.name}")


@cli.command()
@click.argument("number", type=int)
def show(number: int):
    """Display the contents of note NUMBER.

    NUMBER is the position shown by `second_brain list` (1 is the newest).
    Prints the note's markdown on stdout. If the notes directory is missing,
    empty or NUMBER is out of range, an error goes to stderr and the exit
    status is 1.

    \b
    Example:
      second_brain show 1
    """
    base_dir = notes_dir()

    if not base_dir.is_dir():
        logger.error("Notes directory does not exist: {}", base_dir)
        click.echo(f"Error: Notes directory does not exist: {base_dir}", err=True)
        raise SystemExit(1)

    files = list_note_files(base_dir)

    if not files:
        logger.error("No notes found in {}", base_dir)
        click.echo("Error: No notes found.", err=True)
        raise SystemExit(1)

    if number < 1 or number > len(files):
        logger.error("Note {} out of range ({} available)", number, len(files))
        click.echo(
            f"Error: Note {number} not found. Only {len(files)} notes available.",
            err=True,
        )
        raise SystemExit(1)

    logger.debug("Showing note {}: {}", number, files[number - 1].name)
    click.echo(read_note(files[number - 1]))
