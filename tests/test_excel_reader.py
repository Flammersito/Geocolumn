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
    df = pd.DataFrame([{"unit_id": "X1", "lithology": "arenisca", "top_contact": "neto"}])
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
