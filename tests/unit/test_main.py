"""Tests for main module helpers."""

from pathlib import Path

from bot.config.constants import PROJECT_ROOT
from bot.main import _find_session


def _move_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.replace(destination)


def test_find_session_finds_project_root_file_from_other_cwd(
    tmp_path,
    monkeypatch,
) -> None:
    root_session_path = PROJECT_ROOT / "userbot.session"
    data_session_path = PROJECT_ROOT / "data" / "userbot.session"
    root_backup = tmp_path / "userbot.session.backup"
    data_backup = tmp_path / "data-userbot.session.backup"

    _move_if_exists(root_session_path, root_backup)
    _move_if_exists(data_session_path, data_backup)
    root_session_path.write_bytes(b"test-session")

    try:
        monkeypatch.chdir(tmp_path)
        found = _find_session()
        assert found == root_session_path
    finally:
        root_session_path.unlink(missing_ok=True)
        _move_if_exists(root_backup, root_session_path)
        _move_if_exists(data_backup, data_session_path)


def test_find_session_returns_none_when_no_known_session_exists(
    tmp_path,
    monkeypatch,
) -> None:
    root_session_path = PROJECT_ROOT / "userbot.session"
    data_session_path = PROJECT_ROOT / "data" / "userbot.session"
    root_backup = tmp_path / "userbot.session.backup"
    data_backup = tmp_path / "data-userbot.session.backup"

    _move_if_exists(root_session_path, root_backup)
    _move_if_exists(data_session_path, data_backup)

    try:
        monkeypatch.chdir(tmp_path)
        assert _find_session() is None
    finally:
        _move_if_exists(root_backup, root_session_path)
        _move_if_exists(data_backup, data_session_path)
