"""Páginas con datos schema.org Event / MusicEvent en <script type="application/ld+json">."""

import json
import re
from datetime import datetime

from normalize import limpiar_html

_SCRIPT = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE
)
TIPOS = {"Event", "MusicEvent"}


def leer(sala, get_text, hoy):
    eventos = []
    for bloque in _SCRIPT.findall(get_text(sala["url"])):
        try:
            datos = json.loads(bloque)
        except json.JSONDecodeError:
            continue
        for ev in _aplanar(datos):
            convertido = _convertir(ev)
            if convertido:
                eventos.append(convertido)
    return eventos


def _aplanar(datos):
    if isinstance(datos, list):
        for d in datos:
            yield from _aplanar(d)
    elif isinstance(datos, dict):
        if "@graph" in datos:
            yield from _aplanar(datos["@graph"])
        tipo = datos.get("@type")
        tipos = set(tipo) if isinstance(tipo, list) else {tipo}
        if tipos & TIPOS:
            yield datos


def _convertir(ev):
    try:
        inicio = datetime.fromisoformat(str(ev["startDate"]).replace("Z", "+00:00"))
    except (KeyError, ValueError):
        return None
    ofertas = ev.get("offers") or []
    ofertas = ofertas if isinstance(ofertas, list) else [ofertas]
    precios = [float(o["price"]) for o in ofertas if str(o.get("price", "")).replace(".", "", 1).isdigit()]
    agotado = any("SoldOut" in str(o.get("availability", "")) for o in ofertas)
    imagen = ev.get("image")
    if isinstance(imagen, list):
        imagen = imagen[0] if imagen else None
    if isinstance(imagen, dict):
        imagen = imagen.get("url")
    artistas = ev.get("performer") or []
    artistas = artistas if isinstance(artistas, list) else [artistas]
    nombres = [a.get("name") for a in artistas if isinstance(a, dict) and a.get("name")]
    return {
        "titulo": limpiar_html(", ".join(nombres) or ev.get("name", "")),
        "fecha": inicio.date(),
        "hora": inicio.strftime("%H:%M") if "T" in str(ev["startDate"]) else None,
        "precio_min": min(precios) if precios else None,
        "precio_max": max(precios) if precios else None,
        "agotado": agotado,
        "url_entradas": next((o.get("url") for o in ofertas if o.get("url")), ev.get("url")),
        "url": ev.get("url"),
        "imagen": imagen,
        "generos": [],
        "descripcion": limpiar_html(ev.get("description", "")),
    }
