from __future__ import annotations

import socket
import sys

import uvicorn

from agent.config import API_HOST, API_PORT, WEB_DIST


def _porta_livre() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((API_HOST, API_PORT))
        except OSError:
            return False
    return True


def main() -> None:
    if not _porta_livre():
        print(
            f"Porta {API_PORT} já está em uso em {API_HOST}.\n"
            "Encerre o agente anterior ou use outra porta:\n"
            f"  $env:PAINEL_API_PORT=8766; python -m agent",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not WEB_DIST.is_dir():
        print(
            f"Aviso: frontend não buildado ({WEB_DIST}).\n"
            "Rode .\\setup.ps1 na pasta painel/ ou acesse / para instruções.",
            file=sys.stderr,
        )

    uvicorn.run(
        "agent.api:app",
        host=API_HOST,
        port=API_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
