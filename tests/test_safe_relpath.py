"""Tests for cambium_io.safe_relpath -- the cross-drive-safe relpath helper.

On Windows, os.path.relpath raises ValueError when the target and the start
directory live on different drives (e.g. input on D:, CWD on C:). Four tools
(budget_review, budget_narrative_match, checklist_builder, solicitation_explainer)
use this helper to build a display-only label without crashing. These tests run
offline, use only stdlib + tmp dirs, and simulate the cross-drive case by
monkeypatching os.path.relpath to raise ValueError (so they behave the same on
Linux CI and on Windows).
"""
import os
import sys
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "tools"))

import cambium_io


def test_safe_relpath_returns_relative_path_normally():
    """Normal case: same result as os.path.relpath for a path under the start dir."""
    base = tempfile.mkdtemp()
    target = os.path.join(base, "sub", "file.txt")
    assert cambium_io.safe_relpath(target, start=base) == os.path.join("sub", "file.txt")


def test_safe_relpath_default_start_matches_os_relpath():
    """With start=None the helper mirrors os.path.relpath(path) against the CWD."""
    p = os.path.join(os.getcwd(), "some", "nested", "thing.json")
    assert cambium_io.safe_relpath(p) == os.path.relpath(p)


def test_safe_relpath_does_not_raise_on_cross_drive(monkeypatch):
    """Cross-drive (ValueError) must be swallowed and fall back to the absolute path."""
    def _boom(*_a, **_k):
        raise ValueError("path is on mount 'D:', start on mount 'C:'")

    monkeypatch.setattr(os.path, "relpath", _boom)
    weird = os.path.join("D:", "data", "rules.json") if os.name == "nt" else "/mnt/d/data/rules.json"
    # Must not raise, and must return the absolute path as the cosmetic fallback.
    result = cambium_io.safe_relpath(weird)
    assert result == os.path.abspath(weird)


def test_safe_relpath_cross_drive_with_explicit_start(monkeypatch):
    """The ValueError fallback also applies when an explicit start is passed."""
    def _boom(*_a, **_k):
        raise ValueError("different drives")

    monkeypatch.setattr(os.path, "relpath", _boom)
    p = "/some/other/place/budget.json"
    assert cambium_io.safe_relpath(p, start="/unrelated/start") == os.path.abspath(p)
