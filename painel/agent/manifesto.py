from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from agent.config import MANIFESTO_PATH


@dataclass(frozen=True)
class Automacao:
    id: str
    titulo: str
    modulo: str
    pasta: str


def carregar_manifesto(caminho: Path | None = None) -> list[Automacao]:
    alvo = caminho or MANIFESTO_PATH
    bruto = yaml.safe_load(alvo.read_text(encoding="utf-8"))
    entradas = bruto.get("automacoes", [])
    return [
        Automacao(
            id=str(item["id"]),
            titulo=str(item["titulo"]),
            modulo=str(item["modulo"]),
            pasta=str(item["pasta"]),
        )
        for item in entradas
    ]
