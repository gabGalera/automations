from __future__ import annotations

import importlib
import sys
from types import ModuleType

from agent.config import SCRIPTS_ROOT


def _garantir_scripts_no_path() -> None:
    raiz = str(SCRIPTS_ROOT.resolve())
    if raiz not in sys.path:
        sys.path.insert(0, raiz)


def modulo_processos(nome_modulo: str) -> ModuleType:
    _garantir_scripts_no_path()
    return importlib.import_module(f"{nome_modulo}.processos")


def watcher_ligado(nome_modulo: str) -> bool:
    return bool(modulo_processos(nome_modulo).watcher_ligado())


def ligar_watcher(nome_modulo: str) -> None:
    modulo_processos(nome_modulo).ligar_watcher()


def desligar_watcher(nome_modulo: str) -> None:
    modulo_processos(nome_modulo).desligar_watcher()
