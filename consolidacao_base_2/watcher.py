from __future__ import annotations

import os
import socket
import sys
import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from consolidacao_base_1.pasta import esperar_tamanho_estavel
from consolidacao_base_1.persistencia import carregar_consolidado, gravar_output
from consolidacao_base_2.motor import apply_confirmacoes_mp
from consolidacao_base_2.pasta import ARQUIVO_MP, eh_origem_mp, ler_xlsx_mp
from consolidacao_base_2.persistencia import controle_com_vistas, vistas_de_controle

HOSTNAME_PERMITIDO = "DaniGalera"
PASTA_PADRAO = Path(r"H:\Meu Drive\AUTOMACOES\dados\base_1")
ARQUIVO_OUTPUT = "output.xlsx"
DEBOUNCE_PROC_S = 4.0

_proc_lock = threading.Lock()
_debounce: dict[str, threading.Timer] = {}


def hostname_ok(atual: str | None = None) -> bool:
    return (atual or socket.gethostname()) == HOSTNAME_PERMITIDO


def sincronizar_mp(pasta: Path, *, semear: bool = False) -> None:
    origem = pasta / ARQUIVO_MP
    if not origem.is_file():
        return
    if not esperar_tamanho_estavel(origem):
        return
    try:
        lote = ler_xlsx_mp(origem)
    except OSError as extra:
        print(f"Falha ao ler {origem}: {extra}", file=sys.stderr, flush=True)
        return
    destino = pasta / ARQUIVO_OUTPUT
    try:
        consolidado, controle = carregar_consolidado(destino)
    except OSError as extra:
        print(f"Falha ao ler {destino}: {extra}", file=sys.stderr, flush=True)
        return
    vistas = vistas_de_controle(controle)
    novo_consolidado, novas_vistas = apply_confirmacoes_mp(
        consolidado, lote, vistas, semear=semear
    )
    if not semear and novas_vistas == vistas:
        return
    gravar_output(
        destino,
        novo_consolidado,
        HOSTNAME_PERMITIDO,
        controle=controle_com_vistas(novas_vistas, controle),
    )


def processar_origem(caminho: Path, pasta: Path) -> None:
    if not _esta_na_pasta(caminho, pasta):
        return
    if not eh_origem_mp(caminho):
        return
    chave = os.path.normcase(str(pasta / ARQUIVO_MP))

    def disparar() -> None:
        with _proc_lock:
            sincronizar_mp(pasta, semear=False)

    anterior = _debounce.get(chave)
    if anterior is not None:
        anterior.cancel()
    timer = threading.Timer(DEBOUNCE_PROC_S, disparar)
    timer.daemon = True
    _debounce[chave] = timer
    timer.start()


def _esta_na_pasta(caminho: Path, pasta: Path) -> bool:
    try:
        alvo = os.path.normcase(str(caminho.resolve()))
        raiz = os.path.normcase(str(pasta.resolve()))
    except OSError:
        return False
    return alvo == raiz or alvo.startswith(raiz + os.sep)


class HandlerMp(FileSystemEventHandler):
    def __init__(self, pasta: Path) -> None:
        super().__init__()
        self.pasta = pasta

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        processar_origem(Path(event.src_path), self.pasta)

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        processar_origem(Path(event.src_path), self.pasta)

    def on_moved(self, event) -> None:
        if event.is_directory:
            return
        processar_origem(Path(event.dest_path), self.pasta)


def observar(pasta: Path | None = None) -> None:
    if not hostname_ok():
        msg = (
            f"Hostname {socket.gethostname()!r} não é {HOSTNAME_PERMITIDO!r}. "
            "O watcher não vai gravar o output.xlsx."
        )
        print(msg, file=sys.stderr, flush=True)
        sys.exit(1)
    pasta = pasta or PASTA_PADRAO
    if not pasta.is_dir():
        print(f"Pasta não encontrada:\n{pasta}", file=sys.stderr, flush=True)
        sys.exit(1)
    try:
        with _proc_lock:
            sincronizar_mp(pasta, semear=True)
        observer = Observer()
        observer.schedule(HandlerMp(pasta), str(pasta), recursive=False)
        observer.start()
    except OSError as extra:
        print(f"Falha ao iniciar o watcher:\n{extra}", file=sys.stderr, flush=True)
        sys.exit(1)
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    observar()
