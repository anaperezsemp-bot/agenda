# Agenda

Agenda de conciertos en salas medianas y espacios pequeños de Madrid, pensada para el móvil.

- `collector/`: recolector en Python que lee la agenda de cada sala sin IA (API de eventos de WordPress, RSS o datos schema.org) y escribe `web/data/agenda.json` y una ficha por concierto en `web/data/events/`.
- `collector/venues.yaml`: lista de salas y de dónde se lee cada una. Las marcadas `pendiente` aún no tienen lector.
- `web/`: web estática (HTML, CSS y JavaScript sin dependencias). La agenda descarga un único JSON y filtra en el propio navegador.
- `.github/workflows/actualizar.yml`: cada 6 horas ejecuta el recolector, guarda los datos y publica la web en GitHub Pages.

## Probar en local

```sh
pip install -r collector/requirements.txt
python -m pytest -q collector/tests
python collector/collect.py
python -m http.server -d web 8000   # y abrir http://localhost:8000
```

## Añadir una sala

1. Añadir una entrada en `collector/venues.yaml` con `fuente: tec`, `rss` o `jsonld`.
2. Si la sala necesita un lector nuevo, crear `collector/sources/<nombre>.py` con una función `leer(sala, get, hoy)` que devuelva la lista de conciertos, y registrarlo en `LECTORES` de `collect.py`.
