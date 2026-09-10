from __future__ import annotations

import sys


def aviso(titulo: str, texto: str, *, erro: bool = False) -> None:
    if sys.platform == "win32":
        import ctypes

        icone = 0x10 if erro else 0x40
        ctypes.windll.user32.MessageBoxW(0, texto, titulo, icone)
        return
    stream = sys.stderr if erro else sys.stdout
    print(f"{titulo}: {texto}", file=stream, flush=True)
