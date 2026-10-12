"""Limpieza de textos de las salas: fechas en español, precios, ids y HTML."""

import html
import re
import unicodedata
from datetime import date

MESES = {
    "ene": 1, "enero": 1, "feb": 2, "febrero": 2, "mar": 3, "marzo": 3,
    "abr": 4, "abril": 4, "may": 5, "mayo": 5, "jun": 6, "junio": 6,
    "jul": 7, "julio": 7, "ago": 8, "agosto": 8, "sep": 9, "sept": 9,
    "septiembre": 9, "setiembre": 9, "oct": 10, "octubre": 10,
    "nov": 11, "noviembre": 11, "dic": 12, "diciembre": 12,
}

_FECHA_TEXTO = re.compile(
    r"\b(\d{1,2})\s*(?:de\s+)?(" + "|".join(sorted(MESES, key=len, reverse=True)) + r")\.?\b"
    r"(?:\s*(?:de\s+)?(\d{4}))?",
    re.IGNORECASE,
)
_FECHA_NUM = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?\b")
_HORA = re.compile(r"\b([01]?\d|2[0-3])[:.h]([0-5]\d)\s*(?:h|horas?)?\b", re.IGNORECASE)
_PRECIO = re.compile(r"(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:€|euros?)", re.IGNORECASE)
_GRATIS = re.compile(r"\b(gratis|gratuito|entrada libre|free)\b", re.IGNORECASE)
_AGOTADO = re.compile(r"\b(agotad[oa]s?|sold ?out|completo)\b", re.IGNORECASE)


def _con_anio(dia, mes, anio, hoy):
    """Sin año explícito, se asume la próxima vez que cae esa fecha."""
    if anio:
        anio = int(anio)
        if anio < 100:
            anio += 2000
        return date(anio, mes, dia)
    candidata = date(hoy.year, mes, dia)
    if (hoy - candidata).days > 60:
        candidata = date(hoy.year + 1, mes, dia)
    return candidata


def parse_fecha(texto, hoy=None):
    """Primera fecha que aparezca en un texto en español, o None."""
    hoy = hoy or date.today()
    m = _FECHA_TEXTO.search(texto or "")
    try:
        if m:
            return _con_anio(int(m.group(1)), MESES[m.group(2).lower()], m.group(3), hoy)
        m = _FECHA_NUM.search(texto or "")
        if m:
            return _con_anio(int(m.group(1)), int(m.group(2)), m.group(3), hoy)
    except ValueError:
        return None
    return None


def parse_hora(texto):
    m = _HORA.search(texto or "")
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def parse_precios(texto):
    """(mínimo, máximo) en euros; (0, 0) si es gratis; (None, None) si no se sabe."""
    valores = [float(v.replace(",", ".")) for v in _PRECIO.findall(texto or "")]
    if valores:
        return min(valores), max(valores)
    if _GRATIS.search(texto or ""):
        return 0.0, 0.0
    return None, None


def es_agotado(texto):
    return bool(_AGOTADO.search(texto or ""))


def limpiar_html(texto):
    texto = re.sub(r"<(br|/p|/li|/h\d)[^>]*>", "\n", texto or "", flags=re.IGNORECASE)
    texto = html.unescape(re.sub(r"<[^>]+>", "", texto))
    texto = re.sub(r"[ \t]+", " ", texto)
    return re.sub(r"\n\s*\n+", "\n\n", texto).strip()


def slug(texto):
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:60]


def id_concierto(sala_id, fecha, titulo):
    return f"{sala_id}-{fecha.isoformat()}-{slug(titulo)}"
