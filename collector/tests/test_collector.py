import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from normalize import parse_fecha, parse_hora, parse_precios  # noqa: E402
from sources import jsonld, rss, tec  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
HOY = date(2026, 10, 12)


def test_fechas_en_espanol():
    assert parse_fecha("Viernes 24 de octubre", HOY) == date(2026, 10, 24)
    assert parse_fecha("sáb 3 ene", HOY) == date(2027, 1, 3)
    assert parse_fecha("17/10/2026", HOY) == date(2026, 10, 17)
    assert parse_fecha("sin fecha", HOY) is None


def test_hora_y_precio():
    assert parse_hora("Puertas 21:30h") == "21:30"
    assert parse_precios("Anticipada 10€ + gastos, taquilla 14€") == (10.0, 14.0)
    assert parse_precios("Entrada libre") == (0.0, 0.0)
    assert parse_precios("consultar") == (None, None)


def test_tec():
    datos = json.loads((FIX / "tec.json").read_text())
    evs = tec.leer({"base": "https://x"}, lambda url: datos, HOY)
    punsetes, jam = evs[0], evs[1]
    assert punsetes["fecha"] == date(2026, 10, 17) and punsetes["hora"] == "21:00"
    assert (punsetes["precio_min"], punsetes["precio_max"]) == (12.0, 15.0)
    assert punsetes["generos"] == ["Indie"]
    assert jam["agotado"] and jam["precio_min"] == 0.0 and jam["titulo"] == "Jam session – AGOTADO"


def test_rss():
    texto = (FIX / "rss.xml").read_text()
    evs = rss.leer({"url": "u"}, lambda url: texto, HOY)
    assert len(evs) == 1
    ev = evs[0]
    assert ev["fecha"] == date(2026, 10, 24) and ev["hora"] == "21:30"
    assert ev["precio_min"] == 10.0 and ev["imagen"] == "https://m.com/biz.jpg"


def test_jsonld():
    texto = (FIX / "jsonld.html").read_text()
    (ev,) = jsonld.leer({"url": "u"}, lambda url: texto, HOY)
    assert ev["titulo"] == "Hinds" and ev["agotado"] and ev["precio_min"] == 18.0
    assert ev["hora"] == "20:00" and ev["url_entradas"] == "https://dice.fm/hinds"


def test_generos():
    from normalize import generos_y_titulo
    assert generos_y_titulo("LINDA BURNETTI + MIRAGÜANO (Blues Rock Indie Pop)", ["Conciertos"]) == (
        "LINDA BURNETTI + MIRAGÜANO", ["Blues", "Rock", "Indie", "Pop"])
    assert generos_y_titulo("ALBERTO BALLESTEROS (Pop · Rock · Folk)", []) == (
        "ALBERTO BALLESTEROS", ["Pop", "Rock", "Folk"])
    assert generos_y_titulo("Chema Saiz (Festival JazzMadrid)", ["Madrid", "jazz", "blues", "Maravillas"]) == (
        "Chema Saiz (Festival JazzMadrid)", ["Jazz", "Blues"])


def test_escuchar(tmp_path):
    import escuchar
    assert escuchar.cabeza_de_cartel("LINDA BURNETTI + MIRAGÜANO") == "LINDA BURNETTI"
    assert escuchar.cabeza_de_cartel("Hinds") == "Hinds"
    assert escuchar.cabeza_de_cartel("Jesse & Joy") == "Jesse & Joy"
    respuestas = {
        "Hinds": {"results": [
            {"artistName": "Hinds Tribute", "previewUrl": "x"},
            {"artistName": "HINDS", "previewUrl": "https://a/p.m4a", "trackName": "Garden", "trackViewUrl": "https://m/1"}]},
        "Nadie": {"results": []},
        "Nadie + Otro": {"results": []},
    }
    llamadas = []
    def get_json(url, params):
        llamadas.append(params["term"])
        return respuestas[params["term"]]
    conciertos = [{"titulo": "Hinds"}, {"titulo": "Nadie + Otro"}, {"titulo": "Hinds"}]
    cache = tmp_path / "cache.json"
    escuchar.enriquecer(conciertos, cache, get_json, HOY, dormir=lambda s: None)
    assert conciertos[0]["audio"] == "https://a/p.m4a" and conciertos[2]["cancion"] == "Garden"
    assert "audio" not in conciertos[1]
    assert llamadas == ["Hinds", "Nadie + Otro", "Nadie"]
    # segunda ejecución: todo sale de la caché
    escuchar.enriquecer([{"titulo": "Hinds"}], cache, get_json, HOY, dormir=lambda s: None)
    assert llamadas == ["Hinds", "Nadie + Otro", "Nadie"]


def test_quitar_agotado():
    from normalize import quitar_agotado
    assert quitar_agotado("Arde Bogotá (Sold Out)") == ("Arde Bogotá", True)
    assert quitar_agotado("CARLES BENAVENT TRÍO – ENTRADAS AGOTADAS") == ("CARLES BENAVENT TRÍO", True)
    assert quitar_agotado("Editors + Big Sleep (Sold Out)") == ("Editors + Big Sleep", True)
    assert quitar_agotado("Los Completos") == ("Los Completos", False)
    assert quitar_agotado("Completo") == ("Completo", False)


def test_escuchar_ciclo(tmp_path):
    import escuchar
    llamadas = []
    def get_json(url, params):
        llamadas.append(params["term"])
        if params["term"] == "CARLES BENAVENT TRÍO":
            return {"results": [{"artistName": "Carles Benavent Trío", "previewUrl": "https://a/c.m4a"}]}
        return {"results": []}
    c = [{"titulo": "Jazz con Sabor A Club 2026: CARLES BENAVENT TRÍO"}]
    escuchar.enriquecer(c, tmp_path / "c.json", get_json, HOY, dormir=lambda s: None)
    assert c[0]["audio"] == "https://a/c.m4a"


def test_madridenvivo():
    import json
    from pathlib import Path
    from sources import madridenvivo
    datos = json.loads((Path(__file__).parent / "datos" / "madridenvivo.json").read_text())
    madridenvivo._cache.clear()
    pedidas = []
    def get_json(url):
        pedidas.append(url)
        return datos if "page=1&" in url else []
    sala = {"mev": 61555}
    evs = madridenvivo.leer(sala, get_json, HOY, dormir=lambda s: None)
    assert len(evs) == 1
    ev = evs[0]
    assert ev["titulo"] == "CANAL STREET JAZZ BAND" and ev["hora"] == "20:00" and ev["precio_min"] == 24
    assert ev["fecha"].isoformat() == "2026-12-13" and "Jazz" in ev["generos"]
    # el evento de clubbing de la otra sala se descarta, y la descarga se hace una vez por ejecución
    assert madridenvivo.leer({"mev": 61582}, get_json, HOY, dormir=lambda s: None) == []
    assert len(pedidas) == 2


def test_html():
    import yaml
    from pathlib import Path
    from sources import html
    aqui = Path(__file__).parent
    salas = {s["id"]: s for s in yaml.safe_load((aqui.parent / "venues.yaml").read_text())["salas"]}
    pagina = (aqui / "datos" / "wurlitzer.html").read_text()
    evs = html.leer(salas["wurlitzer"], lambda url: pagina, HOY)
    assert [e["titulo"] for e in evs] == [
        "JOHNNY IRION + TESS LIAUTAUD + TIM EASTON", "miaw", "Penny & The Pits + tovar"]
    primero = evs[0]
    assert primero["fecha"].isoformat() == "2026-11-16" and primero["hora"] == "21:00"
    assert (primero["precio_min"], primero["precio_max"]) == (18, 21)
    assert primero["generos"] == ["americana", "folk", "country"]
    assert primero["url_entradas"].startswith("https://mutick.com/")


def test_manual():
    import manual
    salas = [{"id": "fun-house", "nombre": "Fun House", "barrio": "Chamberí"}]
    hoja = (
        "Grupo,Fecha,Hora,Sala,Barrio,Precio,Agotado,Entradas,Géneros\n"
        "Los Nuevos,20/10/2026,21,Fun House,,12,no,https://e/1,\"Rock, Garage\"\n"
        "Otra Banda,2026-10-25,20:30,Sala Rara,Lavapiés,gratis,,,\n"
        "Pasado,01/01/2020,20:00,Fun House,,,,,\n"
        "Sin fecha,,,Fun House,,,,,\n"
    )
    nuevos, errores = manual.conciertos_nuevos(hoja, salas, HOY)
    assert [c["titulo"] for c in nuevos] == ["Los Nuevos", "Otra Banda"]
    a, b = nuevos
    assert a["sala"] == "fun-house" and a["fecha"] == "2026-10-20" and a["hora"] == "21:00"
    assert a["precio_min"] == 12 and a["agotado"] is False and a["generos"] == ["Rock", "Garage"]
    assert b["sala"] == "sala-rara" and b["precio_min"] == 0 and salas[-1]["barrio"] == "Lavapiés"
    assert len(errores) == 1 and "fila 5" in errores[0]

    conciertos = {a["id"]: dict(a), b["id"]: dict(b)}
    cambios = (
        "Enlace,Precio,Agotado,Hora,Ocultar\n"
        f"https://x.pages.dev/detalle.html?id={a['id']},15 €,sí,,\n"
        f"https://x.pages.dev/detalle.html?id={b['id']},,,,sí\n"
        "https://x.pages.dev/detalle.html?id=fun-house-2026-12-01-no-existe,,,,\n"
    )
    errores = manual.aplicar_cambios(cambios, conciertos, HOY)
    assert list(conciertos) == [a["id"]]
    assert conciertos[a["id"]]["precio_min"] == 15 and conciertos[a["id"]]["agotado"] is True
    assert conciertos[a["id"]]["hora"] == "21:00"  # celda vacía: no cambia
    assert len(errores) == 1 and "no-existe" in errores[0]
