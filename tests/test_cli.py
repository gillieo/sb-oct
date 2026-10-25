"""Tests for the CLI (Click group + new subcommand)."""

import re
from pathlib import Path

from click.testing import CliRunner

from second_brain.cli import cli

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

runner = CliRunner()


# ---------------------------------------------------------------------------
# new subcommand
# ---------------------------------------------------------------------------


def test_cli_new_creates_file(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Test idea"])
    assert result.exit_code == 0
    files = list(tmp_note_dir.glob("*.md"))
    assert len(files) == 1


def test_cli_new_prints_path_to_stdout(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Test idea"])
    assert result.exit_code == 0
    output = result.output.strip().splitlines()[-1]
    assert output.endswith(".md")
    assert Path(output).is_file()


def test_cli_new_uses_env_var_for_dir(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Test idea"])
    assert result.exit_code == 0
    assert tmp_note_dir.is_dir()
    files = list(tmp_note_dir.glob("*.md"))
    assert len(files) == 1


def test_cli_new_default_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("SECOND_BRAIN_DIR", raising=False)
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    result = runner.invoke(cli, ["new", "Test idea"])
    assert result.exit_code == 0
    expected_dir = fake_home / "second_brain"
    assert expected_dir.is_dir()
    files = list(expected_dir.glob("*.md"))
    assert len(files) == 1


def test_cli_new_missing_title_shows_error():
    result = runner.invoke(cli, ["new"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_cli_new_file_content_has_heading(tmp_note_dir):
    result = runner.invoke(cli, ["new", "My heading test"])
    assert result.exit_code == 0
    md_file = next(tmp_note_dir.glob("*.md"))
    lines = md_file.read_text().splitlines()
    assert lines[0] == "# My heading test"


def test_cli_new_file_content_has_timestamp(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Timestamp test"])
    assert result.exit_code == 0
    md_file = next(tmp_note_dir.glob("*.md"))
    text = md_file.read_text()
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", text)


# ---------------------------------------------------------------------------
# help
# ---------------------------------------------------------------------------


def test_cli_group_help():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "second_brain" in result.output or "capture" in result.output


def test_cli_new_help():
    result = runner.invoke(cli, ["new", "--help"])
    assert result.exit_code == 0
    assert "TITLE" in result.output


def test_cli_new_folds_accents_in_filename(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Café über Ideen"])
    assert result.exit_code == 0
    assert "cafe-uber-ideen" in next(tmp_note_dir.glob("*.md")).name


# ---------------------------------------------------------------------------
# list subcommand
# ---------------------------------------------------------------------------


def test_cli_list_shows_directory_header(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260322-note.md").write_text("# Note\n")
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert f"Notes: {tmp_note_dir}" in result.output


def test_cli_list_shows_numbered_files(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260320-a.md").write_text("# A\n")
    (tmp_note_dir / "20260321-b.md").write_text("# B\n")
    (tmp_note_dir / "20260322-c.md").write_text("# C\n")
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "1." in result.output
    assert "2." in result.output
    assert "3." in result.output


def test_cli_list_sorted_newest_first(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260320-old.md").write_text("# Old\n")
    (tmp_note_dir / "20260322-new.md").write_text("# New\n")
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    numbered = [ln for ln in lines if re.match(r"^\d+\.", ln)]
    assert "20260322-new.md" in numbered[0]
    assert "20260320-old.md" in numbered[1]


def test_cli_list_empty_directory(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No notes found" in result.output


def test_cli_list_missing_directory(tmp_note_dir):
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "does not exist" in result.output


def test_cli_list_ignores_non_md_files(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260322-note.md").write_text("# Note\n")
    (tmp_note_dir / "20260322-other.txt").write_text("not a note\n")
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "20260322-note.md" in result.output
    assert "20260322-other.txt" not in result.output


def test_cli_list_help():
    result = runner.invoke(cli, ["list", "--help"])
    assert result.exit_code == 0
    assert "List" in result.output or "list" in result.output


# ---------------------------------------------------------------------------
# show subcommand
# ---------------------------------------------------------------------------


def test_cli_show_prints_file_content(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260322-note.md").write_text("# My Note\n\n2026-03-22T14:30:00\n")
    result = runner.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "# My Note" in result.output
    assert "2026-03-22T14:30:00" in result.output


def test_cli_show_correct_note_by_number(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260320-old.md").write_text("# Old\n")
    (tmp_note_dir / "20260322-new.md").write_text("# New\n")
    result1 = runner.invoke(cli, ["show", "1"])
    assert result1.exit_code == 0
    assert "# New" in result1.output
    result2 = runner.invoke(cli, ["show", "2"])
    assert result2.exit_code == 0
    assert "# Old" in result2.output


def test_cli_show_out_of_range(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260322-a.md").write_text("# A\n")
    (tmp_note_dir / "20260321-b.md").write_text("# B\n")
    result = runner.invoke(cli, ["show", "99"])
    assert result.exit_code != 0
    assert "Note 99 not found" in result.output
    assert "2 notes available" in result.output


def test_cli_show_zero_index(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260322-note.md").write_text("# Note\n")
    result = runner.invoke(cli, ["show", "0"])
    assert result.exit_code != 0


def test_cli_show_missing_directory(tmp_note_dir):
    result = runner.invoke(cli, ["show", "1"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_cli_show_empty_directory(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    result = runner.invoke(cli, ["show", "1"])
    assert result.exit_code != 0
    assert "No notes found" in result.output


def test_cli_show_roundtrips_unicode_content(tmp_note_dir):
    created = runner.invoke(cli, ["new", "Café über Ideen 日本"])
    assert created.exit_code == 0
    result = runner.invoke(cli, ["show", "1"])
    assert result.exit_code == 0
    assert "Café über Ideen 日本" in result.output


def test_cli_show_help():
    result = runner.invoke(cli, ["show", "--help"])
    assert result.exit_code == 0
    assert "NUMBER" in result.output


def test_cli_show_missing_argument():
    result = runner.invoke(cli, ["show"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_cli_show_matches_list_numbering(tmp_note_dir):
    tmp_note_dir.mkdir(parents=True)
    (tmp_note_dir / "20260320-a.md").write_text("# A\n")
    (tmp_note_dir / "20260321-b.md").write_text("# B\n")
    (tmp_note_dir / "20260322-c.md").write_text("# C\n")
    listing = runner.invoke(cli, ["list"]).output
    for n, heading in [(1, "# C"), (2, "# B"), (3, "# A")]:
        assert f"{n}. " in listing
        assert heading in runner.invoke(cli, ["show", str(n)]).output


# ---------------------------------------------------------------------------
# multi-line notes
# ---------------------------------------------------------------------------


def test_cli_new_body_option(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Idea", "--body", "line1\nline2"])
    assert result.exit_code == 0
    text = next(tmp_note_dir.glob("*.md")).read_text()
    assert text.startswith("# Idea\n\nline1\nline2\n\n")


def test_cli_new_body_from_stdin(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Idea", "--body", "-"], input="a\nb\n")
    assert result.exit_code == 0
    text = next(tmp_note_dir.glob("*.md")).read_text()
    assert text.startswith("# Idea\n\na\nb\n\n")


def test_cli_new_without_body_does_not_read_stdin(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Idea"], input="ignored\n")
    assert result.exit_code == 0
    assert "ignored" not in next(tmp_note_dir.glob("*.md")).read_text()


def test_cli_new_multiline_title_is_split(tmp_note_dir):
    result = runner.invoke(cli, ["new", "Head\n\nTail text"])
    assert result.exit_code == 0
    note = next(tmp_note_dir.glob("*.md"))
    assert note.name.endswith("-head.md")
    assert note.read_text().startswith("# Head\n\nTail text\n\n")


def test_cli_new_multiline_note_roundtrips_through_show(tmp_note_dir):
    runner.invoke(cli, ["new", "Head", "--body", "p1\n\np2"])
    result = runner.invoke(cli, ["show", "1"])
    assert "# Head" in result.output
    assert "p1\n\np2" in result.output


def test_cli_new_help_mentions_body():
    result = runner.invoke(cli, ["new", "--help"])
    assert "--body" in result.output


# ---------------------------------------------------------------------------
# help text (the CLI's own documentation, for people and agents)
# ---------------------------------------------------------------------------


def test_cli_group_help_lists_commands_and_env_vars():
    out = runner.invoke(cli, ["--help"]).output
    for command in ("new", "list", "show"):
        assert command in out
    assert "SECOND_BRAIN_DIR" in out
    assert "~/second_brain" in out
    assert "stderr" in out


def test_cli_group_help_has_workflow_example():
    out = runner.invoke(cli, ["--help"]).output
    assert 'second_brain new "' in out
    assert "second_brain list" in out
    assert "second_brain show 1" in out


def test_cli_new_help_has_multiline_examples():
    out = runner.invoke(cli, ["new", "--help"]).output
    assert "Examples:" in out
    assert "--body $'" in out
    assert "--body -" in out
    assert "stdout" in out


def test_cli_new_help_keeps_example_line_breaks():
    out = runner.invoke(cli, ["new", "--help"]).output
    lines = [ln.strip() for ln in out.splitlines()]
    assert any(ln.startswith("second_brain new ") for ln in lines)
    assert any(ln.startswith("cat ") and "--body -" in ln for ln in lines)


def test_cli_list_help_explains_numbering():
    out = runner.invoke(cli, ["list", "--help"]).output
    assert "newest first" in out
    assert "show" in out


def test_cli_show_help_explains_number_and_errors():
    out = runner.invoke(cli, ["show", "--help"]).output
    assert "second_brain list" in out
    assert "exit" in out.lower()
    assert "stderr" in out
