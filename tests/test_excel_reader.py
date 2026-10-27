"""Pruebas unitarias para geocolumn.io.excel_reader."""

import pandas as pd
import pytest

from geocolumn.core.models import ContactType
from geocolumn.io.excel_reader import read_column_from_excel


@pytest.fixture
def minimal_excel(tmp_path):
    """Crea un Excel mínimo con dos unidades, para pruebas rápidas."""
    path = tmp_path / "minimal.xlsx"
    df = pd.DataFrame(
        [
            {
                "unit_id": "A1",
                "top_depth_m": 0.0,
                "base_depth_m": 5.0,
                "lithology": "arenisca",
                "fossils": "Ammonites;Bivalvos",
                "hydrothermal_alteration": "propilitica;argilica",
                "top_contact": "sharp",
            },
            {
                "unit_id": "A2",
                "thickness_m": 3.0,  # sin profundidades, solo espesor
                "lithology": "lutita",
                "top_contact": "gradual",
            },
        ]
    )
    df.to_excel(path, index=False)
    return path


def test_read_column_returns_correct_number_of_units(minimal_excel):
    column = read_column_from_excel(minimal_excel)
    assert len(column) == 2


def test_thickness_is_computed_from_depths(minimal_excel):
    column = read_column_from_excel(minimal_excel)
    unit_a1 = next(u for u in column if u.unit_id == "A1")
    assert unit_a1.computed_thickness == 5.0


def test_thickness_falls_back_to_explicit_value(minimal_excel):
    column = read_column_from_excel(minimal_excel)
    unit_a2 = next(u for u in column if u.unit_id == "A2")
    assert unit_a2.top_depth is None
    assert unit_a2.base_depth is None
    assert unit_a2.computed_thickness == 3.0


def test_list_fields_are_parsed_correctly(minimal_excel):
    column = read_column_from_excel(minimal_excel)
    unit_a1 = next(u for u in column if u.unit_id == "A1")
    assert unit_a1.fossils == ["Ammonites", "Bivalvos"]
    assert unit_a1.hydrothermal_alteration == ["propilitica", "argilica"]


def test_missing_list_field_returns_empty_list(minimal_excel):
    column = read_column_from_excel(minimal_excel)
    unit_a2 = next(u for u in column if u.unit_id == "A2")
    assert unit_a2.fossils == []
    assert unit_a2.hydrothermal_alteration == []


def test_contact_type_is_parsed_correctly(minimal_excel):
    column = read_column_from_excel(minimal_excel)
    unit_a1 = next(u for u in column if u.unit_id == "A1")
    unit_a2 = next(u for u in column if u.unit_id == "A2")
    assert unit_a1.top_contact == ContactType.SHARP
    assert unit_a2.top_contact == ContactType.GRADUAL


def test_missing_unit_id_column_raises_error(tmp_path):
    path = tmp_path / "no_id.xlsx"
    df = pd.DataFrame([{"lithology": "arenisca"}])
    df.to_excel(path, index=False)

    with pytest.raises(ValueError, match="unit_id"):
        read_column_from_excel(path)


def test_invalid_contact_type_raises_error(tmp_path):
    path = tmp_path / "bad_contact.xlsx"
    df = pd.DataFrame([{"unit_id": "X1", "lithology": "arenisca", "top_contact": "xyz"}])
    df.to_excel(path, index=False)

    with pytest.raises(ValueError, match="no reconocido"):
        read_column_from_excel(path)


def test_default_contact_type_when_missing(tmp_path):
    """Si no se especifica top_contact, se asume contacto neto (SHARP)."""
    path = tmp_path / "no_contact.xlsx"
    df = pd.DataFrame([{"unit_id": "X1", "lithology": "arenisca"}])
    df.to_excel(path, index=False)

    column = read_column_from_excel(path)
    assert column[0].top_contact == ContactType.SHARP


def test_height_columns_are_read_and_axis_is_height(tmp_path):
    path = tmp_path / "heights.xlsx"
    pd.DataFrame(
        [
            {"unit_id": "B1", "base_height_m": 0.0, "top_height_m": 3.0, "lithology": "lutita"},
            {"unit_id": "B2", "base_height_m": 3.0, "top_height_m": 8.5, "lithology": "arenisca"},
        ]
    ).to_excel(path, index=False)

    column = read_column_from_excel(path)
    assert column.resolved_axis() == "height"
    assert column.resolve_positions() == [(0.0, 3.0), (3.0, 8.5)]


def test_explicit_axis_is_passed_to_the_column(tmp_path):
    path = tmp_path / "depths.xlsx"
    pd.DataFrame([{"unit_id": "A1", "thickness_m": 4.0}]).to_excel(path, index=False)
    assert read_column_from_excel(path, axis="depth").axis == "depth"


def test_kind_column_and_spanish_contact_are_read(tmp_path):
    path = tmp_path / "veins.xlsx"
    pd.DataFrame(
        [
            {"unit_id": "T1", "base_height_m": 0, "top_height_m": 10, "lithology": "pizarra",
             "top_contact": "inferido"},
            {"unit_id": "V1", "kind": "vein", "base_height_m": 4, "thickness_m": 0.15,
             "lithology": "veta_cuarzo"},
        ]
    ).to_excel(path, index=False)

    column = read_column_from_excel(path)
    assert len(column) == 1 and len(column.veins) == 1
    assert column[0].top_contact == ContactType.INFERRED
    assert column.resolve_vein_positions() == [(4.0, pytest.approx(4.15))]
