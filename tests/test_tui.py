"""Tests for the Textual TUI (driven headlessly with Textual's Pilot)."""

import pytest
from textual.widgets import Button, ListView, TextArea

from second_brain.notes import list_note_files
from second_brain.tui import NoteItem, SecondBrainApp


@pytest.fixture
def notes(tmp_note_dir):
    """Two notes on disk, `New` being the newest."""
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "2026-03-20-old.md").write_text("# Old\n\n2026-03-20T09:00:00\n")
    (tmp_note_dir / "2026-03-22-new.md").write_text("# New\n\n2026-03-22T09:00:00\n")
    return tmp_note_dir


def names(app):
    return [item.path.name for item in app.query(NoteItem)]


def editor_of(app):
    return app.query_one("#editor", TextArea)


# ---------------------------------------------------------------------------
# note list and read-only view
# ---------------------------------------------------------------------------


async def test_lists_notes_newest_first(notes):
    app = SecondBrainApp()
    async with app.run_test():
        assert names(app) == ["2026-03-22-new.md", "2026-03-20-old.md"]


async def test_newest_note_is_shown_read_only_on_start(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert "# New" in editor_of(app).text
        assert editor_of(app).read_only


async def test_arrow_keys_show_the_highlighted_note(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.press("down")
        await pilot.pause()
        assert "# Old" in editor_of(app).text
        assert editor_of(app).read_only


async def test_clicking_a_note_shows_its_content(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#notes NoteItem:last-child")
        await pilot.pause()
        assert "# Old" in editor_of(app).text


async def test_read_only_view_rejects_typing(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        before = editor_of(app).text
        editor_of(app).focus()
        await pilot.press("x", "y", "z")
        assert editor_of(app).text == before


async def test_empty_notes_dir_shows_hint(tmp_note_dir):
    app = SecondBrainApp()
    async with app.run_test():
        assert names(app) == []
        assert editor_of(app).text == ""
        assert editor_of(app).read_only
        assert "Create" in str(editor_of(app).placeholder)


async def test_note_deleted_after_listing_does_not_crash(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        (notes / "2026-03-20-old.md").unlink()
        await pilot.press("down")
        await pilot.pause()
        assert editor_of(app).text == ""


# ---------------------------------------------------------------------------
# layout
# ---------------------------------------------------------------------------


async def test_sidebar_is_left_of_editor_and_create_is_below_the_list(notes):
    app = SecondBrainApp()
    async with app.run_test(size=(100, 30)):
        sidebar = app.query_one("#sidebar")
        pane = app.query_one("#editor-pane")
        note_list = app.query_one("#notes", ListView)
        create = app.query_one("#create", Button)
        assert sidebar.region.right <= pane.region.x
        assert create.region.y >= note_list.region.bottom
        assert create.region.bottom <= app.screen.size.height


async def test_long_list_scrolls_and_create_stays_visible(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    for i in range(60):
        (tmp_note_dir / f"2026-01-01-note-{i:03d}.md").write_text(f"# Note {i}\n")
    app = SecondBrainApp()
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        assert app.query_one("#notes", ListView).max_scroll_y > 0
        assert app.query_one("#create", Button).region.bottom <= app.screen.size.height


# ---------------------------------------------------------------------------
# create / save / cancel
# ---------------------------------------------------------------------------


async def test_save_and_cancel_buttons_are_hidden_until_create(notes):
    app = SecondBrainApp()
    async with app.run_test():
        assert app.query_one("#edit-actions").display is False


async def test_create_switches_to_empty_edit_mode(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        await pilot.pause()
        assert not editor_of(app).read_only
        assert editor_of(app).text == ""
        assert editor_of(app).has_focus
        assert app.query_one("#edit-actions").display is True
        assert app.query_one("#save", Button).label.plain == "Save"
        assert app.query_one("#cancel", Button).label.plain == "Cancel"


async def test_list_and_create_are_locked_while_editing(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        await pilot.pause()
        assert app.query_one("#notes", ListView).disabled
        assert app.query_one("#create", Button).disabled


async def test_typing_in_edit_mode_fills_the_editor(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        await pilot.press(*"hello")
        assert editor_of(app).text == "hello"


async def test_cancel_discards_draft_and_restores_view(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.press("down")
        await pilot.pause()
        await pilot.click("#create")
        editor_of(app).text = "draft that is thrown away"
        await pilot.click("#cancel")
        await pilot.pause()
        assert editor_of(app).read_only
        assert "# Old" in editor_of(app).text
        assert app.query_one("#edit-actions").display is False
        assert not app.query_one("#notes", ListView).disabled
        assert not app.query_one("#create", Button).disabled
        assert len(list_note_files(notes)) == 2


async def test_save_creates_the_note_and_shows_it(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        editor_of(app).text = "Caching idea\n\nUse an LRU."
        await pilot.click("#save")
        await pilot.pause()
        created = [f for f in list_note_files(notes) if "caching-idea" in f.name]
        assert len(created) == 1
        assert created[0].read_text().startswith("# Caching idea\n\nUse an LRU.\n\n")
        assert created[0].name in names(app)
        assert editor_of(app).read_only
        assert "# Caching idea" in editor_of(app).text
        assert app.query_one("#notes", ListView).highlighted_child.path.name == (
            created[0].name
        )
        assert app.query_one("#edit-actions").display is False


async def test_save_strips_a_typed_markdown_heading_marker(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        editor_of(app).text = "# Heading\n\nBody"
        await pilot.click("#save")
        await pilot.pause()
        created = [f for f in list_note_files(notes) if f.name.endswith("-heading.md")]
        assert len(created) == 1
        assert created[0].read_text().startswith("# Heading\n\nBody\n\n")


@pytest.mark.parametrize("draft", ["", "   \n\n", "# "])
async def test_saving_a_blank_note_keeps_editing(notes, draft):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        editor_of(app).text = draft
        await pilot.click("#save")
        await pilot.pause()
        assert not editor_of(app).read_only
        assert len(list_note_files(notes)) == 2


async def test_first_note_can_be_created_in_a_fresh_notes_dir(tmp_note_dir):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        editor_of(app).text = "First thought"
        await pilot.click("#save")
        await pilot.pause()
        assert len(list_note_files(tmp_note_dir)) == 1
        assert len(names(app)) == 1


async def test_failed_save_keeps_the_draft(tmp_path, monkeypatch):
    blocker = tmp_path / "afile"
    blocker.write_text("not a directory")
    monkeypatch.setenv("SECOND_BRAIN_DIR", str(blocker))
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.click("#create")
        editor_of(app).text = "precious draft"
        await pilot.click("#save")
        await pilot.pause()
        assert not editor_of(app).read_only
        assert editor_of(app).text == "precious draft"


# ---------------------------------------------------------------------------
# keyboard shortcuts
# ---------------------------------------------------------------------------


async def test_ctrl_n_ctrl_s_create_and_save(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+n")
        assert not editor_of(app).read_only
        editor_of(app).text = "Keyboard note"
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert any("keyboard-note" in f.name for f in list_note_files(notes))
        assert editor_of(app).read_only


async def test_escape_cancels_editing(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+n")
        editor_of(app).text = "abandoned"
        await pilot.press("escape")
        await pilot.pause()
        assert editor_of(app).read_only
        assert len(list_note_files(notes)) == 2


async def test_ctrl_s_and_escape_do_nothing_outside_edit_mode(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+s", "escape")
        await pilot.pause()
        assert editor_of(app).read_only
        assert len(list_note_files(notes)) == 2


async def test_quit_is_listed_in_the_footer_in_both_modes(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        assert app.active_bindings["ctrl+q"].binding.show
        await pilot.press("ctrl+n")
        assert app.active_bindings["ctrl+q"].binding.show


async def test_ctrl_q_quits(notes):
    app = SecondBrainApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+q")
        await pilot.pause()
    assert not app.is_running


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------


def test_run_starts_the_app(monkeypatch):
    started = []
    monkeypatch.setattr(SecondBrainApp, "run", lambda self: started.append(self))
    from second_brain.tui import run

    run()
    assert len(started) == 1
