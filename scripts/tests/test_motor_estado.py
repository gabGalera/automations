from datetime import date, datetime, time

from consolidacao.motor import Estado, apply_lote


def _estado_vazio():
    return Estado(consolidado=[], maquinha=set(), pendentes=set())


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


def _mp(**overrides):
    row = {
        "ID Trans. Adquirente": "176784155259",
        "Confirmacao MP": 79.6,
        "Data Recibo MP": date(2026, 4, 2),
    }
    row.update(overrides)
    return row


def test_id_vazio_descartado_nas_tres_pontas():
    vazio = _estado_vazio()
    assert apply_lote(
        vazio, {"tipo": "transacao", "linhas": [_transacao(**{"ID Trans. Adquirente": "   "})]}
    ).consolidado == []
    assert apply_lote(
        vazio, {"tipo": "recebivel", "linhas": [_recebivel(**{"ID Trans. Adquirente": ""})]}
    ).consolidado == []
    estado = apply_lote(
        vazio,
        {
            "tipo": "confirmacao_mp",
            "linhas": [_mp(**{"ID Trans. Adquirente": "   "})],
        },
    )
    assert estado.consolidado == []
    assert estado.maquinha == set()
    assert estado.pendentes == set()


def test_id_numerico_vira_texto_estavel_sem_notacao_cientifica():
    estado = apply_lote(
        _estado_vazio(),
        {
            "tipo": "confirmacao_mp",
            "linhas": [_mp(**{"ID Trans. Adquirente": 1.76784155259e11})],
        },
    )
    assert "176784155259" in estado.maquinha
    assert ("176784155259", 79.6, date(2026, 4, 2)) in estado.pendentes


def test_transacao_nova_vira_esqueleto_sem_ultima_atualizacao_e_mp_vazio():
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    assert len(estado.consolidado) == 1
    linha = estado.consolidado[0]
    assert "Ultima Atualizacao" not in linha
    assert "Data/Hora" not in linha
    assert linha["data"] == date(2026, 9, 7)
    assert linha["hora"] == time(11, 59, 50)
    assert linha["ID Trans. Adquirente"] == "176784155259"
    assert linha["Confirmacao MP"] == ""
    assert linha["Data Recibo MP"] == ""
    assert linha["Parcela Recebivel"] == ""


def test_status_estornado_e_taxa_negativa_nao_criam_estorno():
    estado = apply_lote(
        _estado_vazio(),
        {
            "tipo": "transacao",
            "linhas": [
                _transacao(**{"Status": "Estornado", "Taxa Valor": "-0,16"}),
            ],
        },
    )
    assert len(estado.consolidado) == 1
    linha = estado.consolidado[0]
    assert linha["Status"] == "Estornado"
    assert linha["Taxa Valor"] == "-0,16"
    assert linha["Confirmacao MP"] == ""
    assert linha["Parcela Recebivel"] == ""


def test_recebivel_antes_da_transacao_fica_uma_linha_so():
    id_ = "04949dde-2b80-4095-9cc7-c8e605756544"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "recebivel", "linhas": [_recebivel()]}
    )
    assert estado.consolidado[0]["Cliente"] == ""
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    estado = apply_lote(
        estado,
        {
            "tipo": "transacao",
            "linhas": [_transacao(**{"ID Trans. Adquirente": id_, "Cliente": "MB OPERADORA"})],
        },
    )
    assert len(estado.consolidado) == 1
    assert estado.consolidado[0]["Cliente"] == "MB OPERADORA"
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[0]["Confirmacao MP"] == ""


def test_segunda_transacao_substitui_so_colunas_de_transacao():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"})],
        },
    )
    estado.consolidado[0]["Confirmacao MP"] = 80.0
    estado.consolidado[0]["Data Recibo MP"] = date(2026, 4, 2)
    estado = apply_lote(
        estado,
        {
            "tipo": "transacao",
            "linhas": [_transacao(**{"Cliente": "NOVO CLIENTE"})],
        },
    )
    assert len(estado.consolidado) == 1
    assert estado.consolidado[0]["Cliente"] == "NOVO CLIENTE"
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[0]["Confirmacao MP"] == 80.0
    assert estado.consolidado[0]["Data Recibo MP"] == date(2026, 4, 2)


def test_segunda_transacao_substitui_colunas_em_todas_as_linhas_do_id():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"}),
                _recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "2"}),
            ],
        },
    )
    estado.consolidado[0]["Confirmacao MP"] = 80.0
    estado.consolidado[0]["Data Recibo MP"] = date(2026, 4, 2)
    estado.consolidado[1]["Confirmacao MP"] = -10
    estado.consolidado[1]["Data Recibo MP"] = date(2026, 4, 8)
    estado = apply_lote(
        estado,
        {
            "tipo": "transacao",
            "linhas": [_transacao(**{"Cliente": "TODAS"})],
        },
    )
    assert len(estado.consolidado) == 2
    assert [linha["Cliente"] for linha in estado.consolidado] == ["TODAS", "TODAS"]
    assert [linha["Parcela Recebivel"] for linha in estado.consolidado] == ["1", "2"]
    assert estado.consolidado[0]["Confirmacao MP"] == 80.0
    assert estado.consolidado[1]["Confirmacao MP"] == -10
    assert estado.consolidado[1]["Data Recibo MP"] == date(2026, 4, 8)


def test_parcela_nova_preenche_vaga_sem_recebivel_que_nao_seja_estorno():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "confirmacao_mp",
            "linhas": [_mp(**{"Confirmacao MP": -80})],
        },
    )
    assert len(estado.consolidado) == 2
    assert estado.consolidado[1]["Confirmacao MP"] == -80
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"})],
        },
    )
    assert len(estado.consolidado) == 2
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[1]["Parcela Recebivel"] == ""
    assert estado.consolidado[1]["Confirmacao MP"] == -80


def test_parcela_preenche_confirmacao_positiva_nua_e_preserva_mp():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado, {"tipo": "confirmacao_mp", "linhas": [_mp(**{"Confirmacao MP": 80})]}
    )
    assert estado.consolidado[0]["Parcela Recebivel"] == ""
    assert estado.consolidado[0]["Confirmacao MP"] == 80
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"})],
        },
    )
    assert len(estado.consolidado) == 1
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[0]["Valor Repasse"] == "17.504,70"
    assert estado.consolidado[0]["Confirmacao MP"] == 80
    assert estado.consolidado[0]["Data Recibo MP"] == date(2026, 4, 2)
    assert estado.consolidado[0]["Cliente"] == "TAXIBUS TRANSPORTES"


def test_sem_vaga_parcela_entra_linha_nova():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"}),
                _recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "2"}),
            ],
        },
    )
    assert len(estado.consolidado) == 2
    assert [r["Parcela Recebivel"] for r in estado.consolidado] == ["1", "2"]
    assert all(r["Cliente"] == "TAXIBUS TRANSPORTES" for r in estado.consolidado)


def test_mesma_parcela_substitui_recebivel_e_preserva_confirmacao_mp():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(
                    **{
                        "ID Trans. Adquirente": id_,
                        "Parcela Recebivel": "1",
                        "Valor Repasse": "17.504,70",
                    }
                )
            ],
        },
    )
    estado = apply_lote(
        estado, {"tipo": "confirmacao_mp", "linhas": [_mp(**{"Confirmacao MP": 80})]}
    )
    assert estado.consolidado[0]["Confirmacao MP"] == 80
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(
                    **{
                        "ID Trans. Adquirente": id_,
                        "Parcela Recebivel": "1",
                        "Valor Repasse": "18.000,00",
                        "Taxa Valor": "-1.000,00",
                    }
                )
            ],
        },
    )
    assert len(estado.consolidado) == 1
    assert estado.consolidado[0]["Valor Repasse"] == "18.000,00"
    assert estado.consolidado[0]["taxa valor cliente"] == "-1.000,00"
    assert estado.consolidado[0]["Confirmacao MP"] == 80
    assert estado.consolidado[0]["Data Recibo MP"] == date(2026, 4, 2)


def test_estorno_nasce_sem_parcela_copia_transacao_e_parcela_vai_outra_linha():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado, {"tipo": "confirmacao_mp", "linhas": [_mp(**{"Confirmacao MP": -25660.54})]}
    )
    assert len(estado.consolidado) == 2
    estorno = estado.consolidado[1]
    assert estorno["Confirmacao MP"] == -25660.54
    assert estorno["Parcela Recebivel"] == ""
    assert estorno["Cliente"] == "TAXIBUS TRANSPORTES"
    assert estorno["ID Transacao"] == "3128"
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"})],
        },
    )
    assert len(estado.consolidado) == 2
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[1]["Parcela Recebivel"] == ""
    assert estado.consolidado[1]["Confirmacao MP"] == -25660.54


def test_confirmacao_positiva_por_data_repasse_mesma_tupla_nao_reaplica_outra_data_aplica():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(
                    **{
                        "ID Trans. Adquirente": id_,
                        "Parcela Recebivel": "1",
                        "Data Repasse": "10/04/2026",
                    }
                ),
                _recebivel(
                    **{
                        "ID Trans. Adquirente": id_,
                        "Parcela Recebivel": "2",
                        "Data Repasse": "02/04/2026",
                    }
                ),
            ],
        },
    )
    estado = apply_lote(
        estado, {"tipo": "confirmacao_mp", "linhas": [_mp(**{"Confirmacao MP": 80})]}
    )
    assert estado.consolidado[0]["Confirmacao MP"] == ""
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[1]["Confirmacao MP"] == 80
    assert estado.consolidado[1]["Parcela Recebivel"] == "2"

    estado = apply_lote(
        estado, {"tipo": "confirmacao_mp", "linhas": [_mp(**{"Confirmacao MP": 80})]}
    )
    assert sum(1 for r in estado.consolidado if r["Confirmacao MP"] == 80) == 1

    estado = apply_lote(
        estado,
        {
            "tipo": "confirmacao_mp",
            "linhas": [
                _mp(**{"Confirmacao MP": 80, "Data Recibo MP": date(2026, 4, 8)})
            ],
        },
    )
    assert estado.consolidado[0]["Confirmacao MP"] == 80
    assert estado.consolidado[0]["Data Recibo MP"] == date(2026, 4, 8)
    assert estado.consolidado[1]["Confirmacao MP"] == 80
    assert estado.consolidado[1]["Data Recibo MP"] == date(2026, 4, 2)


def test_lote_positivos_antes_de_negativos_por_data_recibo():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "confirmacao_mp",
            "linhas": [
                _mp(**{"Confirmacao MP": -80, "Data Recibo MP": date(2026, 4, 1)}),
                _mp(**{"Confirmacao MP": 90, "Data Recibo MP": date(2026, 4, 8)}),
                _mp(**{"Confirmacao MP": 80, "Data Recibo MP": date(2026, 4, 2)}),
                _mp(**{"Confirmacao MP": 70, "Data Recibo MP": date(2026, 4, 2)}),
            ],
        },
    )
    assert [linha["Confirmacao MP"] for linha in estado.consolidado] == [
        80,
        70,
        90,
        -80,
    ]


def test_id_sem_transacao_nem_recebivel_vai_para_maquinha_e_tupla_fica_pendente():
    estado = apply_lote(
        _estado_vazio(),
        {
            "tipo": "confirmacao_mp",
            "linhas": [_mp(**{"ID Trans. Adquirente": "orfao-1", "Confirmacao MP": 80})],
        },
    )
    assert estado.consolidado == []
    assert estado.maquinha == {"orfao-1"}
    assert estado.pendentes == {("orfao-1", 80, date(2026, 4, 2))}


def test_chegada_de_transacao_tira_da_maquinha_e_aplica_pendentes_depois():
    estado = apply_lote(
        _estado_vazio(),
        {
            "tipo": "confirmacao_mp",
            "linhas": [
                _mp(
                    **{
                        "ID Trans. Adquirente": "176784155259",
                        "Confirmacao MP": -80,
                        "Data Recibo MP": date(2026, 4, 1),
                    }
                ),
                _mp(
                    **{
                        "ID Trans. Adquirente": "176784155259",
                        "Confirmacao MP": 79.6,
                        "Data Recibo MP": date(2026, 4, 2),
                    }
                ),
            ],
        },
    )
    assert estado.maquinha == {"176784155259"}
    assert len(estado.pendentes) == 2
    assert estado.consolidado == []

    estado = apply_lote(
        estado, {"tipo": "transacao", "linhas": [_transacao()]}
    )
    assert "176784155259" not in estado.maquinha
    assert estado.pendentes == set()
    assert len(estado.consolidado) == 2
    assert estado.consolidado[0]["Confirmacao MP"] == 79.6
    assert estado.consolidado[0]["Cliente"] == "TAXIBUS TRANSPORTES"
    assert estado.consolidado[1]["Confirmacao MP"] == -80
    assert estado.consolidado[1]["Parcela Recebivel"] == ""


def test_chegada_de_recebivel_tira_da_maquinha_e_aplica_pendentes_depois():
    id_ = "04949dde-2b80-4095-9cc7-c8e605756544"
    estado = apply_lote(
        _estado_vazio(),
        {
            "tipo": "confirmacao_mp",
            "linhas": [
                _mp(
                    **{
                        "ID Trans. Adquirente": id_,
                        "Confirmacao MP": 100,
                        "Data Recibo MP": date(2026, 4, 2),
                    }
                )
            ],
        },
    )
    assert estado.maquinha == {id_}
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_})],
        },
    )
    assert id_ not in estado.maquinha
    assert estado.pendentes == set()
    assert len(estado.consolidado) == 1
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[0]["Confirmacao MP"] == 100
    assert estado.consolidado[0]["Data Repasse"] == date(2026, 4, 2)


def test_tres_chamadas_em_sequencia_produzem_estado_final_da_largada():
    id_ = "176784155259"
    estado = apply_lote(
        _estado_vazio(), {"tipo": "transacao", "linhas": [_transacao()]}
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(
                    **{
                        "ID Trans. Adquirente": id_,
                        "Parcela Recebivel": "1",
                        "Data Repasse": "02/04/2026",
                    }
                )
            ],
        },
    )
    estado = apply_lote(
        estado,
        {
            "tipo": "confirmacao_mp",
            "linhas": [
                _mp(**{"Confirmacao MP": 79.6, "Data Recibo MP": date(2026, 4, 2)}),
                _mp(
                    **{
                        "ID Trans. Adquirente": "so-mp",
                        "Confirmacao MP": 50,
                        "Data Recibo MP": date(2026, 5, 1),
                    }
                ),
            ],
        },
    )
    assert len(estado.consolidado) == 1
    assert estado.consolidado[0]["Cliente"] == "TAXIBUS TRANSPORTES"
    assert estado.consolidado[0]["Parcela Recebivel"] == "1"
    assert estado.consolidado[0]["Confirmacao MP"] == 79.6
    assert estado.consolidado[0]["Data Recibo MP"] == date(2026, 4, 2)
    assert estado.maquinha == {"so-mp"}
    assert estado.pendentes == {("so-mp", 50, date(2026, 5, 1))}


def test_confirmacao_incompleta_nao_entra():
    estado = apply_lote(
        _estado_vazio(),
        {
            "tipo": "confirmacao_mp",
            "linhas": [
                _mp(**{"Confirmacao MP": 0}),
                _mp(**{"Confirmacao MP": ""}),
                _mp(**{"Data Recibo MP": "32-13-2026"}),
                _mp(**{"Data Recibo MP": datetime(2026, 4, 8, 15, 30)}),
            ],
        },
    )
    assert len(estado.consolidado) == 0
    assert estado.maquinha == {"176784155259"}
    assert estado.pendentes == {("176784155259", 79.6, date(2026, 4, 8))}
