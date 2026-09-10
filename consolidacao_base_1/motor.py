from datetime import date, datetime, time

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


def apply_lote(consolidado: list[dict], lote: dict) -> list[dict]:
    resultado = [dict(linha) for linha in consolidado]
    tipo = lote["tipo"]
    for linha in lote["linhas"]:
        chave = (linha.get(ID_ADQUIRENTE) or "").strip()
        if not chave:
            continue
        if tipo == "transacao":
            resultado = _aplicar_transacao(resultado, linha, chave)
        elif tipo == "recebivel":
            resultado = _aplicar_recebivel(resultado, linha, chave)
    return resultado


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
    return row


def _linha_so_recebivel(chave: str, recebivel: dict) -> dict:
    row = {col: "" for col in COLUNAS_TRANSACAO}
    row[ID_ADQUIRENTE] = chave
    row.update(recebivel)
    return row


def _e_esqueleto(row: dict) -> bool:
    return (row.get("Parcela Recebivel") or "") == "" and (
        row.get("Valor Repasse") or ""
    ) == ""


def _aplicar_recebivel(consolidado: list[dict], csv_row: dict, chave: str) -> list[dict]:
    mapped = _mapear_recebivel(csv_row)
    existentes = [i for i, row in enumerate(consolidado) if row.get(ID_ADQUIRENTE) == chave]
    if not existentes:
        consolidado.append(_linha_so_recebivel(chave, mapped))
        return consolidado
    esqueletos = [i for i in existentes if _e_esqueleto(consolidado[i])]
    if esqueletos:
        i = esqueletos[0]
        consolidado[i] = {**consolidado[i], **mapped}
        return consolidado
    base = consolidado[existentes[0]]
    nova = {col: base.get(col, "") for col in COLUNAS_TRANSACAO}
    nova[ID_ADQUIRENTE] = chave
    nova.update(mapped)
    consolidado.append(nova)
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
    texto = valor.strip()
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
    texto = " ".join(valor.split())
    if not texto:
        return "", ""
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            dt = datetime.strptime(texto, fmt)
            return dt.date(), dt.time().replace(microsecond=0)
        except ValueError:
            continue
    return "", ""
