"""Utilidades compartidas: configuración, rutas y la vCard del QR."""
import json
import os
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"              # sitio público (GitHub Pages / hosting)
BUILD = ROOT / "build"            # archivos intermedios (no se suben)
ASSETS = ROOT / "assets"
LOGO = ASSETS / "logo-fue.png"


# Valores que se pueden pasar por variables de entorno (útil en GitHub Actions)
ENV_OVERRIDES = {
    "GOOGLE_WALLET_ISSUER_ID": ("google", "issuer_id"),
    "APPLE_TEAM_ID": ("apple", "team_identifier"),
    "APPLE_PASS_TYPE_ID": ("apple", "pass_type_identifier"),
}


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        cfg = json.load(f)
    for env, (section, key) in ENV_OVERRIDES.items():
        if os.environ.get(env):
            cfg[section][key] = os.environ[env].strip()
    # Dirección pública: SITIO_PUBLICO o, en Vercel, el dominio de producción
    if os.environ.get("SITIO_PUBLICO"):
        cfg["sitio_publico"] = os.environ["SITIO_PUBLICO"].strip().rstrip("/")
    elif os.environ.get("VERCEL_PROJECT_PRODUCTION_URL"):
        cfg["sitio_publico"] = "https://" + os.environ["VERCEL_PROJECT_PRODUCTION_URL"].strip().rstrip("/")
    return cfg


WALLET_PATH = "w/"   # página corta que abre "Agregar a Wallet"


def pass_qr_value(cfg):
    """Contenido del QR que aparece dentro del pase.
    - "wallet": un enlace corto; quien lo escanea con la cámara agrega la
      tarjeta a su Google Wallet (Android) o Apple Wallet (iPhone).
    - "contacto": la vCard; quien lo escanea guarda el contacto."""
    if cfg.get("qr_del_pase", "wallet") == "wallet":
        return public_url(cfg, WALLET_PATH)
    return build_vcard(cfg, ascii_safe=True)


def pass_qr_text(cfg):
    if cfg.get("qr_del_pase", "wallet") == "wallet":
        return "Escanea para agregar esta tarjeta a tu Wallet"
    return "Escanea para guardar el contacto"


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
