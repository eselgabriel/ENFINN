"""Crea el pase de Google Wallet y el enlace "Agregar a Google Wallet".

El pase se crea UNA sola vez con "MULTIPLE_HOLDERS": el mismo enlace sirve
para un número ilimitado de personas y teléfonos.

Requisitos (gratis):
  1. Cuenta de emisor en Google Pay & Wallet Console -> Issuer ID en config.json
  2. Un service account de Google Cloud con la "Google Wallet API" activada,
     agregado como usuario en la Wallet Console. Su llave JSON en
     certs/google-service-account.json
  3. Las imágenes publicadas en "sitio_publico" (Google las descarga de ahí).

Uso:
  python3 scripts/build_google_pass.py            # crea/actualiza vía API + enlace
  python3 scripts/build_google_pass.py --sin-api  # solo genera el enlace (el
                                                  # pase se crea al primer guardado)
"""
import argparse
import json
import sys
import time

from google.auth import crypt, jwt
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

from common import BUILD, DOCS, ROOT, load_config, pass_qr_text, pass_qr_value, public_url

API = "https://walletobjects.googleapis.com/walletobjects/v1"
SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]


def ids(cfg):
    g = cfg["google"]
    return f"{g['issuer_id']}.{g['class_suffix']}", f"{g['issuer_id']}.{g['object_suffix']}"


def text(value):
    return {"defaultValue": {"language": "es", "value": value}}


def generic_class(cfg):
    class_id, _ = ids(cfg)
    # Plantilla: dos filas de datos debajo del nombre
    row = lambda left, right: {"twoItems": {
        "startItem": {"firstValue": {"fields": [{"fieldPath": f"object.textModulesData['{left}']"}]}},
        "endItem": {"firstValue": {"fields": [{"fieldPath": f"object.textModulesData['{right}']"}]}},
    }}
    return {
        "id": class_id,
        "classTemplateInfo": {"cardTemplateOverride": {"cardRowTemplateInfos": [
            row("telefono", "web"),
        ]}},
    }


def generic_object(cfg):
    class_id, object_id = ids(cfg)
    c = cfg["contacto"]
    modules = [
        {"id": "telefono", "header": "Teléfono", "body": c["telefono_mostrado"]},
        {"id": "web", "header": "Web", "body": c["web_mostrada"]},
    ]
    if c.get("cargo"):
        modules.insert(0, {"id": "cargo", "header": "Cargo", "body": c["cargo"]})
    for i, email in enumerate(c["emails"], 1):
        modules.append({"id": f"email{i}", "header": "Correo", "body": email})

    links = [{"id": "tel", "uri": f"tel:{c['telefono']}", "description": f"Llamar {c['telefono_mostrado']}"}]
    links += [{"id": f"mail{i}", "uri": f"mailto:{e}", "description": e}
              for i, e in enumerate(c["emails"], 1)]
    links.append({"id": "web", "uri": c["web"], "description": c["web_mostrada"]})
    links.append({"id": "vcf", "uri": public_url(cfg, "contacto.vcf"),
                  "description": "Guardar contacto (.vcf)"})

    return {
        "id": object_id,
        "classId": class_id,
        "state": "ACTIVE",
        "multipleDevicesAndHoldersAllowedStatus": "MULTIPLE_HOLDERS",
        "hexBackgroundColor": cfg["colores"]["fondo"],
        "logo": {"sourceUri": {"uri": public_url(cfg, "img/google-logo.png")},
                 "contentDescription": text(cfg["organizacion"])},
        "heroImage": {"sourceUri": {"uri": public_url(cfg, "img/google-hero.png")},
                      "contentDescription": text(cfg["organizacion"])},
        "cardTitle": text(cfg["organizacion"]),
        "subheader": text(c.get("cargo") or cfg["titulo_tarjeta"]),
        "header": text(c["nombre_mostrado"]),
        "textModulesData": modules,
        "linksModuleData": {"uris": links},
        "barcode": {"type": "QR_CODE", "value": pass_qr_value(cfg),
                    "alternateText": pass_qr_text(cfg)},
    }


def upsert(session, kind, body):
    url = f"{API}/{kind}"
    r = session.get(f"{url}/{body['id']}")
    if r.status_code == 404:
        r = session.post(url, json=body)
        action = "creado"
    elif r.ok:
        r = session.put(f"{url}/{body['id']}", json=body)
        action = "actualizado"
    else:
        action = "consultado"
    if not r.ok:
        sys.exit(f"Error de Google Wallet API ({kind}): {r.status_code} {r.text}")
    print(f"  {kind} {action}: {body['id']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sin-api", action="store_true",
                        help="no llamar a la API; incluir clase y objeto completos en el enlace")
    args = parser.parse_args()

    cfg = load_config()
    key_path = ROOT / cfg["google"]["service_account_json"]
    if not cfg["google"]["issuer_id"].isdigit() or cfg["google"]["issuer_id"].startswith("3388000000000000000"):
        print("Aviso: el Issuer ID parece de ejemplo; usa el tuyo (config.json o GOOGLE_WALLET_ISSUER_ID).")
    if not key_path.exists():
        sys.exit(f"Falta la llave del service account: {key_path.relative_to(ROOT)}\n"
                 "Lee README.md -> 'Google Wallet'.")
    cls, obj = generic_class(cfg), generic_object(cfg)
    BUILD.mkdir(exist_ok=True)
    (BUILD / "google-class.json").write_text(json.dumps(cls, ensure_ascii=False, indent=2), encoding="utf-8")
    (BUILD / "google-object.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.sin_api:
        payload = {"genericClasses": [cls], "genericObjects": [obj]}
    else:
        creds = service_account.Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
        session = AuthorizedSession(creds)
        upsert(session, "genericClass", cls)
        upsert(session, "genericObject", obj)
        payload = {"genericObjects": [{"id": obj["id"]}]}  # enlace corto

    info = json.loads(key_path.read_text())
    claims = {
        "iss": info["client_email"],
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "origins": [cfg["sitio_publico"]],
        "payload": payload,
    }
    signer = crypt.RSASigner.from_service_account_info(info)
    token = jwt.encode(signer, claims).decode()
    link = f"https://pay.google.com/gp/v/save/{token}"
    (DOCS / "google-wallet-link.txt").write_text(link + "\n", encoding="utf-8")
    print(f"Enlace de Google Wallet guardado en docs/google-wallet-link.txt ({len(link)} caracteres)")


if __name__ == "__main__":
    main()
