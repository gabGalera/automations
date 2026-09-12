from __future__ import annotations

from datetime import date, datetime
from typing import Any

from consolidacao_base_1.motor import (
    COLUNAS_RECEBIVEL,
    COLUNAS_TRANSACAO,
    ID_ADQUIRENTE,
)

COL_CONFIRMACAO = "Confirmacao MP"
COL_DATA_RECIBO = "Data Recibo MP"


def apply_confirmacoes_mp(
    consolidado: list[dict],
    lote: list[dict],
    vistas: set[tuple],
    *,
    semear: bool = False,
) -> tuple[list[dict], set[tuple]]:
    resultado = [dict(linha) for linha in consolidado]
    novas_vistas = set(vistas)
    extraidas = _tuplas_validas(lote)
    if semear:
        for tupla, _ in extraidas:
            novas_vistas.add(tupla)
        return resultado, novas_vistas
    extraidas.sort(key=lambda item: (item[0][1] < 0, item[0][2], item[1]))
    for tupla, _ in extraidas:
        if tupla in novas_vistas:
            continue
        chave, valor, data_recibo = tupla
        if valor > 0:
            _aplicar_positivo(resultado, chave, valor, data_recibo)
        else:
            resultado.append(_linha_estorno(resultado, chave, valor, data_recibo))
        novas_vistas.add(tupla)
    return resultado, novas_vistas


def _sem_confirmacao(row: dict) -> bool:
    return row.get(COL_CONFIRMACAO) in ("", None)


def _chave_data(valor: Any) -> tuple:
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        return (0, valor)
    return (1, date.max)


def _aplicar_positivo(consolidado: list[dict], chave: str, valor: int | float, data_recibo: date) -> None:
    vagas = [
        (i, row)
        for i, row in enumerate(consolidado)
        if row.get(ID_ADQUIRENTE) == chave and _sem_confirmacao(row)
    ]
    if not vagas:
        consolidado.append(_esqueleto_mp(chave, valor, data_recibo))
        return
    vagas.sort(key=lambda item: (_chave_data(item[1].get("Data Repasse")), _chave_data(item[1].get("data"))))
    i = vagas[0][0]
    preenchida = dict(consolidado[i])
    preenchida[COL_CONFIRMACAO] = valor
    preenchida[COL_DATA_RECIBO] = data_recibo
    consolidado[i] = preenchida


def _tuplas_validas(lote: list[dict]) -> list[tuple[tuple, int]]:
    extraidas = []
    for i, linha in enumerate(lote):
        tupla = _parse_confirmacao(linha)
        if tupla is None:
            continue
        extraidas.append((tupla, i))
    return extraidas


def _parse_confirmacao(linha: dict) -> tuple | None:
    chave = _id_estavel(linha.get(ID_ADQUIRENTE))
    if not chave:
        return None
    valor = _parse_confirmacao_mp(linha.get(COL_CONFIRMACAO))
    if valor is None:
        return None
    data_recibo = _parse_data_recibo(linha.get(COL_DATA_RECIBO))
    if data_recibo is None:
        return None
    return (chave, valor, data_recibo)


def _id_estavel(valor: Any) -> str:
    if valor is None or isinstance(valor, bool):
        return ""
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, float):
        if valor != valor or valor in (float("inf"), float("-inf")):
            return ""
        if valor.is_integer():
            return str(int(valor))
        return ""
    texto = str(valor).strip()
    if not texto:
        return ""
    lower = texto.lower()
    if "e" in lower:
        try:
            numero = float(texto)
        except ValueError:
            return texto
        if numero.is_integer():
            return str(int(numero))
        return ""
    return texto


def _parse_confirmacao_mp(valor: Any) -> int | float | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        if isinstance(valor, float) and (valor != valor or valor in (float("inf"), float("-inf"))):
            return None
        if valor == 0:
            return None
        if isinstance(valor, float) and valor.is_integer():
            return int(valor)
        return valor
    return None


def _parse_data_recibo(valor: Any) -> date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d-%m-%Y").date()
    except ValueError:
        return None


def _esqueleto_mp(chave: str, valor: int | float, data_recibo: date) -> dict:
    row = {col: "" for col in COLUNAS_TRANSACAO}
    row[ID_ADQUIRENTE] = chave
    for col in COLUNAS_RECEBIVEL:
        row[col] = ""
    row[COL_CONFIRMACAO] = valor
    row[COL_DATA_RECIBO] = data_recibo
    return row


def _linha_estorno(
    consolidado: list[dict], chave: str, valor: int | float, data_recibo: date
) -> dict:
    existentes = [row for row in consolidado if row.get(ID_ADQUIRENTE) == chave]
    if not existentes:
        return _esqueleto_mp(chave, valor, data_recibo)
    nova = {col: existentes[0].get(col, "") for col in COLUNAS_TRANSACAO}
    nova[ID_ADQUIRENTE] = chave
    for col in COLUNAS_RECEBIVEL:
        nova[col] = ""
    nova[COL_CONFIRMACAO] = valor
    nova[COL_DATA_RECIBO] = data_recibo
    return nova
