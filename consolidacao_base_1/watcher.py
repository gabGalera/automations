from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from consolidacao_base_1.aviso import aviso
from consolidacao_base_1.motor import apply_lote
from consolidacao_base_1.pasta import (
    classificar_entrada,
    esperar_tamanho_estavel,
    ler_csv,
    nomes_csv_na_pasta,
    nomes_reentrantes,
)
from consolidacao_base_1.persistencia import carregar_consolidado, gravar_output

HOSTNAME_PERMITIDO = "DaniGalera"
PASTA_PADRAO = Path(r"H:\Meu Drive\AUTOMACOES\dados\base_1")
ARQUIVO_OUTPUT = "output.xlsx"
INTERVALO_POLL_S = 1.0
DEBOUNCE_PROC_S = 4.0

_proc_lock = threading.Lock()
_ultimo_ok: dict[str, float] = {}


def hostname_ok(atual: str | None = None) -> bool:
    return (atual or socket.gethostname()) == HOSTNAME_PERMITIDO


def _esta_na_pasta(caminho: Path, pasta: Path) -> bool:
    try:
        alvo = os.path.normcase(str(caminho.resolve()))
        raiz = os.path.normcase(str(pasta.resolve()))
    except OSError:
        return False
    return alvo == raiz or alvo.startswith(raiz + os.sep)


def processar_arquivo(caminho: Path, pasta: Path) -> None:
    with _proc_lock:
        _processar_arquivo_locked(caminho, pasta)


def _processar_arquivo_locked(caminho: Path, pasta: Path) -> None:
    if not _esta_na_pasta(caminho, pasta):
        return
    tipo = classificar_entrada(caminho)
    if tipo is None:
        return
    chave = os.path.normcase(str(caminho.resolve()))
    agora = time.monotonic()
    if agora - _ultimo_ok.get(chave, 0) < DEBOUNCE_PROC_S:
        return
    if not esperar_tamanho_estavel(caminho):
        return
    try:
        linhas = ler_csv(caminho)
    except OSError as extra:
        print(f"Falha ao ler {caminho}: {extra}", file=sys.stderr, flush=True)
        return
    destino = pasta / ARQUIVO_OUTPUT
    try:
        consolidado, controle = carregar_consolidado(destino)
    except OSError as extra:
        print(f"Falha ao ler {destino}: {extra}", file=sys.stderr, flush=True)
        aviso("Consolidação base_1", f"Não deu para ler o output.xlsx:\n{extra}", erro=True)
        return
    consolidado = apply_lote(consolidado, {"tipo": tipo, "linhas": linhas})
    gravar_output(destino, consolidado, HOSTNAME_PERMITIDO, controle=controle)
    _ultimo_ok[chave] = time.monotonic()


def _loop_reentrada(pasta: Path, conhecidos: set[str], parar: threading.Event) -> None:
    while not parar.wait(INTERVALO_POLL_S):
        atuais = nomes_csv_na_pasta(pasta)
        for nome in sorted(nomes_reentrantes(conhecidos, atuais)):
            processar_arquivo(pasta / nome, pasta)
        conhecidos.clear()
        conhecidos.update(atuais)


class HandlerEntrada(FileSystemEventHandler):
    def __init__(self, pasta: Path) -> None:
        super().__init__()
        self.pasta = pasta

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        processar_arquivo(Path(event.src_path), self.pasta)

    def on_moved(self, event) -> None:
        if event.is_directory:
            return
        processar_arquivo(Path(event.dest_path), self.pasta)


def observar(pasta: Path | None = None) -> None:
    if not hostname_ok():
        msg = (
            f"Hostname {socket.gethostname()!r} não é {HOSTNAME_PERMITIDO!r}. "
            "O watcher não vai gravar o output.xlsx."
        )
        print(msg, file=sys.stderr, flush=True)
        aviso("Consolidação base_1", msg, erro=True)
        sys.exit(1)
    pasta = pasta or PASTA_PADRAO
    if not pasta.is_dir():
        msg = f"Pasta não encontrada:\n{pasta}"
        print(msg, file=sys.stderr, flush=True)
        aviso("Consolidação base_1", msg, erro=True)
        sys.exit(1)
    destino = pasta / ARQUIVO_OUTPUT
    parar = threading.Event()
    try:
        if not destino.exists():
            gravar_output(destino, [], HOSTNAME_PERMITIDO)
        observer = Observer()
        observer.schedule(HandlerEntrada(pasta), str(pasta), recursive=False)
        observer.start()
        conhecidos = nomes_csv_na_pasta(pasta)
        polling = threading.Thread(
            target=_loop_reentrada,
            args=(pasta, conhecidos, parar),
            daemon=True,
        )
        polling.start()
    except OSError as extra:
        msg = f"Falha ao iniciar o watcher:\n{extra}"
        print(msg, file=sys.stderr, flush=True)
        aviso("Consolidação base_1", msg, erro=True)
        sys.exit(1)
    try:
        observer.join()
    except KeyboardInterrupt:
        parar.set()
        observer.stop()
        observer.join()


if __name__ == "__main__":
    observar()
