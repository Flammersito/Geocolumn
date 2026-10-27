"""Lectura de columnas estratigráficas desde archivos Excel.

Este módulo traduce un archivo .xlsx con la estructura de columnas
esperada (ver plantilla de ejemplo del proyecto) en un `StratigraphicColumn`.

Convención de listas dentro de una celda: los campos que representan
listas (estructuras sedimentarias, fósiles, muestras, alteración,
mineralización, fotos) se escriben en una sola celda separando los
valores con punto y coma (`;`). Ejemplo: "Ammonites;Bivalvos".

Toda la validación y el parseo real vive en `StratigraphicUnit.from_dict`;
este módulo solo se encarga de leer el Excel y normalizar cada fila a un
diccionario "limpio" (sin NaN, con los nombres de columna que el modelo
espera) antes de delegar la construcción de la unidad.
"""

import pandas as pd

from geocolumn.core.column import StratigraphicColumn
from geocolumn.core.models import StratigraphicUnit

# Columnas de Excel cuyo nombre incluye la unidad de medida (para claridad
# en la hoja de cálculo) pero que en el modelo de datos no la llevan.
EXCEL_TO_MODEL_KEYS = {
    "top_depth_m": "top_depth",
    "base_depth_m": "base_depth",
    "thickness_m": "thickness",
    "top_height_m": "top_height",
    "base_height_m": "base_height",
}


def _row_to_dict(row: pd.Series) -> dict:
    """Convierte una fila de pandas en un dict plano, reemplazando NaN por None."""
    raw = row.to_dict()
    clean = {key: (None if pd.isna(value) else value) for key, value in raw.items()}
    for excel_key, model_key in EXCEL_TO_MODEL_KEYS.items():
        if excel_key in clean:
            clean[model_key] = clean.pop(excel_key)
    return clean


def read_column_from_excel(
    path: str,
    sheet_name: str | int = 0,
    name: str | None = None,
    axis: str | None = None,
) -> StratigraphicColumn:
    """Lee un archivo Excel y devuelve la columna estratigráfica completa.

    Args:
        path: Ruta al archivo .xlsx.
        sheet_name: Nombre o índice de la hoja a leer (por defecto, la primera).
        name: Nombre opcional para la columna resultante.
        axis: `"height"` (altura desde la base, columnas de afloramiento),
            `"depth"` (profundidad, sondajes) o `None` para deducirlo de
            las columnas del Excel (`*_height_m` o `*_depth_m`).

    Returns:
        Un `StratigraphicColumn` con las unidades en el mismo orden en que
        aparecen las filas en el Excel. Las filas con `kind` = `vein`
        (o `veta`) quedan aparte, en `column.veins`.

    Raises:
        ValueError: Si falta la columna obligatoria `unit_id`, o si algún
            tipo de contacto no es reconocido.
    """
    df = pd.read_excel(path, sheet_name=sheet_name)

    if "unit_id" not in df.columns:
        raise ValueError("El Excel debe tener una columna 'unit_id'.")

    items = [StratigraphicUnit.from_dict(_row_to_dict(row)) for _, row in df.iterrows()]
    return StratigraphicColumn.from_units(items, name=name, axis=axis)
