"""Conciertos y correcciones a mano, desde una hoja de cálculo publicada como CSV.

manual.yaml guarda los enlaces CSV de dos pestañas:
  conciertos  una fila por concierto que no sale de ninguna web
  cambios     una fila por concierto existente a corregir; se identifica pegando su
              enlace (botón «Copiar enlace» del detalle) en la columna «enlace»

Columnas (en cualquier orden; mayúsculas y tildes dan igual):
  grupo, fecha, hora, sala, barrio, precio, agotado, entradas, web, imagen, generos, descripcion
  y en «cambios» además: enlace, ocultar
Una celda vacía en «cambios» deja el dato como estaba.
"""

import csv
import io
import re
from datetime import date
from urllib.parse import parse_qs, urlparse

from normalize import id_concierto, parse_fecha, parse_hora, parse_precios, slug

SI = {"si", "sí", "s", "x", "yes", "true", "1", "agotado", "agotadas"}


def _filas(texto):
    lector = csv.DictReader(io.StringIO(texto.lstrip("﻿")))
    for fila in lector:
        fila = {slug(k or "").replace("-", ""): (v or "").strip() for k, v in fila.items()}
        if any(fila.values()):
            yield fila


def _fecha(texto, hoy):
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", texto)
    try:
        if m:
            return date(*map(int, m.groups()))
        m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", texto)
        if m:
            d, mes, a = map(int, m.groups())
            return date(a + 2000 if a < 100 else a, mes, d)
    except ValueError:
        return None
    return parse_fecha(texto, hoy)


def _datos(fila, hoy):
    """Campos que trae la fila, ya convertidos; los vacíos no aparecen."""
    d = {}
    if fila.get("grupo"):
        d["titulo"] = fila["grupo"]
    if fila.get("fecha"):
        f = _fecha(fila["fecha"], hoy)
        if not f:
            raise ValueError(f"fecha que no se entiende: «{fila['fecha']}»")
        d["fecha"] = f
    if fila.get("hora"):
        d["hora"] = parse_hora(fila["hora"].replace(".", ":") if ":" not in fila["hora"] else fila["hora"]) \
            or parse_hora(fila["hora"] + ":00")
    if fila.get("precio"):
        p = fila["precio"]
        pmin, pmax = parse_precios(p if re.search(r"€|euro|gratis|libre", p, re.I) else re.sub(r"(\d+(?:[.,]\d+)?)", r"\1 €", p))
        d["precio_min"], d["precio_max"] = pmin, pmax
    if fila.get("agotado"):
        d["agotado"] = fila["agotado"].lower() in SI
    for col, campo in (("entradas", "url_entradas"), ("web", "url"), ("imagen", "imagen"), ("descripcion", "descripcion")):
        if fila.get(col):
            d[campo] = fila[col]
    if fila.get("generos"):
        d["generos"] = [g.strip() for g in re.split(r"[,·/]", fila["generos"]) if g.strip()]
    return d


def _sala(nombre, barrio, salas):
    """Id de la sala por su nombre; si no es de las que sigue la agenda, se da de alta."""
    clave = slug(nombre)
    for s in salas:
        if clave in (s["id"], slug(s["nombre"])):
            return s["id"]
    salas.append({"id": clave, "nombre": nombre, "barrio": barrio, "fuente": "manual"})
    return clave


def conciertos_nuevos(texto, salas, hoy):
    nuevos, errores = [], []
    for n, fila in enumerate(_filas(texto), start=2):
        try:
            d = _datos(fila, hoy)
            if not d.get("titulo") or not d.get("fecha") or not fila.get("sala"):
                raise ValueError("faltan grupo, fecha o sala")
        except ValueError as e:
            errores.append(f"fila {n}: {e}")
            continue
        if d["fecha"] < hoy:
            continue
        sala = _sala(fila["sala"], fila.get("barrio", ""), salas)
        c = {"hora": None, "precio_min": None, "precio_max": None, "agotado": False, "url_entradas": None,
             "url": None, "imagen": None, "generos": [], "categorias": [], "descripcion": "", **d}
        c.update(sala=sala, id=id_concierto(sala, d["fecha"], d["titulo"]), manual=True, fecha=d["fecha"].isoformat())
        nuevos.append(c)
    return nuevos, errores


def _id_de(fila):
    if fila.get("id"):
        return fila["id"]
    enlace = fila.get("enlace", "")
    return (parse_qs(urlparse(enlace).query).get("id") or [enlace])[0]


def aplicar_cambios(texto, conciertos, hoy):
    """Corrige o quita conciertos ya leídos. Devuelve los errores (filas que no encajan)."""
    errores = []
    for n, fila in enumerate(_filas(texto), start=2):
        cid = _id_de(fila)
        if cid not in conciertos:
            # Puede ser un concierto que ya pasó: solo es error si aún no ha llegado su fecha.
            m = re.search(r"-(\d{4}-\d{2}-\d{2})-", cid or "")
            if not m or m.group(1) >= hoy.isoformat():
                errores.append(f"fila {n}: no encuentro el concierto «{cid}»")
            continue
        if fila.get("ocultar", "").lower() in SI:
            del conciertos[cid]
            continue
        try:
            d = _datos(fila, hoy)
        except ValueError as e:
            errores.append(f"fila {n}: {e}")
            continue
        if "fecha" in d:
            d["fecha"] = d["fecha"].isoformat()
        conciertos[cid].update(d, corregido=True)
    return errores
