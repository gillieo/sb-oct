"""Textual TUI: a note list beside a markdown editor."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, TextArea

from second_brain.notes import (
    create_note,
    list_note_files,
    notes_dir,
    read_note,
    strip_heading_marker,
)

EMPTY_HINT = "No notes yet. Click Create (Ctrl+N) to write your first one."
DRAFT_HINT = "Title on the first line, then the body. Markdown works."


class NoteItem(ListItem):
    """A row in the note list that remembers the file it stands for."""

    def __init__(self, path: Path) -> None:
        super().__init__(Label(path.stem, markup=False))
        self.path = path


class SecondBrainApp(App[None]):
    """Browse notes on the left; read or write them on the right.

    Selecting a note shows it read-only. Create switches the editor to an
    empty draft with Save and Cancel buttons. While a draft is open the note
    list and the Create button are disabled, so a draft is never lost by
    clicking another note.
    """

    TITLE = "second_brain"

    CSS = """
    #sidebar { width: 34; border-right: solid $primary; }
    #notes { height: 1fr; }
    #create { width: 100%; }
    #editor-pane { width: 1fr; }
    #editor { height: 1fr; }
    #edit-actions { height: auto; display: none; }
    #edit-actions Button { width: 1fr; }
    """

    BINDINGS = [
        Binding("ctrl+n", "create", "Create", priority=True),
        Binding("ctrl+s", "save", "Save", priority=True),
        Binding("escape", "cancel", "Cancel", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.editing = False
        self.current: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield ListView(id="notes")
                yield Button("Create", id="create", variant="primary")
            with Vertical(id="editor-pane"):
                yield TextArea(
                    "",
                    language="markdown",
                    read_only=True,
                    placeholder=EMPTY_HINT,
                    id="editor",
                )
                with Horizontal(id="edit-actions"):
                    yield Button("Save", id="save", variant="success")
                    yield Button("Cancel", id="cancel")
        yield Footer()

    async def on_mount(self) -> None:
        self.sub_title = str(notes_dir())
        await self.refresh_notes()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Offer Save and Cancel only while editing, Create only while not."""
        if action in ("save", "cancel"):
            return self.editing
        if action == "create":
            return not self.editing
        return True

    # -- note list -----------------------------------------------------------

    async def refresh_notes(self, select: Path | None = None) -> None:
        """Reload the list from disk and show `select` (default: the newest)."""
        files = list_note_files(notes_dir())
        note_list = self.query_one("#notes", ListView)
        await note_list.clear()
        await note_list.extend(NoteItem(f) for f in files)
        index = 0
        if select is not None:
            index = next((i for i, f in enumerate(files) if f.name == select.name), 0)
        if files:
            note_list.index = index
            self.show_note(files[index])
        else:
            self.show_note(None)

    def show_note(self, path: Path | None) -> None:
        """Load `path` into the read-only editor (blank when `path` is None)."""
        editor = self.query_one("#editor", TextArea)
        self.current = path
        if path is None:
            editor.load_text("")
            return
        try:
            editor.load_text(read_note(path))
        except (OSError, UnicodeDecodeError) as exc:
            logger.error("Could not read {}: {}", path, exc)
            self.notify(f"Could not read {path.name}: {exc}", severity="error")
            editor.load_text("")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if not self.editing and isinstance(event.item, NoteItem):
            self.show_note(event.item.path)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not self.editing and isinstance(event.item, NoteItem):
            self.show_note(event.item.path)

    # -- modes ---------------------------------------------------------------

    def set_editing(self, editing: bool) -> None:
        """Switch between the read-only view and the draft editor."""
        self.editing = editing
        editor = self.query_one("#editor", TextArea)
        editor.read_only = not editing
        editor.placeholder = DRAFT_HINT if editing else EMPTY_HINT
        self.query_one("#edit-actions").display = editing
        self.query_one("#create", Button).disabled = editing
        self.query_one("#notes", ListView).disabled = editing
        self.refresh_bindings()
        if editing:
            editor.focus()
        else:
            self.query_one("#notes", ListView).focus()

    async def action_create(self) -> None:
        if self.editing:
            return
        self.set_editing(True)
        self.query_one("#editor", TextArea).load_text("")
        logger.debug("Editing a new note")

    async def action_cancel(self) -> None:
        if not self.editing:
            return
        self.set_editing(False)
        self.show_note(self.current)
        logger.debug("Discarded the draft")

    async def action_save(self) -> None:
        if not self.editing:
            return
        text = strip_heading_marker(self.query_one("#editor", TextArea).text)
        if not text.strip():
            self.notify("Nothing to save: write a title first.", severity="warning")
            return
        try:
            path = create_note(text, notes_dir())
        except OSError as exc:
            # Stay in edit mode so the draft is not lost.
            logger.error("Could not save note: {}", exc)
            self.notify(f"Could not save note: {exc}", severity="error")
            return
        logger.info("Created note: {}", path)
        self.notify(f"Saved {path.name}")
        self.set_editing(False)
        await self.refresh_notes(select=path)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "create":
                await self.action_create()
            case "save":
                await self.action_save()
            case "cancel":
                await self.action_cancel()


def run() -> None:
    """Start the TUI and block until the user quits."""
    SecondBrainApp().run()
