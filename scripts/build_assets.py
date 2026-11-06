"""Genera el QR (vCard), el archivo .vcf y todas las imágenes que piden
Apple Wallet, Google Wallet y la página web."""
from pathlib import Path

import qrcode
import qrcode.image.svg
from PIL import Image, ImageDraw, ImageFont

from common import BUILD, DOCS, LOGO, WALLET_PATH, build_vcard, hex_to_rgb, load_config, public_url

RAINBOW = ["#E30613", "#1E6BB8", "#2BB7D0", "#4CAF3A", "#F2C318", "#F07D00", "#8E3E96"]


def square_logo(pad_ratio=0.08):
    """Recorta el espacio vacío del logo y lo deja cuadrado con margen."""
    im = Image.open(LOGO).convert("RGBA")
    im = im.crop(im.getbbox())
    side = int(max(im.size) * (1 + 2 * pad_ratio))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
    return canvas


def on_background(im, color):
    bg = Image.new("RGBA", im.size, hex_to_rgb(color) + (255,))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def resized(im, size):
    return im.resize(size, Image.LANCZOS)


def load_font(size, bold=True):
    candidates = [
        "/usr/share/fonts/opentype/inter/Inter-Bold.otf" if bold else
        "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def rainbow_bar(draw, x0, y0, width, height):
    seg = width / len(RAINBOW)
    for i, color in enumerate(RAINBOW):
        draw.rectangle([x0 + i * seg, y0, x0 + (i + 1) * seg, y0 + height], fill=color)


def build_hero(cfg, logo):
    """Banner para Google Wallet (1032x336)."""
    w, h = 1032, 336
    hero = Image.new("RGB", (w, h), "#FFFFFF")
    lg = resized(logo, (260, 260))
    hero.paste(lg, (48, (h - 260) // 2 - 6), lg)
    draw = ImageDraw.Draw(hero)
    org = cfg["organizacion"].upper()
    font = load_font(46)
    small = load_font(28, bold=False)
    draw.text((340, 112), org, font=font, fill="#111111")
    draw.text((342, 178), cfg["contacto"]["web_mostrada"], font=small, fill="#1E6BB8")
    rainbow_bar(draw, 0, h - 14, w, 14)
    return hero


def build_qr(data, out_png, out_svg):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=12, border=3)
    qr.add_data(data.encode("utf-8"))
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(out_png)
    svg = qrcode.make(data.encode("utf-8"), image_factory=qrcode.image.svg.SvgPathImage,
                      error_correction=qrcode.constants.ERROR_CORRECT_M, border=3)
    svg.save(out_svg)
    return qr.version


def main():
    cfg = load_config()
    img_dir = DOCS / "img"
    apple_dir = BUILD / "apple-images"
    for d in (img_dir, apple_dir):
        d.mkdir(parents=True, exist_ok=True)

    logo = square_logo()
    fondo = cfg["colores"]["fondo"]

    # --- Contacto ---------------------------------------------------------
    vcard_qr = build_vcard(cfg, ascii_safe=True)
    (BUILD / "vcard.txt").write_text(vcard_qr, encoding="utf-8")
    # El .vcf descargable conserva acentos (los teléfonos lo leen en UTF-8)
    (DOCS / "contacto.vcf").write_bytes(build_vcard(cfg, ascii_safe=False).encode("utf-8"))
    version = build_qr(vcard_qr, DOCS / "qr-contacto.png", DOCS / "qr-contacto.svg")
    # QR "como pase físico": abre Agregar a Google/Apple Wallet
    wallet_url = public_url(cfg, WALLET_PATH)
    build_qr(wallet_url, DOCS / "qr-wallet.png", DOCS / "qr-wallet.svg")
    print(f"QR de Wallet -> {wallet_url}")

    # --- Web -------------------------------------------------------------
    resized(logo, (512, 512)).save(img_dir / "logo.png")
    on_background(resized(logo, (180, 180)), fondo).save(img_dir / "apple-touch-icon.png")
    resized(logo, (64, 64)).save(img_dir / "favicon.png")

    # --- Google Wallet (imágenes deben estar en una URL pública) ----------
    on_background(resized(logo, (660, 660)), "#FFFFFF").save(img_dir / "google-logo.png")
    build_hero(cfg, logo).save(img_dir / "google-hero.png")

    # --- Apple Wallet (van dentro del .pkpass) ----------------------------
    for scale, suffix in ((1, ""), (2, "@2x"), (3, "@3x")):
        on_background(resized(logo, (29 * scale, 29 * scale)), fondo).save(apple_dir / f"icon{suffix}.png")
        resized(logo, (50 * scale, 50 * scale)).save(apple_dir / f"logo{suffix}.png")
        resized(logo, (90 * scale, 90 * scale)).save(apple_dir / f"thumbnail{suffix}.png")

    print(f"QR generado (versión {version}, {len(vcard_qr)} caracteres)")
    print(f"Imágenes en {img_dir.relative_to(DOCS.parent)} y {apple_dir.relative_to(BUILD.parent)}")


if __name__ == "__main__":
    main()
