"""Utilidades compartidas: configuración, rutas y la vCard del QR."""
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"              # sitio público (GitHub Pages / hosting)
BUILD = ROOT / "build"            # archivos intermedios (no se suben)
ASSETS = ROOT / "assets"
LOGO = ASSETS / "logo-fue.png"


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def ascii_only(text):
    """Quita acentos. Algunos lectores QR de Android muestran mal los
    caracteres especiales, así que la vCard del QR va en ASCII puro."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def _esc(value):
    # Escapes requeridos por vCard 3.0
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def build_vcard(cfg, ascii_safe=True):
    """vCard 3.0. Al escanearla con la cámara (iPhone o Android) el teléfono
    ofrece 'Agregar contacto' de inmediato, sin internet."""
    c = cfg["contacto"]
    fix = ascii_only if ascii_safe else (lambda s: s)
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{_esc(fix(c['apellido']))};{_esc(fix(c['nombre']))};;;",
        f"FN:{_esc(fix(c['nombre'] + ' ' + c['apellido']))}",
        f"ORG:{_esc(fix(cfg['organizacion']))}",
    ]
    if c.get("cargo"):
        lines.append(f"TITLE:{_esc(fix(c['cargo']))}")
    lines.append(f"TEL;TYPE=CELL:{c['telefono']}")
    lines += [f"EMAIL:{email}" for email in c["emails"]]
    lines.append(f"URL:{c['web']}")
    lines.append("END:VCARD")
    return "\r\n".join(lines)


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def public_url(cfg, path):
    return cfg["sitio_publico"].rstrip("/") + "/" + path.lstrip("/")
