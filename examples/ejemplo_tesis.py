"""Dibuja la columna de campo de la tesis (ejemplo).

Uso:  python examples/ejemplo_tesis.py
"""

from pathlib import Path

from geocolumn.io.excel_reader import read_column_from_excel
from geocolumn.rendering.column_renderer import render_column

here = Path(__file__).parent
column = read_column_from_excel(
    here / "ejemplo_tesis.xlsx", name="Columna litológica de campo (ejemplo)"
)
fig, _ = render_column(column, figsize=(6.5, 9))
out = here / "ejemplo_tesis.png"
fig.savefig(out, dpi=200, bbox_inches="tight")
print(f"Figura guardada en: {out}")
