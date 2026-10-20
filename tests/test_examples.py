"""Pruebas de integración: el ejemplo del repositorio debe seguir funcionando."""

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from geocolumn.io.excel_reader import read_column_from_excel
from geocolumn.rendering.column_renderer import render_column

EXAMPLE = Path(__file__).parent.parent / "examples" / "ejemplo_volcanosedimentario.xlsx"


def test_example_excel_reads_all_units():
    column = read_column_from_excel(EXAMPLE)
    assert len(column) == 8
    assert column[4].unit_id == "U5"
    assert column[4].computed_thickness == 15


def test_example_renders_without_warnings():
    """Si algún litología/patrón del ejemplo dejara de existir, esta prueba falla."""
    column = read_column_from_excel(EXAMPLE, name="Ejemplo")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        fig, (column_ax, legend_ax) = render_column(column)
    assert len(column_ax.patches) >= len(column)  # unidades + franjas de alteración
