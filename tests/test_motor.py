from datetime import date, time

from consolidacao_base_1.motor import apply_lote


def test_transacao_sem_id_adquirente_e_descartada():
    lote = {
        "tipo": "transacao",
        "linhas": [
            {
                "ID Transacao": "3128",
                "Cliente": "TAXIBUS TRANSPORTES",
                "Data/Hora": "07/09/2026 11:59:50",
                "Adquirente": "MERCADO_PAGO",
                "ID Trans. Adquirente": "   ",
                "Status": "Pago",
                "Valor Transacao": "80,00",
                "Tipo": "PIX",
                "Parcelas": "1",
                "Bandeira": "",
                "Aut": "",
                "Cartao": "",
                "Taxa %": "",
                "Taxa Valor": "-0,16",
                "Valor Liquido": "79,84",
                "Total Reembolsado": "",
                "Ultima Atualizacao": "07/09/2026 13:00:03",
            }
        ],
    }

    resultado = apply_lote([], lote)

    assert resultado == []


def _transacao(**overrides):
    row = {
        "ID Transacao": "3128",
        "Cliente": "TAXIBUS TRANSPORTES",
        "Data/Hora": "07/09/2026 11:59:50",
        "Adquirente": "MERCADO_PAGO",
        "ID Trans. Adquirente": "176784155259",
        "Status": "Pago",
        "Valor Transacao": "80,00",
        "Tipo": "PIX",
        "Parcelas": "1",
        "Bandeira": "",
        "Aut": "",
        "Cartao": "",
        "Taxa %": "",
        "Taxa Valor": "-0,16",
        "Valor Liquido": "79,84",
        "Total Reembolsado": "",
        "Ultima Atualizacao": "07/09/2026 13:00:03",
    }
    row.update(overrides)
    return row


def test_transacao_nova_vira_esqueleto_sem_ultima_atualizacao():
    resultado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})

    assert len(resultado) == 1
    linha = resultado[0]
    assert "Ultima Atualizacao" not in linha
    assert "Data/Hora" not in linha
    assert linha["data"] == date(2026, 9, 7)
    assert linha["hora"] == time(11, 59, 50)
    assert linha["ID Trans. Adquirente"] == "176784155259"
    assert linha["Cliente"] == "TAXIBUS TRANSPORTES"
    assert linha["Parcela Recebivel"] == ""
    assert linha["taxa % cliente"] == ""
    assert linha["Data Repasse"] == ""
    assert linha["Confirmacao MP"] == ""
    assert linha["Data Recibo MP"] == ""


def _recebivel(**overrides):
    row = {
        "Cliente": "MB OPERADORA DE TURISMO",
        "ID Transacao": "25",
        "Adquirente": "barte",
        "ID Trans. Adquirente": "04949dde-2b80-4095-9cc7-c8e605756544",
        "Tipo": "Cartao de Credito",
        "Data Transacao": "01/04/2026",
        "Valor Transacao": "19.000,00",
        "Parcela Recebivel": "1",
        "Total Parcelas": "6",
        "Taxa %": "7,87",
        "Taxa Valor": "-1.495,30",
        "Valor Repasse": "17.504,70",
        "Data Repasse": "02/04/2026",
    }
    row.update(overrides)
    return row


def test_recebivel_sem_id_adquirente_e_descartado():
    resultado = apply_lote(
        [],
        {"tipo": "recebivel", "linhas": [_recebivel(**{"ID Trans. Adquirente": ""})]},
    )
    assert resultado == []


def test_recebivel_primeiro_entra_sem_colunas_de_transacao():
    resultado = apply_lote([], {"tipo": "recebivel", "linhas": [_recebivel()]})

    assert len(resultado) == 1
    linha = resultado[0]
    assert linha["ID Trans. Adquirente"] == "04949dde-2b80-4095-9cc7-c8e605756544"
    assert linha["Cliente"] == ""
    assert linha["Parcela Recebivel"] == "1"
    assert linha["Total Parcelas"] == "6"
    assert linha["taxa % cliente"] == "7,87"
    assert linha["taxa valor cliente"] == "-1.495,30"
    assert linha["Valor Repasse"] == "17.504,70"
    assert linha["Data Repasse"] == date(2026, 4, 2)
    assert linha.get("Taxa %") in ("", None)


def test_transacao_depois_preenche_recebivel_existente_e_substitui():
    id_ = "176784155259"
    consolidado = apply_lote(
        [],
        {"tipo": "recebivel", "linhas": [_recebivel(**{"ID Trans. Adquirente": id_})]},
    )
    consolidado = apply_lote(
        consolidado,
        {"tipo": "transacao", "linhas": [_transacao(**{"ID Trans. Adquirente": id_, "Cliente": "RUNNERS"})]},
    )

    assert len(consolidado) == 1
    assert consolidado[0]["Cliente"] == "RUNNERS"
    assert consolidado[0]["Parcela Recebivel"] == "1"
    assert consolidado[0]["data"] == date(2026, 9, 7)

    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "transacao",
            "linhas": [_transacao(**{"ID Trans. Adquirente": id_, "Cliente": "NOVO CLIENTE"})],
        },
    )
    assert len(consolidado) == 1
    assert consolidado[0]["Cliente"] == "NOVO CLIENTE"
    assert consolidado[0]["Parcela Recebivel"] == "1"


def test_recebivel_preenche_esqueleto_e_parcela_extra_vira_linha():
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(**{"ID Trans. Adquirente": "176784155259", "Parcela Recebivel": "1"}),
                _recebivel(**{"ID Trans. Adquirente": "176784155259", "Parcela Recebivel": "2"}),
            ],
        },
    )

    assert len(consolidado) == 2
    assert [r["Parcela Recebivel"] for r in consolidado] == ["1", "2"]
    assert all(r["Cliente"] == "TAXIBUS TRANSPORTES" for r in consolidado)


def test_recebivel_repetido_adiciona_linha():
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    rec = _recebivel(**{"ID Trans. Adquirente": "176784155259", "Parcela Recebivel": "1"})
    consolidado = apply_lote(consolidado, {"tipo": "recebivel", "linhas": [rec]})
    consolidado = apply_lote(consolidado, {"tipo": "recebivel", "linhas": [rec]})

    assert len(consolidado) == 2
    assert [r["Parcela Recebivel"] for r in consolidado] == ["1", "1"]


def test_data_hora_com_espacos_extras_ainda_parte():
    resultado = apply_lote(
        [],
        {
            "tipo": "transacao",
            "linhas": [_transacao(**{"Data/Hora": "07/09/2026  11:59:50"})],
        },
    )
    assert resultado[0]["data"] == date(2026, 9, 7)
    assert resultado[0]["hora"] == time(11, 59, 50)


def test_transacao_substitui_colunas_sem_apagar_confirmacao_mp():
    id_ = "176784155259"
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado[0]["Confirmacao MP"] = 80.0
    consolidado[0]["Data Recibo MP"] = date(2026, 4, 8)
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "transacao",
            "linhas": [_transacao(**{"ID Trans. Adquirente": id_, "Cliente": "NOVO"})],
        },
    )

    assert len(consolidado) == 1
    assert consolidado[0]["Cliente"] == "NOVO"
    assert consolidado[0]["Confirmacao MP"] == 80.0
    assert consolidado[0]["Data Recibo MP"] == date(2026, 4, 8)


def test_recebivel_preenche_estorno_sem_mexer_na_confirmacao_mp():
    id_ = "176784155259"
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"})],
        },
    )
    estorno = {
        **{k: consolidado[0][k] for k in consolidado[0]},
        "Parcela Recebivel": "",
        "Total Parcelas": "",
        "taxa % cliente": "",
        "taxa valor cliente": "",
        "Valor Repasse": "",
        "Data Repasse": "",
        "Confirmacao MP": -80.0,
        "Data Recibo MP": date(2026, 4, 8),
    }
    consolidado.append(estorno)
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "2"})],
        },
    )

    assert len(consolidado) == 2
    assert consolidado[0]["Parcela Recebivel"] == "1"
    assert consolidado[1]["Parcela Recebivel"] == "2"
    assert consolidado[1]["Confirmacao MP"] == -80.0
    assert consolidado[1]["Data Recibo MP"] == date(2026, 4, 8)
    assert consolidado[1]["Cliente"] == "TAXIBUS TRANSPORTES"


def test_recebivel_sem_vaga_entra_linha_nova_com_mp_vazio():
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    rec = _recebivel(**{"ID Trans. Adquirente": "176784155259", "Parcela Recebivel": "1"})
    consolidado = apply_lote(consolidado, {"tipo": "recebivel", "linhas": [rec]})
    consolidado[0]["Confirmacao MP"] = 79.6
    consolidado[0]["Data Recibo MP"] = date(2026, 4, 2)
    consolidado = apply_lote(consolidado, {"tipo": "recebivel", "linhas": [rec]})

    assert len(consolidado) == 2
    assert consolidado[0]["Confirmacao MP"] == 79.6
    assert consolidado[1]["Parcela Recebivel"] == "1"
    assert consolidado[1]["Confirmacao MP"] == ""
    assert consolidado[1]["Data Recibo MP"] == ""
    assert consolidado[1]["Cliente"] == "TAXIBUS TRANSPORTES"
