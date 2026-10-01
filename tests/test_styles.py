"""Pruebas unitarias para geocolumn.styles (colores y patrones)."""

from geocolumn.styles.colors import resolve_color
from geocolumn.styles.patterns import resolve_pattern


def test_resolve_color_finds_catalog_entry():
    assert resolve_color("gris_verdoso") == "#8c9c8c"


def test_resolve_color_is_accent_and_case_insensitive():
    assert resolve_color("Gris Verdoso") == resolve_color("gris_verdoso")


def test_resolve_color_returns_none_for_unknown():
    assert resolve_color("color_inventado_xyz") is None


def test_resolve_color_returns_none_for_empty():
    assert resolve_color(None) is None
    assert resolve_color("") is None


def test_resolve_pattern_finds_catalog_entry():
    pattern = resolve_pattern("607")
    assert pattern is not None
    assert pattern["name"] == "Massive sand or sandstone"


def test_resolve_pattern_returns_none_for_unknown_code():
    assert resolve_pattern("999") is None


def test_resolve_pattern_returns_none_for_empty():
    assert resolve_pattern(None) is None
