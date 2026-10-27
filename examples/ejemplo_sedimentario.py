"""Dibuja las dos columnas sedimentarias de ejemplo (afloramiento) con perfil granulométrico.

Uso:  python examples/ejemplo_sedimentario.py
"""

from pathlib import Path

from geocolumn.io.excel_reader import read_column_from_excel
from geocolumn.rendering.column_renderer import render_column

here = Path(__file__).parent
excel = here / "ejemplo_sedimentario.xlsx"

casos = [
    ("Siliciclastica", "siliciclastic", "Secuencia siliciclástica de ejemplo"),
    ("Carbonatos", "carbonate", "Secuencia carbonatada de ejemplo"),
]
for hoja, escala, titulo in casos:
    column = read_column_from_excel(excel, sheet_name=hoja, name=titulo)
    fig, _ = render_column(column, grain_scale=escala)
    out = here / f"ejemplo_sedimentario_{escala}.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"Figura guardada en: {out}")
