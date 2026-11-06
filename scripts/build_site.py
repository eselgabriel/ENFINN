"""Genera docs/index.html: la tarjeta digital que se comparte por enlace."""
import html

from common import DOCS, ROOT, ascii_only, load_config, public_url

MAIL_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/>'
             '<path d="m22 7-10 6L2 7"/></svg>')


def main():
    cfg = load_config()
    c = cfg["contacto"]
    e = html.escape
    google_file = DOCS / "google-wallet-link.txt"
    google_link = google_file.read_text().strip() if google_file.exists() else ""
    has_apple = (DOCS / "tarjeta-fue.pkpass").exists()

    emails_html = "\n      ".join(
        f'<li><a href="mailto:{e(m)}">{MAIL_ICON}<span>{e(m)}</span></a></li>' for m in c["emails"])
    values = {
        "organizacion": e(cfg["organizacion"]),
        "titulo_tarjeta": e(cfg["titulo_tarjeta"]),
        "nombre_mostrado": e(c["nombre_mostrado"]),
        "nombre_titulo": e(f"{c['nombre']} {c['apellido']}"),
        "cargo_html": f'<div class="role">{e(c["cargo"])}</div>' if c.get("cargo") else "",
        "telefono": e(c["telefono"]),
        "telefono_mostrado": e(c["telefono_mostrado"]),
        "emails_html": emails_html,
        "web": e(c["web"]),
        "web_mostrada": e(c["web_mostrada"]),
        "color_etiquetas": e(cfg["colores"]["etiquetas"]),
        "og_image": e(public_url(cfg, "img/google-hero.png")),
        "google_link": e(google_link or "#"),
        "google_class": "" if google_link else "hidden",
        "apple_class": "" if has_apple else "hidden",
        "vcf_nombre": e(ascii_only(f"{c['nombre']}-{c['apellido']}").replace(" ", "-") + ".vcf"),
    }
    page = (ROOT / "scripts" / "site_template.html").read_text(encoding="utf-8")
    for key, val in values.items():
        page = page.replace("{{" + key + "}}", val)
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("")
    print("Página creada: docs/index.html"
          f"  (Apple Wallet: {'sí' if has_apple else 'pendiente'},"
          f" Google Wallet: {'sí' if google_link else 'pendiente'})")


if __name__ == "__main__":
    main()
