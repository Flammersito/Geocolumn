"""Pruebas unitarias para geocolumn.core.column.StratigraphicColumn."""

import pytest

from geocolumn.core.column import StratigraphicColumn
from geocolumn.core.models import ContactType


def test_from_dicts_builds_units_in_order():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "top_depth": 0, "base_depth": 15, "lithology": "andesita"},
            {"unit_id": "A2", "top_depth": 15, "base_depth": 28, "lithology": "brecha_volcanica"},
        ]
    )
    assert len(column) == 2
    assert [u.unit_id for u in column] == ["A1", "A2"]


def test_from_dicts_accepts_semicolon_lists_like_excel():
    column = StratigraphicColumn.from_dicts(
        [
            {
                "unit_id": "A1",
                "lithology": "brecha_hidrotermal",
                "hydrothermal_alteration": "silicificacion;argilica_avanzada",
                "top_contact": "fault",
            }
        ]
    )
    unit = column[0]
    assert unit.hydrothermal_alteration == ["silicificacion", "argilica_avanzada"]
    assert unit.top_contact == ContactType.FAULT


def test_from_dicts_accepts_native_python_lists():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "fossils": ["Ammonites", "Bivalvos"]}]
    )
    assert column[0].fossils == ["Ammonites", "Bivalvos"]


def test_from_dicts_computes_thickness():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 10, "base_depth": 22.5}]
    )
    assert column[0].computed_thickness == 12.5


def test_from_dicts_raises_on_missing_unit_id():
    with pytest.raises(ValueError, match="unit_id"):
        StratigraphicColumn.from_dicts([{"lithology": "andesita"}])


def test_resolve_depths_uses_explicit_depths_when_present():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 5, "base_depth": 12}]
    )
    assert column.resolve_depths() == [(5.0, 12.0)]


def test_resolve_depths_infers_continuity_from_thickness():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "thickness": 10},
            {"unit_id": "A2", "thickness": 5},
        ]
    )
    assert column.resolve_depths() == [(0.0, 10.0), (10.0, 15.0)]


def test_resolve_depths_raises_without_enough_info():
    column = StratigraphicColumn.from_dicts([{"unit_id": "A1"}])
    with pytest.raises(ValueError, match="A1"):
        column.resolve_depths()


def test_column_supports_indexing_and_naming():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1"}, {"unit_id": "A2"}], name="Sondaje DDH-01"
    )
    assert column.name == "Sondaje DDH-01"
    assert column[1].unit_id == "A2"
