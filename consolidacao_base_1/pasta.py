from __future__ import annotations

import csv
import time
import unicodedata
from pathlib import Path

PREFIXO_TRANSACAO = "transacoes_"
PREFIXO_RECEBIVEL = "recebiveis_"


def nomes_reentrantes(conhecidos: set[str], atuais: set[str]) -> set[str]:
    return atuais - conhecidos


def nomes_csv_na_pasta(pasta: Path) -> set[str]:
    nomes: set[str] = set()
    try:
        entradas = list(pasta.iterdir())
    except OSError:
        return nomes
    for caminho in entradas:
        try:
            if caminho.is_file() and classificar_entrada(caminho):
                nomes.add(caminho.name)
        except OSError:
            continue
    return nomes


def classificar_entrada(caminho: Path) -> str | None:
    nome = _normalizar_nome(caminho.name)
    if not nome.endswith(".csv"):
        return None
    if nome.startswith(PREFIXO_TRANSACAO):
        return "transacao"
    if nome.startswith(PREFIXO_RECEBIVEL):
        return "recebivel"
    return None


def ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def esperar_tamanho_estavel(
    caminho: Path,
    *,
    tentativas: int = 20,
    intervalo: float = 0.4,
) -> bool:
    ultimo = -1
    iguais = 0
    for _ in range(tentativas):
        try:
            tamanho = caminho.stat().st_size
        except OSError:
            time.sleep(intervalo)
            continue
        if tamanho == ultimo:
            iguais += 1
            if iguais >= 2:
                return True
        else:
            iguais = 0
            ultimo = tamanho
        time.sleep(intervalo)
    return False


def _normalizar_nome(nome: str) -> str:
    decomposto = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(ch for ch in decomposto if not unicodedata.combining(ch))
    return sem_acento.lower()
