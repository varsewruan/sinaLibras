# -*- mode: python ; coding: utf-8 -*-
"""
Spec do PyInstaller para o SINALibras desktop.

Rode a partir de desktop/ (veja README.md) — os caminhos abaixo são relativos
à raiz do repo, resolvida a partir do SPECPATH.

Saída: dist/SINALibras/ (modo onedir). Onedir e não onefile de propósito: o
onefile descompacta ~200MB em %TEMP% a cada abertura, o que faz o app demorar
uns 10s pra aparecer e ainda tranca o mongod embutido em pasta temporária.
Onedir abre rápido e é o que vai zipado pro usuário final.
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).resolve().parent          # noqa: F821 — injetado pelo PyInstaller
BACKEND = ROOT / "backend"
MONGOD = Path(os.environ["SINA_MONGOD"])        # caminho do mongod.exe (ver README)
FRONTEND_BUILD = ROOT / "frontend" / "build"

for required in (BACKEND / "app", FRONTEND_BUILD, MONGOD):
    if not required.exists():
        raise SystemExit(f"faltando: {required}")

datas = [
    # SPA já buildado com REACT_APP_BACKEND_URL="" (mesma origem).
    (str(FRONTEND_BUILD), "frontend_build"),
    # SVGs + vídeos dos sinais, servidos em /signs/*.
    (str(BACKEND / "static" / "signs"), "signs"),
    # mongod embutido.
    (str(MONGOD), "mongodb"),
]

hiddenimports = [
    # uvicorn resolve loop/protocolo por string em runtime, então o PyInstaller
    # não enxerga esses imports no grafo estático.
    *collect_submodules("uvicorn"),
    # motor/pymongo idem, para os módulos de encoding do BSON.
    *collect_submodules("pymongo"),
    *collect_submodules("motor"),
    "email_validator",
]

a = Analysis(                                    # noqa: F821
    ["launcher.py"],
    pathex=[str(BACKEND)],                       # torna `app` e `scripts` importáveis
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # Pesos mortos que entrariam de carona pelas dependências de teste.
    excludes=["tkinter", "pytest", "httpx", "matplotlib", "numpy"],
    noarchive=False,
)

pyz = PYZ(a.pure)                                # noqa: F821

exe = EXE(                                       # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SINALibras",
    debug=False,
    strip=False,
    upx=False,
    # Sem console: é um app de janela. Erros de boot viram MessageBox e log
    # (ver _show_error no launcher), senão a falha fica invisível.
    console=False,
)

coll = COLLECT(                                  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SINALibras",
)
