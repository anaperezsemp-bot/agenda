# Agenda

Agenda de conciertos en salas medianas y espacios pequeños de Madrid, pensada para el móvil.

- `collector/`: recolector en Python que lee la agenda de cada sala sin IA (API de eventos de WordPress, RSS o datos schema.org) y escribe `web/data/agenda.json` y una ficha por concierto en `web/data/events/`.
- `collector/venues.yaml`: lista de salas y de dónde se lee cada una. Las marcadas `pendiente` aún no tienen lector.
- `web/`: web estática (HTML, CSS y JavaScript sin dependencias). La agenda descarga un único JSON y filtra en el propio navegador.
- `.github/workflows/actualizar.yml`: cada 6 horas ejecuta el recolector y guarda los datos en `main`. El alojamiento (Cloudflare Pages, carpeta `web`, sin comando de build) publica la web en cada commit.

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

## Cuentas (Supabase)

Las cuentas son opcionales: si `web/config.js` está vacío, la web funciona sin ellas.

1. Crear un proyecto en Supabase y ejecutar `supabase/schema.sql` en su SQL Editor.
2. Copiar la Project URL y la clave anon/publishable en `web/config.js`.
3. En Authentication → URL Configuration, añadir la dirección de la web (y la de pruebas) como Site URL y Redirect URLs.

Cada persona guarda sus salas y géneros favoritos (`perfiles`) y los conciertos a los que va (`voy`). Las reglas de seguridad de `schema.sql` hacen que cada una solo vea y cambie sus propias filas.
