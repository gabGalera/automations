from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any

ID_ADQUIRENTE = "ID Trans. Adquirente"

COLUNAS_TRANSACAO = [
    "ID Transacao",
    "Cliente",
    "data",
    "hora",
    "Adquirente",
    ID_ADQUIRENTE,
    "Status",
    "Valor Transacao",
    "Tipo",
    "Parcelas",
    "Bandeira",
    "Aut",
    "Cartao",
    "Taxa %",
    "Taxa Valor",
    "Valor Liquido",
    "Total Reembolsado",
]

COLUNAS_RECEBIVEL = [
    "Parcela Recebivel",
    "Total Parcelas",
    "taxa % cliente",
    "taxa valor cliente",
    "Valor Repasse",
    "Data Repasse",
]

COLUNAS_CONFIRMACAO_MP = [
    "Confirmacao MP",
    "Data Recibo MP",
]

COL_CONFIRMACAO = "Confirmacao MP"
COL_DATA_RECIBO = "Data Recibo MP"


@dataclass
class Estado:
    consolidado: list[dict]
    maquinha: set[str]
    pendentes: set[tuple]


def apply_lote(estado: Estado, lote: dict) -> Estado:
    consolidado = [dict(linha) for linha in estado.consolidado]
    maquinha = set(estado.maquinha)
    pendentes = set(estado.pendentes)
    tipo = lote["tipo"]
    if tipo == "transacao":
        consolidado, ids_lote = _aplicar_linhas_transacao(consolidado, lote["linhas"])
        consolidado, maquinha, pendentes = _liberar_maquinha(
            consolidado, maquinha, pendentes, ids_lote
        )
    elif tipo == "recebivel":
        consolidado, ids_lote = _aplicar_linhas_recebivel(consolidado, lote["linhas"])
        consolidado, maquinha, pendentes = _liberar_maquinha(
            consolidado, maquinha, pendentes, ids_lote
        )
    elif tipo == "confirmacao_mp":
        consolidado, maquinha, pendentes = _aplicar_confirmacoes_mp(
            consolidado, maquinha, pendentes, lote["linhas"]
        )
    return Estado(consolidado=consolidado, maquinha=maquinha, pendentes=pendentes)


def _aplicar_linhas_transacao(
    consolidado: list[dict], linhas: list[dict]
) -> tuple[list[dict], set[str]]:
    ids_lote: set[str] = set()
    for linha in linhas:
        chave = _id_estavel(linha.get(ID_ADQUIRENTE))
        if not chave:
            continue
        ids_lote.add(chave)
        consolidado = _aplicar_transacao(consolidado, linha, chave)
    return consolidado, ids_lote


def _aplicar_linhas_recebivel(
    consolidado: list[dict], linhas: list[dict]
) -> tuple[list[dict], set[str]]:
    ids_lote: set[str] = set()
    for linha in linhas:
        chave = _id_estavel(linha.get(ID_ADQUIRENTE))
        if not chave:
            continue
        ids_lote.add(chave)
        consolidado = _aplicar_recebivel(consolidado, linha, chave)
    return consolidado, ids_lote


def _liberar_maquinha(
    consolidado: list[dict],
    maquinha: set[str],
    pendentes: set[tuple],
    ids_lote: set[str],
) -> tuple[list[dict], set[str], set[tuple]]:
    saindo = maquinha & ids_lote
    if not saindo:
        return consolidado, maquinha, pendentes
    maquinha -= saindo
    tuplas = [t for t in pendentes if t[0] in saindo]
    pendentes -= set(tuplas)
    consolidado = _aplicar_tuplas_ordenadas(consolidado, tuplas)
    return consolidado, maquinha, pendentes


def _aplicar_confirmacoes_mp(
    consolidado: list[dict],
    maquinha: set[str],
    pendentes: set[tuple],
    linhas: list[dict],
) -> tuple[list[dict], set[str], set[tuple]]:
    extraidas = _tuplas_validas(linhas)
    aplicadas = _tuplas_aplicadas(consolidado) | pendentes
    novas: list[tuple] = []
    for tupla, _ in extraidas:
        if tupla in aplicadas or tupla in novas:
            continue
        novas.append(tupla)
    novas.sort(key=lambda t: (t[1] < 0, t[2]))
    for tupla in novas:
        chave = tupla[0]
        if _id_no_consolidado(consolidado, chave):
            consolidado = _aplicar_uma_tupla(consolidado, tupla)
        else:
            maquinha.add(chave)
            pendentes.add(tupla)
    return consolidado, maquinha, pendentes


def _aplicar_tuplas_ordenadas(consolidado: list[dict], tuplas: list[tuple]) -> list[dict]:
    ordenadas = sorted(tuplas, key=lambda t: (t[1] < 0, t[2]))
    for tupla in ordenadas:
        consolidado = _aplicar_uma_tupla(consolidado, tupla)
    return consolidado


def _aplicar_uma_tupla(consolidado: list[dict], tupla: tuple) -> list[dict]:
    chave, valor, data_recibo = tupla
    if valor > 0:
        _aplicar_positivo(consolidado, chave, valor, data_recibo)
    else:
        consolidado.append(_linha_estorno(consolidado, chave, valor, data_recibo))
    return consolidado


def _tuplas_aplicadas(consolidado: list[dict]) -> set[tuple]:
    vistas: set[tuple] = set()
    for row in consolidado:
        chave = row.get(ID_ADQUIRENTE) or ""
        valor = row.get(COL_CONFIRMACAO)
        data_recibo = row.get(COL_DATA_RECIBO)
        if chave and valor not in ("", None) and isinstance(data_recibo, date):
            vistas.add((chave, valor, data_recibo))
    return vistas


def _id_no_consolidado(consolidado: list[dict], chave: str) -> bool:
    return any(row.get(ID_ADQUIRENTE) == chave for row in consolidado)


def _aplicar_transacao(consolidado: list[dict], csv_row: dict, chave: str) -> list[dict]:
    mapped = _mapear_transacao(csv_row, chave)
    existentes = [i for i, row in enumerate(consolidado) if row.get(ID_ADQUIRENTE) == chave]
    if not existentes:
        consolidado.append(_esqueleto(mapped))
        return consolidado
    for i in existentes:
        consolidado[i] = {**consolidado[i], **mapped}
    return consolidado


def _esqueleto(transacao: dict) -> dict:
    row = dict(transacao)
    for col in COLUNAS_RECEBIVEL:
        row[col] = ""
    return _com_confirmacao_mp_vazia(row)


def _linha_so_recebivel(chave: str, recebivel: dict) -> dict:
    row = {col: "" for col in COLUNAS_TRANSACAO}
    row[ID_ADQUIRENTE] = chave
    row.update(recebivel)
    return _com_confirmacao_mp_vazia(row)


def _com_confirmacao_mp_vazia(row: dict) -> dict:
    for col in COLUNAS_CONFIRMACAO_MP:
        row[col] = ""
    return row


def _sem_recebivel(row: dict) -> bool:
    return (row.get("Parcela Recebivel") or "") == "" and (
        row.get("Valor Repasse") or ""
    ) == ""


def _e_estorno(row: dict) -> bool:
    conf = row.get(COL_CONFIRMACAO)
    return isinstance(conf, (int, float)) and not isinstance(conf, bool) and conf < 0


def _vaga_recebivel(row: dict) -> bool:
    return _sem_recebivel(row) and not _e_estorno(row)


def _aplicar_recebivel(consolidado: list[dict], csv_row: dict, chave: str) -> list[dict]:
    mapped = _mapear_recebivel(csv_row)
    parcela = mapped["Parcela Recebivel"]
    existentes = [i for i, row in enumerate(consolidado) if row.get(ID_ADQUIRENTE) == chave]
    if not existentes:
        consolidado.append(_linha_so_recebivel(chave, mapped))
        return consolidado
    if parcela:
        mesma = [
            i
            for i in existentes
            if (consolidado[i].get("Parcela Recebivel") or "") == parcela
        ]
        if mesma:
            i = mesma[0]
            consolidado[i] = {**consolidado[i], **mapped}
            return consolidado
    vagas = [i for i in existentes if _vaga_recebivel(consolidado[i])]
    if vagas:
        i = vagas[0]
        consolidado[i] = {**consolidado[i], **mapped}
        return consolidado
    base = consolidado[existentes[0]]
    nova = {col: base.get(col, "") for col in COLUNAS_TRANSACAO}
    nova[ID_ADQUIRENTE] = chave
    nova.update(mapped)
    consolidado.append(_com_confirmacao_mp_vazia(nova))
    return consolidado


def _mapear_recebivel(csv_row: dict) -> dict:
    return {
        "Parcela Recebivel": csv_row.get("Parcela Recebivel") or "",
        "Total Parcelas": csv_row.get("Total Parcelas") or "",
        "taxa % cliente": csv_row.get("Taxa %") or "",
        "taxa valor cliente": csv_row.get("Taxa Valor") or "",
        "Valor Repasse": csv_row.get("Valor Repasse") or "",
        "Data Repasse": _parse_data(csv_row.get("Data Repasse") or ""),
    }


def _parse_data(valor: str) -> date | str:
    texto = valor.strip() if isinstance(valor, str) else str(valor or "").strip()
    if not texto:
        return ""
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return ""


def _mapear_transacao(csv_row: dict, chave: str) -> dict:
    data_val, hora_val = _partir_data_hora(csv_row.get("Data/Hora") or "")
    return {
        "ID Transacao": csv_row.get("ID Transacao") or "",
        "Cliente": csv_row.get("Cliente") or "",
        "data": data_val,
        "hora": hora_val,
        "Adquirente": csv_row.get("Adquirente") or "",
        ID_ADQUIRENTE: chave,
        "Status": csv_row.get("Status") or "",
        "Valor Transacao": csv_row.get("Valor Transacao") or "",
        "Tipo": csv_row.get("Tipo") or "",
        "Parcelas": csv_row.get("Parcelas") or "",
        "Bandeira": csv_row.get("Bandeira") or "",
        "Aut": csv_row.get("Aut") or "",
        "Cartao": csv_row.get("Cartao") or "",
        "Taxa %": csv_row.get("Taxa %") or "",
        "Taxa Valor": csv_row.get("Taxa Valor") or "",
        "Valor Liquido": csv_row.get("Valor Liquido") or "",
        "Total Reembolsado": csv_row.get("Total Reembolsado") or "",
    }


def _partir_data_hora(valor: str) -> tuple[date | str, time | str]:
    texto = " ".join(str(valor).split())
    if not texto:
        return "", ""
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            dt = datetime.strptime(texto, fmt)
            return dt.date(), dt.time().replace(microsecond=0)
        except ValueError:
            continue
    return "", ""


def _sem_confirmacao(row: dict) -> bool:
    return row.get(COL_CONFIRMACAO) in ("", None)


def _chave_data(valor: Any) -> tuple:
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        return (0, valor)
    return (1, date.max)


def _aplicar_positivo(
    consolidado: list[dict], chave: str, valor: int | float, data_recibo: date
) -> None:
    vagas = [
        (i, row)
        for i, row in enumerate(consolidado)
        if row.get(ID_ADQUIRENTE) == chave and _sem_confirmacao(row)
    ]
    if not vagas:
        consolidado.append(_esqueleto_mp(chave, valor, data_recibo))
        return
    vagas.sort(key=lambda item: (_chave_data(item[1].get("Data Repasse")), item[0]))
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
