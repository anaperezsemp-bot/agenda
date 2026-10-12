"""Recolector: lee la agenda de cada sala y genera los JSON que muestra la web.

Uso: python collector/collect.py [--salida web/data]
"""

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
import yaml

from normalize import id_concierto
from sources import jsonld, rss, tec

AQUI = Path(__file__).resolve().parent
USER_AGENT = "AgendaConciertosMadrid/0.1 (agenda personal sin animo de lucro)"
LECTORES = {"tec": (tec, "json"), "rss": (rss, "text"), "jsonld": (jsonld, "text")}


def _sesion():
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def leer_sala(sala, sesion, hoy):
    lector, formato = LECTORES[sala["fuente"]]

    def get(url):
        r = sesion.get(url, timeout=30)
        r.raise_for_status()
        return r.json() if formato == "json" else r.text

    return lector.leer(sala, get, hoy)


def a_listado(c):
    """Fila mínima para el listado: claves cortas para que el JSON pese poco."""
    fila = {"id": c["id"], "f": c["fecha"], "h": c["hora"], "g": c["titulo"], "s": c["sala"]}
    if c["precio_min"] is not None:
        fila["p"] = c["precio_min"]
    if c["agotado"]:
        fila["a"] = 1
    if c["generos"]:
        fila["gen"] = c["generos"]
    return fila


def cargar_anteriores(salida):
    """Conciertos publicados la vez anterior, por sala, para no perderlos si una sala falla."""
    por_sala = {}
    for fichero in (salida / "events").glob("*.json"):
        c = json.loads(fichero.read_text(encoding="utf-8"))
        por_sala.setdefault(c["sala"], []).append(c)
    return por_sala


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--salida", default=str(AQUI.parent / "web" / "data"))
    parser.add_argument("--hoy", help="fecha de referencia AAAA-MM-DD (para pruebas)")
    args = parser.parse_args()

    hoy = date.fromisoformat(args.hoy) if args.hoy else date.today()
    salida = Path(args.salida)
    (salida / "events").mkdir(parents=True, exist_ok=True)
    salas = yaml.safe_load((AQUI / "venues.yaml").read_text(encoding="utf-8"))["salas"]
    anteriores = cargar_anteriores(salida)
    sesion = _sesion()

    conciertos, informe = {}, []
    for sala in salas:
        if sala["fuente"] not in LECTORES:
            continue
        try:
            leidos = leer_sala(sala, sesion, hoy)
            error = None
        except Exception as e:  # una sala rota no debe tumbar la agenda entera
            leidos, error = [], f"{type(e).__name__}: {e}"

        nuevos = []
        for ev in leidos:
            if ev["fecha"] < hoy or not ev["titulo"]:
                continue
            c = dict(ev, sala=sala["id"], fecha=ev["fecha"].isoformat())
            c["id"] = id_concierto(sala["id"], ev["fecha"], ev["titulo"])
            nuevos.append(c)

        if not nuevos and anteriores.get(sala["id"]):
            # Sin datos nuevos: se conservan los anteriores que aún no han pasado.
            nuevos = [c for c in anteriores[sala["id"]] if c["fecha"] >= hoy.isoformat()]
            error = error or "0 conciertos leídos; se mantienen los anteriores"

        for c in nuevos:
            conciertos[c["id"]] = c
        informe.append((sala["nombre"], len(nuevos), error))

    ordenados = sorted(conciertos.values(), key=lambda c: (c["fecha"], c["hora"] or "99", c["titulo"]))
    agenda = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "salas": {
            s["id"]: {"n": s["nombre"], "b": s.get("barrio", ""), "w": s.get("web", "")} for s in salas
        },
        "conciertos": [a_listado(c) for c in ordenados],
    }
    (salida / "agenda.json").write_text(
        json.dumps(agenda, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    for viejo in (salida / "events").glob("*.json"):
        if viejo.stem not in conciertos:
            viejo.unlink()
    for c in ordenados:
        (salida / "events" / f"{c['id']}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    print(f"{len(ordenados)} conciertos desde {hoy.isoformat()}")
    for nombre, n, error in informe:
        print(f"  {nombre}: {n}" + (f"  ⚠ {error}" if error else ""))
    # Si ninguna sala devolvió nada, algo va mal: el workflow lo marcará como fallo.
    return 0 if ordenados or not informe else 1


if __name__ == "__main__":
    sys.exit(main())
