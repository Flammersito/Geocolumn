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


# --- Eje: altura (afloramiento) vs profundidad (sondaje) ---

def test_axis_is_inferred_as_depth_from_depth_fields():
    column = StratigraphicColumn.from_dicts([{"unit_id": "A1", "top_depth": 0, "base_depth": 5}])
    assert column.resolved_axis() == "depth"


def test_axis_is_inferred_as_height_from_height_fields_or_thickness_only():
    heights = StratigraphicColumn.from_dicts([{"unit_id": "A1", "base_height": 0, "top_height": 5}])
    thickness = StratigraphicColumn.from_dicts([{"unit_id": "A1", "thickness": 5}])
    assert heights.resolved_axis() == "height"
    assert thickness.resolved_axis() == "height"  # sin posiciones: se asume afloramiento


def test_resolve_positions_height_uses_explicit_heights():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "base_height": 0, "top_height": 4.5},
            {"unit_id": "A2", "base_height": 4.5, "top_height": 6},
        ]
    )
    assert column.resolve_positions() == [(0.0, 4.5), (4.5, 6.0)]


def test_resolve_positions_height_stacks_thickness_upward_from_base():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "thickness": 10}, {"unit_id": "A2", "thickness": 5}]
    )
    # la primera unidad es la más baja
    assert column.resolve_positions() == [(0.0, 10.0), (10.0, 15.0)]


def test_resolve_positions_depth_matches_resolve_depths():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5}, {"unit_id": "A2", "thickness": 3}]
    )
    assert column.resolve_positions() == column.resolve_depths()


def test_computed_thickness_from_heights():
    column = StratigraphicColumn.from_dicts([{"unit_id": "A1", "base_height": 2, "top_height": 9.5}])
    assert column[0].computed_thickness == 7.5


def test_mixing_depths_and_heights_raises():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "top_depth": 0, "base_depth": 5},
            {"unit_id": "A2", "base_height": 0, "top_height": 3},
        ]
    )
    with pytest.raises(ValueError, match="mezcla"):
        column.resolve_positions()


def test_explicit_axis_rejects_fields_of_the_other_kind():
    depth_data = [{"unit_id": "A1", "top_depth": 0, "base_depth": 5}]
    height_data = [{"unit_id": "A1", "base_height": 0, "top_height": 5}]
    with pytest.raises(ValueError, match="top_depth"):
        StratigraphicColumn.from_dicts(depth_data, axis="height").resolve_positions()
    with pytest.raises(ValueError, match="top_height"):
        StratigraphicColumn.from_dicts(height_data, axis="depth").resolve_positions()


def test_invalid_axis_raises_and_axis_is_case_insensitive():
    with pytest.raises(ValueError, match="no reconocido"):
        StratigraphicColumn.from_dicts([], axis="vertical")
    assert StratigraphicColumn.from_dicts([], axis="HEIGHT").axis == "height"


def test_inverted_extremes_raise_in_both_modes():
    with pytest.raises(ValueError, match="top_height"):
        StratigraphicColumn.from_dicts(
            [{"unit_id": "A1", "base_height": 5, "top_height": 2}]
        ).resolve_positions()
    with pytest.raises(ValueError, match="base_depth"):
        StratigraphicColumn.from_dicts(
            [{"unit_id": "A1", "top_depth": 5, "base_depth": 2}]
        ).resolve_positions()


def test_height_unit_without_enough_info_raises():
    column = StratigraphicColumn.from_dicts([{"unit_id": "A1"}], axis="height")
    with pytest.raises(ValueError, match="A1"):
        column.resolve_positions()


# --- Contactos y vetas ---

from geocolumn.core.models import ContactType, StratigraphicUnit


def test_contact_accepts_spanish_aliases_and_inferred():
    for text, expected in [
        ("neto", ContactType.SHARP), ("erosivo", ContactType.EROSIVE),
        ("falla", ContactType.FAULT), ("Inferido", ContactType.INFERRED),
        ("inferred", ContactType.INFERRED),
    ]:
        unit = StratigraphicUnit.from_dict({"unit_id": "A1", "top_contact": text})
        assert unit.top_contact == expected


def test_kind_defaults_to_unit_and_accepts_spanish():
    assert StratigraphicUnit.from_dict({"unit_id": "A1"}).kind == "unit"
    assert StratigraphicUnit.from_dict({"unit_id": "V1", "kind": "Veta"}).kind == "vein"


def test_invalid_kind_raises():
    with pytest.raises(ValueError, match="kind"):
        StratigraphicUnit.from_dict({"unit_id": "A1", "kind": "dique"})


def test_from_dicts_separates_veins_from_units():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "base_height": 0, "top_height": 10},
            {"unit_id": "V1", "kind": "vein", "base_height": 4, "thickness": 0.6},
        ]
    )
    assert len(column) == 1 and [v.unit_id for v in column.veins] == ["V1"]


def test_vein_positions_height_mode_from_thickness_or_top():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "base_height": 0, "top_height": 10},
            {"unit_id": "V1", "kind": "vein", "base_height": 4, "thickness": 0.6},
            {"unit_id": "V2", "kind": "vein", "base_height": 6, "top_height": 6.27},
        ]
    )
    (s1, e1), (s2, e2) = column.resolve_vein_positions()
    assert (s1, e1) == (4.0, pytest.approx(4.6))
    assert (s2, e2) == (6.0, pytest.approx(6.27))


def test_vein_positions_depth_mode():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "top_depth": 0, "base_depth": 10},
            {"unit_id": "V1", "kind": "vein", "top_depth": 3, "thickness": 0.5},
        ]
    )
    assert column.resolve_vein_positions() == [(3.0, 3.5)]


def test_vein_without_position_or_thickness_raises():
    base = {"unit_id": "A1", "base_height": 0, "top_height": 10}
    no_pos = StratigraphicColumn.from_dicts([base, {"unit_id": "V1", "kind": "vein", "thickness": 1}])
    no_thick = StratigraphicColumn.from_dicts([base, {"unit_id": "V2", "kind": "vein", "base_height": 3}])
    with pytest.raises(ValueError, match="V1"):
        no_pos.resolve_vein_positions()
    with pytest.raises(ValueError, match="V2"):
        no_thick.resolve_vein_positions()


def test_vein_with_depth_fields_in_height_column_raises():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "base_height": 0, "top_height": 10},
            {"unit_id": "V1", "kind": "vein", "top_depth": 3, "thickness": 0.5},
        ],
        axis="height",
    )
    with pytest.raises(ValueError, match="V1"):
        column.resolve_vein_positions()
