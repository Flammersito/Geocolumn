"""Pruebas unitarias para geocolumn.rendering.column_renderer."""

import matplotlib
matplotlib.use("Agg")  # backend sin pantalla, necesario para correr en pruebas

from geocolumn.core.column import StratigraphicColumn
from geocolumn.rendering.column_renderer import render_column


def _simple_column() -> StratigraphicColumn:
    return StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "top_depth": 0, "base_depth": 10, "lithology": "arenisca",
             "pattern": "607"},
            {"unit_id": "A2", "top_depth": 10, "base_depth": 18, "lithology": "lutita"},
            {"unit_id": "A3", "top_depth": 18, "base_depth": 25, "lithology": "arenisca",
             "pattern": "607"},  # misma litología que A1, debe compartir entrada de leyenda
        ],
        name="Columna de prueba",
    )


def test_render_column_draws_one_rectangle_per_unit():
    column = _simple_column()
    fig, (column_ax, legend_ax) = render_column(column)
    assert len(column_ax.patches) == len(column)


def test_render_column_legend_has_one_entry_per_unique_lithology():
    column = _simple_column()
    fig, (column_ax, legend_ax) = render_column(column)
    unique_lithologies = {unit.lithology for unit in column}
    assert len(legend_ax.patches) == len(unique_lithologies)


def test_render_column_sets_title_from_column_name():
    column = _simple_column()
    fig, _ = render_column(column)
    assert fig._suptitle.get_text() == "Columna de prueba"


def test_render_column_works_without_name():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca"}]
    )
    fig, (column_ax, legend_ax) = render_column(column)
    assert fig._suptitle is None
