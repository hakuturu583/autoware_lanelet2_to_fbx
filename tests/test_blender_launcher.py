from __future__ import annotations

import sys

import pytest

from autoware_lanelet2_to_fbx import cli
from autoware_lanelet2_to_fbx.cli import BLENDER_BINARY_ARGS, ExportError, _blender_launcher


def _environment(monkeypatch, *, blender_bin=None, has_bpy, on_path):
    if blender_bin is None:
        monkeypatch.delenv("BLENDER_BIN", raising=False)
    else:
        monkeypatch.setenv("BLENDER_BIN", blender_bin)
    monkeypatch.setattr(cli.importlib.util, "find_spec", lambda name: object() if has_bpy else None)
    monkeypatch.setattr(cli.shutil, "which", lambda name: f"/usr/bin/{name}" if name in on_path else None)


def test_blender_bin_wins_over_bpy(monkeypatch):
    _environment(monkeypatch, blender_bin="my-blender", has_bpy=True, on_path={"my-blender"})
    assert _blender_launcher() == ["my-blender", *BLENDER_BINARY_ARGS]


def test_missing_blender_bin_is_an_error_even_with_bpy(monkeypatch):
    _environment(monkeypatch, blender_bin="missing-blender", has_bpy=True, on_path=set())
    with pytest.raises(ExportError, match="BLENDER_BIN"):
        _blender_launcher()


def test_bpy_runs_under_the_current_interpreter(monkeypatch):
    _environment(monkeypatch, has_bpy=True, on_path={"blender"})
    assert _blender_launcher() == [sys.executable]


def test_blender_on_path_is_the_fallback_without_bpy(monkeypatch):
    _environment(monkeypatch, has_bpy=False, on_path={"blender"})
    assert _blender_launcher() == ["blender", *BLENDER_BINARY_ARGS]


def test_no_blender_at_all_is_an_error(monkeypatch):
    _environment(monkeypatch, has_bpy=False, on_path=set())
    with pytest.raises(ExportError, match="bpy"):
        _blender_launcher()
