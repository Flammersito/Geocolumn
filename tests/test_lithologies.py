"""Pruebas unitarias para geocolumn.styles.lithologies."""

import pytest

from geocolumn.styles.colors import resolve_color
from geocolumn.styles.lithologies import (
    DEFAULT_LITHOLOGIES,
    LithologyCatalog,
    LithologyStyle,
    default_catalog,
)
from geocolumn.styles.patterns import resolve_pattern


def test_every_default_color_exists_in_color_catalog():
    """Un typo en el color de una litología no debe pasar desapercibido."""
    for style in DEFAULT_LITHOLOGIES:
        if style.color is not None:
            assert resolve_color(style.color) is not None, style.key


def test_every_default_pattern_exists_in_pattern_catalog():
    for style in DEFAULT_LITHOLOGIES:
        if style.pattern is not None:
            assert resolve_pattern(style.pattern) is not None, style.key


def test_default_catalog_builds_without_name_clashes():
    catalog = default_catalog()
    assert len(catalog) == len(DEFAULT_LITHOLOGIES)


def test_get_is_accent_case_and_space_insensitive():
    catalog = default_catalog()
    assert catalog.get("Arenisca Tobácea") is catalog.get("arenisca_tobacea")
    assert catalog.get("arenisca_tobacea") is not None


def test_get_finds_english_aliases():
    catalog = default_catalog()
    assert catalog.get("sandstone") is catalog.get("arenisca")
    assert catalog.get("andesite") is catalog.get("andesita")


def test_get_returns_none_for_unknown_or_empty():
    catalog = default_catalog()
    assert catalog.get("litologia_inventada") is None
    assert catalog.get(None) is None
    assert catalog.get("") is None


def test_contains_operator():
    catalog = default_catalog()
    assert "caliza" in catalog
    assert "litologia_inventada" not in catalog


def test_register_adds_custom_lithology():
    catalog = default_catalog()
    catalog.register(LithologyStyle("skarn", "Skarn", "verde_oscuro", None, ("exoskarn",)))
    assert catalog.get("skarn").display_name == "Skarn"
    assert catalog.get("exoskarn") is catalog.get("skarn")


def test_register_raises_on_name_clash_unless_overwrite():
    catalog = default_catalog()
    duplicate = LithologyStyle("arenisca", "Otra arenisca", "rojo", "607")
    with pytest.raises(ValueError, match="arenisca"):
        catalog.register(duplicate)
    catalog.register(duplicate, overwrite=True)
    assert catalog.get("arenisca").display_name == "Otra arenisca"


def test_default_catalogs_are_independent_instances():
    first = default_catalog()
    first.register(LithologyStyle("skarn", "Skarn"))
    assert "skarn" not in default_catalog()


def test_hydrothermal_breccia_has_no_pattern():
    """No hay patrón FGDC para brecha hidrotermal: debe quedar sin patrón."""
    assert default_catalog().get("brecha_hidrotermal").pattern is None
