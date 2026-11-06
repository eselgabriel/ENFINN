"""Build en Vercel: toma las credenciales de las variables de entorno del
proyecto, genera la tarjeta y los pases en docs/ y borra las credenciales."""
import base64
import os
import shutil
import subprocess
import sys

from common import ROOT, load_config


def main():
    cfg = load_config()
    print(f"Sitio público: {cfg['sitio_publico']}")
    certs = ROOT / "certs"
    certs.mkdir(exist_ok=True)
    try:
        sa = os.environ.get("GOOGLE_WALLET_SA_JSON", "").strip()
        if sa:
            (ROOT / cfg["google"]["service_account_json"]).write_text(sa, encoding="utf-8")
            print("Google Wallet: credencial cargada")
        else:
            print("Google Wallet: falta GOOGLE_WALLET_SA_JSON (se omite)")
        p12, wwdr = os.environ.get("APPLE_P12_BASE64", ""), os.environ.get("APPLE_WWDR_BASE64", "")
        if p12 and wwdr:
            (ROOT / cfg["apple"]["certificado_p12"]).write_bytes(base64.b64decode(p12))
            (ROOT / cfg["apple"]["certificado_wwdr"]).write_bytes(base64.b64decode(wwdr))
            print("Apple Wallet: certificados cargados")
        else:
            print("Apple Wallet: faltan APPLE_P12_BASE64 / APPLE_WWDR_BASE64 (se omite)")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")])
    finally:
        shutil.rmtree(certs, ignore_errors=True)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
