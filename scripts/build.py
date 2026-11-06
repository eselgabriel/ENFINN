"""Construye todo lo que se pueda con las credenciales disponibles.

  python3 scripts/build.py
"""
import subprocess
import sys

from common import ROOT, load_config

HERE = ROOT / "scripts"


def run(script, *args):
    print(f"\n▶ {script}")
    subprocess.run([sys.executable, str(HERE / script), *args], check=True)


def main():
    cfg = load_config()
    run("build_assets.py")
    a, g = cfg["apple"], cfg["google"]
    if (ROOT / a["certificado_p12"]).exists() and (ROOT / a["certificado_wwdr"]).exists():
        run("build_apple_pass.py")
    else:
        print("\n• Apple Wallet: faltan certificados en certs/ (ver README). Se omite.")
    if (ROOT / g["service_account_json"]).exists():
        run("build_google_pass.py")
    else:
        print("• Google Wallet: falta certs/google-service-account.json (ver README). Se omite.")
    run("build_site.py")


if __name__ == "__main__":
    main()
