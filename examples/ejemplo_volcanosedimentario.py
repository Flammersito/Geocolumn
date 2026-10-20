"""Lee el Excel de ejemplo y genera la figura de la columna.

Uso:  python examples/ejemplo_volcanosedimentario.py
"""

from pathlib import Path

from geocolumn.io.excel_reader import read_column_from_excel
from geocolumn.rendering.column_renderer import render_column

here = Path(__file__).parent
column = read_column_from_excel(
    here / "ejemplo_volcanosedimentario.xlsx",
    name="Secuencia volcano-sedimentaria de ejemplo",
)
fig, _ = render_column(column)
out = here / "ejemplo_volcanosedimentario.png"
fig.savefig(out, dpi=200, bbox_inches="tight")
print(f"Figura guardada en: {out}")
