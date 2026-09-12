from __future__ import annotations

import json
from datetime import date

CHAVE_TUPLAS_MP = "tuplas_mp"
_PREFIXO_SHARD = CHAVE_TUPLAS_MP + "_"
_LIMITE_CELULA = 32000


def tem_cursor(controle: dict | None) -> bool:
    if not controle:
        return False
    return CHAVE_TUPLAS_MP in controle or any(
        str(chave).startswith(_PREFIXO_SHARD) for chave in controle
    )


def controle_com_vistas(vistas: set, controle: dict | None = None) -> dict:
    dados = {
        chave: valor
        for chave, valor in dict(controle or {}).items()
        if chave != CHAVE_TUPLAS_MP and not str(chave).startswith(_PREFIXO_SHARD)
    }
    bruto = _serializar_vistas(vistas)
    if not bruto:
        dados[_PREFIXO_SHARD + "0"] = "[]"
        return dados
    for i in range(0, len(bruto), _LIMITE_CELULA):
        dados[_PREFIXO_SHARD + str(i // _LIMITE_CELULA)] = bruto[i : i + _LIMITE_CELULA]
    return dados


def vistas_de_controle(controle: dict | None) -> set:
    if not controle:
        return set()
    if CHAVE_TUPLAS_MP in controle:
        return _desserializar_vistas(controle.get(CHAVE_TUPLAS_MP))
    partes = []
    indice = 0
    while _PREFIXO_SHARD + str(indice) in controle:
        partes.append(str(controle[_PREFIXO_SHARD + str(indice)] or ""))
        indice += 1
    if not partes:
        return set()
    return _desserializar_vistas("".join(partes))


def _serializar_vistas(vistas: set) -> str:
    items = []
    for id_, valor, data_recibo in vistas:
        items.append([id_, valor, data_recibo.isoformat()])
    items.sort(key=lambda item: (item[0], str(item[1]), item[2]))
    return json.dumps(items, ensure_ascii=False)


def _desserializar_vistas(valor) -> set:
    if not valor:
        return set()
    if isinstance(valor, str):
        items = json.loads(valor)
    elif isinstance(valor, list):
        items = valor
    else:
        return set()
    out = set()
    for item in items:
        if not item or len(item) < 3:
            continue
        id_, valor_mp, data_txt = item[0], item[1], item[2]
        if isinstance(data_txt, date):
            data_recibo = data_txt
        else:
            data_recibo = date.fromisoformat(str(data_txt))
        if isinstance(valor_mp, float) and valor_mp.is_integer():
            valor_mp = int(valor_mp)
        out.add((str(id_), valor_mp, data_recibo))
    return out
