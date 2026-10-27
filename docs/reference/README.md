# Documentos de referencia

- FGDCgeostdTM11A2_web_all.pdf — Estándar oficial FGDC-STD-013-2006 (USGS Techniques and Methods 11-A2). Contiene la numeración y nombres oficiales de los patrones litológicos (series 600 y 700, pensadas para columnas estratigráficas). Usado para diseñar el catálogo de patrones (geocolumn/styles/patterns.py) y como referencia para la futura Opción B (patrones vectoriales fieles).

- USGS-patterns-INKSCAPE-template.svg — Plantilla de Inkscape con 277 definiciones de patrón SVG vectorial reales (sin etiquetar con números FGDC; habría que emparejarlos visualmente contra el PDF). Recurso clave para implementar la Opción B (patrones vectoriales fieles) más adelante.

- simbologia_rocas.svg — SVG exportado del estándar FGDC con las tres páginas de patrones litológicos: A-37-1 (601–644, sedimentarias), A-37-2 (645–686) y A-37-3 (701–733, metamórficas/ígneas/veta). Solo la primera página cae dentro del `viewBox`; las otras dos están a la derecha, fuera de él. Contiene 117 rectángulos de muestra (72 x 57.6) rellenos con `<pattern>` SVG reales, es decir, la geometría vectorial oficial de cada patrón. Se pueden asociar a su código FGDC por posición (página, fila, columna) y verificar visualmente. Es la fuente prevista para la Opción B (patrones vectoriales fieles). Pesa ~11 MB y está excluido de git.
