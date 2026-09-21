from __future__ import annotations

import os
from pathlib import Path

PAINEL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_ROOT = PAINEL_ROOT.parent / "scripts"
MANIFESTO_PATH = PAINEL_ROOT / "automacoes.yaml"
WEB_DIST = PAINEL_ROOT / "web" / "dist"
API_HOST = os.environ.get("PAINEL_API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("PAINEL_API_PORT", "8765"))
