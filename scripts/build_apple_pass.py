"""Crea y firma el pase de Apple Wallet (docs/tarjeta-fue.pkpass).

Requisitos (cuenta de Apple Developer, USD 99/año):
  1. Un "Pass Type ID" (ej. pass.ec.edu.uniecuador.tarjeta) y su certificado
     exportado como .p12  ->  certs/pass.p12
  2. El certificado intermedio de Apple "WWDR G4"  ->  certs/AppleWWDRCAG4.cer
  3. La contraseña del .p12 en la variable de entorno APPLE_P12_PASSWORD

Uso:
  python3 scripts/build_apple_pass.py
  python3 scripts/build_apple_pass.py --prueba   # firma con un certificado
                                                 # de prueba (no abre en Wallet)
"""
import argparse
import hashlib
import json
import os
import sys
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7, pkcs12

from common import BUILD, DOCS, ROOT, hex_to_rgb, load_config, pass_qr_text, pass_qr_value

OUTPUT = DOCS / "tarjeta-fue.pkpass"


def rgb(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return f"rgb({r}, {g}, {b})"


def pass_json(cfg):
    a, c, col = cfg["apple"], cfg["contacto"], cfg["colores"]
    barcode = {
        "format": "PKBarcodeFormatQR",
        "message": pass_qr_value(cfg),
        "messageEncoding": "iso-8859-1",
        "altText": pass_qr_text(cfg),
    }
    back = [
        {"key": "b_tel", "label": "Teléfono", "value": c["telefono_mostrado"],
         "dataDetectorTypes": ["PKDataDetectorTypePhoneNumber"]},
    ]
    for i, email in enumerate(c["emails"], 1):
        back.append({"key": f"b_email{i}", "label": "Correo", "value": email,
                     "dataDetectorTypes": ["PKDataDetectorTypeLink"]})
    back += [
        {"key": "b_web", "label": "Sitio web", "value": c["web"],
         "dataDetectorTypes": ["PKDataDetectorTypeLink"]},
        {"key": "b_info", "label": "Cómo compartir",
         "value": "Muestra el código QR: quien lo escanee con la cámara puede "
                  "agregar esta tarjeta a su Wallet y guardar el contacto."},
    ]
    secondary = [{"key": "tel", "label": "TELÉFONO", "value": c["telefono_mostrado"]}]
    if c.get("cargo"):
        secondary.insert(0, {"key": "cargo", "label": "CARGO", "value": c["cargo"]})

    return {
        "formatVersion": 1,
        "passTypeIdentifier": a["pass_type_identifier"],
        "teamIdentifier": a["team_identifier"],
        "serialNumber": a["serial_number"],
        "organizationName": cfg["organizacion"],
        "description": f"{cfg['titulo_tarjeta']} – {cfg['organizacion']}",
        "logoText": cfg["organizacion"],
        "backgroundColor": rgb(col["fondo"]),
        "foregroundColor": rgb(col["texto"]),
        "labelColor": rgb(col["etiquetas"]),
        "sharingProhibited": False,   # se puede compartir desde Wallet sin límite
        "generic": {
            "headerFields": [{"key": "tipo", "label": "", "value": "CONTACTO"}],
            "primaryFields": [{"key": "nombre", "label": "NOMBRE", "value": c["nombre_mostrado"]}],
            "secondaryFields": secondary,
            "auxiliaryFields": [
                {"key": "email", "label": "CORREO", "value": c["emails"][0]},
                {"key": "web", "label": "WEB", "value": c["web_mostrada"]},
            ],
            "backFields": back,
        },
        "barcodes": [barcode],
        "barcode": barcode,  # compatibilidad con iOS antiguos
    }


def load_signer(cfg, prueba):
    if prueba:
        return make_test_signer()
    a = cfg["apple"]
    p12_path, wwdr_path = ROOT / a["certificado_p12"], ROOT / a["certificado_wwdr"]
    missing = [str(p.relative_to(ROOT)) for p in (p12_path, wwdr_path) if not p.exists()]
    if missing:
        sys.exit("Faltan certificados de Apple: " + ", ".join(missing) +
                 "\nLee README.md -> 'Apple Wallet'. (Usa --prueba para probar sin certificados)")
    password = os.environ.get(a["certificado_p12_password_env"], "")
    key, cert, _ = pkcs12.load_key_and_certificates(
        p12_path.read_bytes(), password.encode() or None)
    wwdr_bytes = wwdr_path.read_bytes()
    try:
        wwdr = x509.load_der_x509_certificate(wwdr_bytes)
    except ValueError:
        wwdr = x509.load_pem_x509_certificate(wwdr_bytes)
    return key, cert, wwdr


def make_test_signer():
    """Certificado autofirmado SOLO para comprobar que el empaquetado funciona."""
    import datetime
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Prueba FUE")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1))
            .sign(key, hashes.SHA256()))
    return key, cert, cert


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prueba", action="store_true",
                        help="firmar con certificado de prueba (no válido en Wallet)")
    args = parser.parse_args()

    cfg = load_config()
    images = BUILD / "apple-images"
    if not images.exists():
        sys.exit("Primero ejecuta: python3 scripts/build_assets.py")

    files = {"pass.json": json.dumps(pass_json(cfg), ensure_ascii=False, indent=2).encode("utf-8")}
    for img in sorted(images.glob("*.png")):
        files[img.name] = img.read_bytes()

    manifest = {name: hashlib.sha1(data).hexdigest() for name, data in files.items()}
    files["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")

    key, cert, wwdr = load_signer(cfg, args.prueba)
    signature = (pkcs7.PKCS7SignatureBuilder()
                 .set_data(files["manifest.json"])
                 .add_signer(cert, key, hashes.SHA256())
                 .add_certificate(wwdr)
                 .sign(serialization.Encoding.DER,
                       [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary]))
    files["signature"] = signature

    out = BUILD / "tarjeta-fue-prueba.pkpass" if args.prueba else OUTPUT
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    print(f"Pase de Apple Wallet creado: {out.relative_to(ROOT)}"
          + ("  (PRUEBA: no se puede abrir en Wallet)" if args.prueba else ""))


if __name__ == "__main__":
    main()
