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


def test_miniaturas(tmp_path):
    from io import BytesIO

    from PIL import Image

    import miniaturas

    cartel = BytesIO()
    Image.new("RGBA", (800, 1100), (200, 30, 30, 255)).save(cartel, "PNG")
    conciertos = [
        {"id": "a", "imagen": "https://x/a.png"},
        {"id": "b", "imagen": "https://x/roto.png"},
        {"id": "c", "imagen": None},
    ]
    (tmp_path / "viejo.webp").write_bytes(b"x")

    def descargar(url):
        if "roto" in url:
            raise OSError("404")
        return cartel.getvalue()

    hechas, fallos = miniaturas.actualizar(conciertos, tmp_path, descargar)
    assert hechas == {"a"} and fallos == 1
    assert not (tmp_path / "viejo.webp").exists()
    with Image.open(tmp_path / "a.webp") as img:
        assert img.format == "WEBP" and img.size == (miniaturas.LADO, miniaturas.LADO)
    assert (tmp_path / "a.webp").stat().st_size < 10_000

    # Ya hecha: no se vuelve a descargar.
    hechas, _ = miniaturas.actualizar(conciertos[:1], tmp_path, lambda url: 1 / 0)
    assert hechas == {"a"}


def test_listado_con_imagen_y_entradas():
    from collect import a_listado

    c = {"id": "x", "fecha": "2026-12-01", "hora": "21:00", "titulo": "T", "sala": "s",
         "precio_min": 10.0, "agotado": False, "generos": [], "url_entradas": "https://dice.fm/t"}
    assert a_listado(c, True) == {"id": "x", "f": "2026-12-01", "h": "21:00", "g": "T", "s": "s",
                                  "i": 1, "e": "https://dice.fm/t", "p": 10.0}
