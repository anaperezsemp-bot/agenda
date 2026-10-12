"""Feed RSS: cada entrada es un concierto; la fecha se busca en el título y el texto."""

import xml.etree.ElementTree as ET

from normalize import es_agotado, limpiar_html, parse_fecha, parse_hora, parse_precios

CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


def leer(sala, get_text, hoy):
    raiz = ET.fromstring(get_text(sala["url"]))
    eventos = []
    for item in raiz.iter("item"):
        titulo = limpiar_html(item.findtext("title", ""))
        cuerpo_html = item.findtext(CONTENT) or item.findtext("description", "")
        cuerpo = limpiar_html(cuerpo_html)
        fecha = parse_fecha(titulo, hoy) or parse_fecha(cuerpo, hoy)
        if not fecha:
            continue  # sin fecha no es un concierto que podamos situar
        pmin, pmax = parse_precios(cuerpo)
        enlace = item.findtext("link")
        eventos.append({
            "titulo": titulo,
            "fecha": fecha,
            "hora": parse_hora(cuerpo),
            "precio_min": pmin,
            "precio_max": pmax,
            "agotado": es_agotado(titulo) or es_agotado(cuerpo),
            "url_entradas": enlace,
            "url": enlace,
            "imagen": _primera_imagen(cuerpo_html),
            "generos": [c.text for c in item.findall("category") if c.text],
            "descripcion": cuerpo,
        })
    return eventos


def _primera_imagen(html_texto):
    import re
    m = re.search(r'<img[^>]+src="([^"]+)"', html_texto or "")
    return m.group(1) if m else None
