"""Plugin The Events Calendar de WordPress: /wp-json/tribe/events/v1/events."""

from datetime import datetime

from normalize import es_agotado, limpiar_html, parse_precios


def leer(sala, get_json, hoy):
    url = (
        f"{sala['base'].rstrip('/')}/wp-json/tribe/events/v1/events"
        f"?per_page=50&start_date={hoy.isoformat()}"
    )
    eventos = []
    for _ in range(10):  # como mucho 500 eventos
        datos = get_json(url)
        for ev in datos.get("events", []):
            eventos.append(_convertir(ev))
        url = datos.get("next_rest_url")
        if not url:
            break
    return eventos


def _convertir(ev):
    inicio = datetime.strptime(ev["start_date"], "%Y-%m-%d %H:%M:%S")
    coste = ev.get("cost") or ""
    pmin, pmax = parse_precios(coste if "€" in coste or not coste else coste + " €")
    imagen = ev.get("image") or {}
    descripcion = limpiar_html(ev.get("description", ""))
    return {
        "titulo": limpiar_html(ev.get("title", "")),
        "fecha": inicio.date(),
        "hora": None if ev.get("all_day") else inicio.strftime("%H:%M"),
        "precio_min": pmin,
        "precio_max": pmax,
        "agotado": es_agotado(coste) or es_agotado(ev.get("title", "")),
        "url_entradas": ev.get("website") or ev.get("url"),
        "url": ev.get("url"),
        "imagen": imagen.get("url") if isinstance(imagen, dict) else None,
        "generos": [c["name"] for c in ev.get("categories", []) if c.get("name")],
        "descripcion": descripcion,
    }
