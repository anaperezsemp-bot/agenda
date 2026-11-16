"""Muestra de audio de 30 s por grupo, sacada del buscador público de Apple (iTunes Search API).

Sin IA y sin clave: se busca el nombre del grupo y solo se acepta un resultado cuyo artista
coincida exactamente, para no poner la canción de otro grupo con nombre parecido.
Los resultados se guardan en caché para no repetir búsquedas en cada ejecución.
"""

import json
import re
import time
from datetime import date, timedelta

from normalize import slug

API = "https://itunes.apple.com/search"
MAX_BUSQUEDAS = 60      # por ejecución; el resto queda para la siguiente
PAUSA = 3.2             # segundos entre búsquedas (Apple admite unas 20 por minuto)
CADUCIDAD = 30          # días antes de volver a buscar un grupo sin resultado

# "&" e "y" no cortan: forman parte de muchos nombres ("Jesse & Joy", "Fito y Fitipaldis").
_CORTES = re.compile(r"\s+(?:\+|w/|con|feat\.?|ft\.?)\s+|\s*[:|–—]\s*|\s+-\s+|,\s*", re.IGNORECASE)


def cabeza_de_cartel(titulo):
    """'Grupo A + Grupo B' -> 'Grupo A'; 'GIRA 2026: Grupo' se queda como está si no hay más."""
    partes = [p.strip() for p in _CORTES.split(titulo) if p.strip()]
    return partes[0] if partes else titulo


def buscar(nombre, get_json):
    datos = get_json(API, {"term": nombre, "entity": "song", "attribute": "artistTerm",
                           "country": "ES", "limit": 10})
    clave = slug(nombre)
    for r in datos.get("results", []):
        if slug(r.get("artistName", "")) == clave and r.get("previewUrl"):
            return {"audio": r["previewUrl"], "cancion": r.get("trackName"),
                    "enlace": r.get("trackViewUrl")}
    return None


def enriquecer(conciertos, cache_path, get_json, hoy=None, dormir=time.sleep):
    """Añade 'audio', 'cancion' y 'enlace_audio' a cada concierto cuyo grupo se encuentre."""
    hoy = hoy or date.today()
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    hechas = 0
    for c in conciertos:
        # Primero el título entero; si no aparece, el primer grupo del cartel.
        candidatos = list(dict.fromkeys(n for n in (c["titulo"], cabeza_de_cartel(c["titulo"])) if slug(n)))
        for nombre in candidatos:
            clave = slug(nombre)
            guardado = cache.get(clave)
            caducado = (guardado and guardado.get("r") is None
                        and date.fromisoformat(guardado["f"]) < hoy - timedelta(days=CADUCIDAD))
            if (guardado is None or caducado) and hechas < MAX_BUSQUEDAS:
                if hechas:
                    dormir(PAUSA)
                try:
                    cache[clave] = {"f": hoy.isoformat(), "r": buscar(nombre, get_json)}
                except Exception:
                    pass  # si Apple falla, se reintenta en la siguiente ejecución
                hechas += 1
            r = (cache.get(clave) or {}).get("r")
            if r:
                c.update(audio=r["audio"], cancion=r["cancion"], enlace_audio=r["enlace"])
                break
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    return hechas
