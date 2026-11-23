"""Miniaturas de los carteles para el listado de la agenda.

Los carteles de las salas suelen ser PNG de cientos de KB. Para el listado se
guarda una miniatura cuadrada en WebP de pocos KB en web/data/min/<id>.webp.
Una miniatura ya hecha no se vuelve a descargar.
"""

from io import BytesIO

from PIL import Image, ImageOps

LADO = 144          # px; se muestra a 64 px, así queda nítida en pantallas 2x
CALIDAD = 70
MAX_BYTES = 15_000_000  # no descargar carteles desmesurados


def hacer_miniatura(contenido):
    """Bytes de una imagen -> bytes WebP cuadrados de LADO x LADO."""
    with Image.open(BytesIO(contenido)) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "transparency" in img.info or img.mode in ("LA", "PA") else "RGB")
        if img.mode == "RGBA":
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            fondo.paste(img, mask=img.getchannel("A"))
            img = fondo
        img = ImageOps.fit(img, (LADO, LADO), Image.LANCZOS, centering=(0.5, 0.4))
        salida = BytesIO()
        img.save(salida, "WEBP", quality=CALIDAD, method=6)
        return salida.getvalue()


def actualizar(conciertos, carpeta, descargar):
    """Crea las miniaturas que falten y borra las de conciertos que ya no están.

    `descargar(url)` devuelve los bytes de la imagen. Devuelve el conjunto de ids
    que tienen miniatura. Un cartel que no se puede leer no detiene la agenda.
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    con_miniatura, fallos = set(), 0
    for c in conciertos:
        destino = carpeta / f"{c['id']}.webp"
        if destino.exists():
            con_miniatura.add(c["id"])
            continue
        if not c.get("imagen"):
            continue
        try:
            destino.write_bytes(hacer_miniatura(descargar(c["imagen"])))
            con_miniatura.add(c["id"])
        except Exception:
            fallos += 1
    for vieja in carpeta.glob("*.webp"):
        if vieja.stem not in {c["id"] for c in conciertos}:
            vieja.unlink()
    return con_miniatura, fallos
