"""Pruebas de integración: el ejemplo del repositorio debe seguir funcionando."""

import warnings
from pathlib import Path

import pytest

import matplotlib

matplotlib.use("Agg")

from geocolumn.io.excel_reader import read_column_from_excel
from geocolumn.rendering.column_renderer import render_column

EXAMPLE = Path(__file__).parent.parent / "examples" / "ejemplo_volcanosedimentario.xlsx"


def test_example_excel_reads_all_units():
    column = read_column_from_excel(EXAMPLE)
    assert len(column) == 8
    assert column.resolved_axis() == "depth"  # estilo sondaje
    assert column[4].unit_id == "U5"
    assert column[4].computed_thickness == 15


def test_example_renders_without_warnings():
    """Si algún litología/patrón del ejemplo dejara de existir, esta prueba falla."""
    column = read_column_from_excel(EXAMPLE, name="Ejemplo")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fig, (column_ax, legend_ax) = render_column(column)
    assert len(column_ax.patches) >= len(column)  # unidades + franjas de alteración


SEDIMENTARY = Path(__file__).parent.parent / "examples" / "ejemplo_sedimentario.xlsx"


@pytest.mark.parametrize(
    "sheet, scale, n_units",
    [("Siliciclastica", "siliciclastic", 12), ("Carbonatos", "carbonate", 11)],
)
def test_sedimentary_examples_render_without_warnings(sheet, scale, n_units):
    """Toda granulometría escrita en el ejemplo debe existir en su escala."""
    column = read_column_from_excel(SEDIMENTARY, sheet_name=sheet)
    assert len(column) == n_units
    assert column.resolved_axis() == "height"  # estilo afloramiento
    assert column.resolve_positions()[0][0] == 0.0  # la primera unidad está en la base
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, (column_ax, _) = render_column(column, grain_scale=scale)
    widths = [p.get_width() for p in column_ax.patches]
    assert len(set(widths)) > 1  # el perfil realmente varía


THESIS = Path(__file__).parent.parent / "examples" / "ejemplo_tesis.xlsx"


def test_thesis_example_has_three_units_three_veins_and_inferred_contacts():
    from geocolumn.core.models import ContactType

    column = read_column_from_excel(THESIS)
    assert [u.lithology for u in column] == ["esquisto", "pizarra", "andesita"]
    assert [round(e - s, 2) for s, e in column.resolve_positions()] == [30.0, 15.0, 60.0]
    assert column[0].top_contact == column[1].top_contact == ContactType.INFERRED
    assert sorted(round(e - s, 2) for s, e in column.resolve_vein_positions()) == [0.15, 0.27, 0.6]


def test_thesis_example_renders_without_warnings():
    column = read_column_from_excel(THESIS, name="Tesis")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, (column_ax, legend_ax) = render_column(column)
    texts = [t.get_text() for t in legend_ax.texts]
    assert "Contacto inferido" in texts and "Veta de cuarzo" in texts
