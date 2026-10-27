"""Genera un Excel de ejemplo con dos columnas sedimentarias (una hoja cada una).

Uso:  python examples/make_sedimentary_excel.py

Las columnas son de afloramiento: alturas desde la base (`base_height_m`,
`top_height_m`), unidades listadas desde la base y lo más joven arriba.

Hojas:
  - Siliciclastica: lutitas, limolitas, areniscas y conglomerado, con la
    granulometría en `grain_size` (escala Udden-Wentworth).
  - Carbonatos: calizas y dolomías, con la textura de Dunham en `grain_size`.

El color y el patrón se dejan vacíos: salen del catálogo de litologías.
Los espesores varían a propósito (desde 0.4 m hasta más de 13 m).
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HEADERS = ["unit_id", "base_height_m", "top_height_m", "lithology", "grain_size",
           "sedimentary_structures", "fossils", "observations"]

# Columnas de afloramiento: las unidades se listan DESDE LA BASE hacia arriba y
# las alturas se miden desde la base de la columna (0 m). Lo más joven queda
# arriba en la figura.
# (unit_id, base_height, top_height, lithology, grain_size, structures, fossils, observations)
SILICICLASTIC = [
    ("S1", 0.0, 6.7, "arenisca_cruzada", "arena media", "cross_bedding", "", "Base de la sección expuesta"),
    ("S2", 6.7, 7.1, "carbon", "arcilla", "", "", "Veta de carbón de 40 cm"),
    ("S3", 7.1, 8.0, "lutita_carbonosa", "arcilla", "", "restos_vegetales", "Rica en materia orgánica"),
    ("S4", 8.0, 20.0, "lutita", "arcilla", "laminacion", "", ""),
    ("S5", 20.0, 21.5, "arenisca", "arena muy fina", "", "", ""),
    ("S6", 21.5, 25.0, "limolita", "limo", "ripple_marks", "", ""),
    ("S7", 25.0, 38.4, "lutita", "arcilla", "laminacion", "restos_vegetales", "Lutitas laminadas, grises"),
    ("S8", 38.4, 39.0, "limolita", "limo", "laminacion", "", "Capa muy delgada"),
    ("S9", 39.0, 50.8, "arenisca_estratificada", "arena fina", "planar_bedding;ripple_marks", "", ""),
    ("S10", 50.8, 52.0, "arenisca", "arena media", "", "", "Capa delgada y masiva"),
    ("S11", 52.0, 58.0, "arenisca_cruzada", "arena gruesa", "cross_bedding", "", "Estratificación cruzada en artesa"),
    ("S12", 58.0, 60.0, "conglomerado", "guijarro", "imbricacion", "", "Base erosiva; clastos redondeados"),
]

CARBONATE = [
    ("C1", 0.0, 2.5, "caliza", "mudstone", "", "", ""),
    ("C2", 2.5, 9.5, "caliza", "wackestone", "bioturbacion", "", ""),
    ("C3", 9.5, 13.5, "caliza", "boundstone", "", "corales;estromatolitos", "Construcción orgánica"),
    ("C4", 13.5, 16.5, "caliza", "grainstone", "", "", ""),
    ("C5", 16.5, 22.5, "dolomia", "packstone", "", "", "Dolomitización parcial"),
    ("C6", 22.5, 24.3, "caliza", "rudstone", "", "corales", "Bioclastos soportados por clastos"),
    ("C7", 24.3, 25.5, "caliza", "floatstone", "", "corales;bivalvos", "Bioclastos grandes en matriz fina"),
    ("C8", 25.5, 33.0, "caliza", "mudstone", "laminacion", "", "Mudstone micrítico, aspecto masivo"),
    ("C9", 33.0, 41.5, "caliza", "wackestone", "bioturbacion", "foraminiferos", "Estratos de 20 a 40 cm"),
    ("C10", 41.5, 43.0, "caliza", "packstone", "", "bivalvos;gasteropodos", ""),
    ("C11", 43.0, 47.5, "caliza", "grainstone", "cross_bedding", "bivalvos", "Calcarenita bien lavada; techo de la sección"),
]


def _sheet(wb, title, rows):
    ws = wb.create_sheet(title)
    ws.append(HEADERS)
    for row in rows:
        ws.append([None if v == "" else v for v in row])
    thin = Side(style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for cell in ws[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", start_color="4C6B52", end_color="4C6B52")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Arial", size=10)
            cell.border = border
    for i, header in enumerate(HEADERS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = 40 if header == "observations" else 20
    ws.freeze_panes = "A2"


def build(path: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    _sheet(wb, "Siliciclastica", SILICICLASTIC)
    _sheet(wb, "Carbonatos", CARBONATE)
    wb.save(path)


if __name__ == "__main__":
    out = Path(__file__).parent / "ejemplo_sedimentario.xlsx"
    build(out)
    print(f"Generado: {out}")
