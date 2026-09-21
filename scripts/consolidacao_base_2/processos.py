from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MARCA_WATCHER = "consolidacao_base_2.watcher"


def eh_comando_watcher(command_line: str | None, pid: int, meu_pid: int) -> bool:
    if pid == meu_pid or not command_line:
        return False
    normalizado = command_line.replace("\\", "/").lower()
    return MARCA_WATCHER in normalizado


def eh_processo_a_controlar(command_line: str | None, pid: int, meu_pid: int) -> bool:
    return eh_comando_watcher(command_line, pid, meu_pid)


def pythonw_path() -> str:
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        return str(exe)
    candidato = exe.with_name("pythonw.exe")
    return str(candidato) if candidato.exists() else str(exe)


def raiz_projeto() -> Path:
    return Path(__file__).resolve().parent.parent


def _linhas_pythonw() -> list[tuple[int, str]]:
    comando = (
        "Get-CimInstance Win32_Process -Filter \"Name = 'pythonw.exe'\" | "
        "ForEach-Object { '{0}|{1}' -f $_.ProcessId, $_.CommandLine }"
    )
    try:
        bruto = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", comando],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    pares: list[tuple[int, str]] = []
    for linha in bruto.splitlines():
        linha = linha.strip()
        if "|" not in linha:
            continue
        pid_txt, _, cmd = linha.partition("|")
        try:
            pares.append((int(pid_txt), cmd))
        except ValueError:
            continue
    return pares


def pids_watcher(meu_pid: int | None = None) -> list[int]:
    meu = meu_pid if meu_pid is not None else os.getpid()
    return [pid for pid, cmd in _linhas_pythonw() if eh_processo_a_controlar(cmd, pid, meu)]


def watcher_ligado(meu_pid: int | None = None) -> bool:
    return bool(pids_watcher(meu_pid))


def ligar_watcher() -> None:
    meu = os.getpid()
    if any(eh_comando_watcher(cmd, pid, meu) for pid, cmd in _linhas_pythonw()):
        return
    desligar_watcher()
    flags = 0
    for nome in ("DETACHED_PROCESS", "CREATE_NEW_PROCESS_GROUP", "CREATE_NO_WINDOW"):
        flags |= int(getattr(subprocess, nome, 0))
    subprocess.Popen(
        [pythonw_path(), "-m", "consolidacao_base_2.watcher"],
        cwd=str(raiz_projeto()),
        creationflags=flags,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


def desligar_watcher() -> None:
    for pid in pids_watcher():
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
