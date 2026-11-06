#!/usr/bin/env bash
# Comando de build de Vercel (ver vercel.json).
# Si algo falla, se publica la versión ya incluida en docs/ en vez de romper el deploy.
cd "$(dirname "$0")/.."
PY=python3
if python3 -m venv .venv 2>/dev/null; then PY=.venv/bin/python; fi
if ! $PY -m pip install -q -r requirements.txt; then
  echo "AVISO: no se pudieron instalar dependencias; se publica docs/ tal cual."
  exit 0
fi
$PY scripts/vercel_build.py || echo "AVISO: el build falló; se publica docs/ tal cual."
exit 0
