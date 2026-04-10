import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.filesystem import LocalFileSystemTool
from src.agents.workers import _is_path_in_workspace


def test_filesystem_commonpath_guard(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    fs = LocalFileSystemTool(str(root))

    ok = fs._get_path("docs/a.txt")
    assert str(ok).startswith(str(root))

    try:
        fs._get_path("../root-evil/steal.txt")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_worker_workspace_guard_prefix_escape(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    assert _is_path_in_workspace("docs/a.txt", str(root)) is True
    assert _is_path_in_workspace("../work-evil/file.txt", str(root)) is False

