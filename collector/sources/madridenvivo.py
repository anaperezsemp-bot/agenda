"""Agenda de Madrid en Vivo (madridenvivo.com), la asociación de salas de Madrid.

Las salas publican allí sus conciertos y la web los ofrece en su API de WordPress
(/wp-json/wp/v2/evento), con la sala, fecha, hora, precio y enlace de entradas en
campos separados. Se descarga una sola vez por ejecución y cada sala se queda con
los suyos (campo `mev` de venues.yaml = id de la sala en Madrid en Vivo).
"""

import time
from datetime import date, timedelta

from normalize import es_agotado, limpiar_html, parse_hora, parse_precios

API = "https://madridenvivo.com/wp-json/wp/v2/evento"
CAMPOS = "id,date,link,title,content,acf,estilo_evento,taxonomy_info,featured_image_src_large"
# Estilos de la asociación: los que no son conciertos se descartan.
ESTILOS = {770: "Artes escénicas", 772: "Clubbing", 774: "Flamenco", 778: "Músicas negras",
           779: "Pop / Rock", 822: "Musicales"}
NO_CONCIERTOS = {770, 772, 822}
PAUSA = 10  # su robots.txt pide 10 s entre peticiones
MAX_PAGINAS = 12

_cache = {}


def _todos(get_json, hoy, dormir=time.sleep):
    if hoy in _cache:
        return _cache[hoy]
    eventos, limite = [], (hoy - timedelta(days=240)).isoformat()
    for pagina in range(1, MAX_PAGINAS + 1):
        if pagina > 1:
            dormir(PAUSA)
        try:
            lote = get_json(f"{API}?per_page=100&page={pagina}&_fields={CAMPOS}")
        except Exception:
            if pagina == 1:
                raise
            break  # WordPress responde 400 al pasarse de la última página
        if not lote:
            break
        eventos += lote
        # Ordenados por fecha de publicación: lo publicado hace meses ya no trae conciertos futuros.
        if all(ev.get("date", "") < limite for ev in lote):
            break
    _cache[hoy] = eventos
    return eventos


def leer(sala, get_json, hoy, dormir=time.sleep):
    return [c for c in (_convertir(ev) for ev in _todos(get_json, hoy, dormir)
                        if (ev.get("acf") or {}).get("relacion_con_sala") == sala["mev"]) if c]


def _convertir(ev):
    acf = ev.get("acf") or {}
    estilos = set(ev.get("estilo_evento") or [])
    if estilos & NO_CONCIERTOS:
        return None
    try:
        f = acf["fecha_del_evento"]
        fecha = date(int(f[:4]), int(f[4:6]), int(f[6:8]))
    except (KeyError, TypeError, ValueError):
        return None
    pases = acf.get("hora_del_pase") or []
    hora = parse_hora(pases[0].get("hora", "")) if pases else None
    precio_txt = acf.get("precio_del_evento") or ""
    if acf.get("entrada_libre"):
        pmin, pmax = 0.0, 0.0
    else:
        pmin, pmax = parse_precios(precio_txt)
    titulo = limpiar_html(ev.get("title", {}).get("rendered", ""))
    etiquetas = [t["label"] for t in (ev.get("taxonomy_info") or {}).get("post_tag", []) if t.get("label")]
    imagen = ev.get("featured_image_src_large")
    return {
        "titulo": titulo,
        "fecha": fecha,
        "hora": hora,
        "precio_min": pmin,
        "precio_max": pmax,
        "agotado": es_agotado(precio_txt) or es_agotado(acf.get("venta_de_entradas_texto") or ""),
        "url_entradas": acf.get("venta_de_entradas_url") or ev.get("link"),
        "url": ev.get("link"),
        "imagen": imagen[0] if isinstance(imagen, list) and imagen else None,
        "generos": etiquetas + [ESTILOS[e] for e in estilos if e in ESTILOS],
        "descripcion": limpiar_html(ev.get("content", {}).get("rendered", "")),
    }
