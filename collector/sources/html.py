"""Páginas de agenda sin datos estructurados: se trocea el HTML en fichas con
expresiones regulares que se configuran por sala en venues.yaml (`html:`).

Claves de `html` (todas regex; la del grupo 1 es el valor):
  bloque    dónde empieza cada ficha de concierto (obligatoria)
  titulo    nombre del concierto (obligatoria)
  fecha     texto con la fecha (si no, se busca en toda la ficha); admite AAAA-MM-DD
  hora, precio, enlace, entradas, imagen   opcionales
  generos   se recogen todas las coincidencias
  quitar    texto a borrar del título (p. ej. la fecha pegada al nombre)
"""

import re
from datetime import date
from urllib.parse import urljoin

from normalize import es_agotado, limpiar_html, parse_fecha, parse_hora, parse_precios

_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _texto(html_trozo):
    return limpiar_html(re.sub(r"<[^>]+>", " ", html_trozo or ""))


def _uno(regex, trozo):
    if not regex:
        return None
    m = re.search(regex, trozo, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else None


def leer(sala, get_text, hoy):
    cfg = sala["html"]
    pagina = get_text(sala["url"])
    inicios = [m.start() for m in re.finditer(cfg["bloque"], pagina)]
    if not inicios:
        resumen = re.sub(r"\s+", " ", _texto(pagina))[:160]
        raise ValueError(f"no se encuentran fichas ({len(pagina)} caracteres): {resumen}")
    eventos = []
    for i, inicio in enumerate(inicios):
        fin = inicios[i + 1] if i + 1 < len(inicios) else inicio + 8000
        ev = _ficha(pagina[inicio:fin], cfg, sala["url"], hoy)
        if ev:
            eventos.append(ev)
    return eventos


def _ficha(trozo, cfg, base, hoy):
    titulo = _texto(_uno(cfg["titulo"], trozo))
    if cfg.get("quitar"):
        titulo = re.sub(cfg["quitar"], "", titulo, flags=re.IGNORECASE).strip()
    texto = _texto(trozo)
    fecha_txt = _uno(cfg.get("fecha"), trozo)
    fecha_txt = _texto(fecha_txt) if fecha_txt else texto
    m = _ISO.search(fecha_txt)
    try:
        fecha = date(*map(int, m.groups())) if m else parse_fecha(fecha_txt, hoy)
    except ValueError:
        fecha = None
    if not titulo or not fecha:
        return None
    hora_txt = _uno(cfg.get("hora"), trozo)
    precio_txt = _uno(cfg.get("precio"), trozo) if cfg.get("precio") else texto
    if precio_txt and cfg.get("precio") and "€" not in precio_txt:
        precio_txt = re.sub(r"(\d+(?:[.,]\d+)?)", r"\1 €", precio_txt)
    pmin, pmax = parse_precios(_texto(precio_txt))
    enlace = _uno(cfg.get("enlace"), trozo)
    entradas = _uno(cfg.get("entradas"), trozo)
    imagen = _uno(cfg.get("imagen"), trozo)
    generos = []
    for g in re.findall(cfg["generos"], trozo, re.DOTALL) if cfg.get("generos") else []:
        generos += [limpiar_html(x).strip() for x in re.findall(r">([^<]+)<", f">{g}<")]
    return {
        "titulo": titulo,
        "fecha": fecha,
        "hora": parse_hora(_texto(hora_txt)) if hora_txt else parse_hora(texto),
        "precio_min": pmin,
        "precio_max": pmax,
        "agotado": es_agotado(texto),
        "url_entradas": urljoin(base, entradas or enlace) if (entradas or enlace) else None,
        "url": urljoin(base, enlace) if enlace else None,
        "imagen": urljoin(base, imagen) if imagen else None,
        "generos": [g for g in generos if g],
        "descripcion": "",
    }
