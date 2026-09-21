from datetime import date, datetime

from consolidacao_base_1.motor import apply_lote
from consolidacao_base_2.motor import apply_confirmacoes_mp
from tests.test_motor import _recebivel, _transacao


def _mp(**overrides):
    row = {
        "ID Trans. Adquirente": "176784155259",
        "Confirmacao MP": 79.6,
        "Data Recibo MP": date(2026, 4, 2),
    }
    row.update(overrides)
    return row


def test_linha_incompleta_id_vazio_zero_ou_data_ilegivels_nao_vira_confirmacao_mp():
    consolidado, vistas = apply_confirmacoes_mp(
        [],
        [
            _mp(**{"Confirmacao MP": "", "Data Recibo MP": ""}),
            _mp(**{"ID Trans. Adquirente": "   "}),
            _mp(**{"ID Trans. Adquirente": ""}),
            _mp(**{"Confirmacao MP": 0}),
            _mp(**{"Confirmacao MP": "abc"}),
            _mp(**{"Confirmacao MP": None}),
            _mp(**{"Data Recibo MP": "32-13-2026"}),
            _mp(**{"Data Recibo MP": "2026-04-02"}),
            _mp(**{"Data Recibo MP": ""}),
        ],
        set(),
    )

    assert consolidado == []
    assert vistas == set()


def test_data_recibo_texto_dd_mm_yyyy_e_datetime_excel():
    consolidado, _ = apply_confirmacoes_mp(
        [],
        [
            _mp(
                **{
                    "ID Trans. Adquirente": "a",
                    "Confirmacao MP": 80,
                    "Data Recibo MP": "02-04-2026",
                }
            ),
            _mp(
                **{
                    "ID Trans. Adquirente": "b",
                    "Confirmacao MP": 81,
                    "Data Recibo MP": datetime(2026, 4, 8, 15, 30),
                }
            ),
        ],
        set(),
    )

    assert consolidado[0]["Data Recibo MP"] == date(2026, 4, 2)
    assert consolidado[1]["Data Recibo MP"] == date(2026, 4, 8)


def test_id_numerico_vira_texto_estavel():
    consolidado, vistas = apply_confirmacoes_mp(
        [],
        [_mp(**{"ID Trans. Adquirente": 1.76784155259e11})],
        set(),
    )

    assert consolidado[0]["ID Trans. Adquirente"] == "176784155259"
    assert ("176784155259", 79.6, date(2026, 4, 2)) in vistas


def test_semear_vistas_nao_altera_consolidado_e_apply_posterior_e_noop():
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    lote = [_mp()]
    antes = [dict(linha) for linha in consolidado]

    semeado, vistas = apply_confirmacoes_mp(consolidado, lote, set(), semear=True)

    assert semeado == antes
    assert vistas == {("176784155259", 79.6, date(2026, 4, 2))}
    assert consolidado == antes

    depois, vistas2 = apply_confirmacoes_mp(semeado, lote, vistas)

    assert depois == antes
    assert vistas2 == vistas


def test_positivo_preenche_primeira_vaga_por_data_repasse_entao_data():
    id_ = "176784155259"
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado = apply_lote(
        consolidado,
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
    consolidado[0]["data"] = date(2026, 1, 1)
    consolidado[1]["data"] = date(2026, 9, 7)

    consolidado, vistas = apply_confirmacoes_mp(
        consolidado,
        [_mp(**{"Confirmacao MP": 80})],
        set(),
    )

    assert len(consolidado) == 2
    assert consolidado[0]["Confirmacao MP"] == ""
    assert consolidado[0]["Parcela Recebivel"] == "1"
    assert consolidado[1]["Confirmacao MP"] == 80
    assert consolidado[1]["Data Recibo MP"] == date(2026, 4, 2)
    assert consolidado[1]["Parcela Recebivel"] == "2"
    assert vistas == {("176784155259", 80, date(2026, 4, 2))}


def test_vaga_sem_datas_fica_por_ultimo_e_data_desempata():
    id_ = "176784155259"
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "recebivel",
            "linhas": [
                _recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "1"}),
                _recebivel(**{"ID Trans. Adquirente": id_, "Parcela Recebivel": "2"}),
            ],
        },
    )
    consolidado[0]["Data Repasse"] = ""
    consolidado[0]["data"] = ""
    consolidado[1]["Data Repasse"] = date(2026, 4, 2)
    consolidado[1]["data"] = date(2026, 9, 7)

    consolidado, _ = apply_confirmacoes_mp(consolidado, [_mp(**{"Confirmacao MP": 80})], set())

    assert consolidado[0]["Confirmacao MP"] == ""
    assert consolidado[1]["Confirmacao MP"] == 80

    consolidado[0]["Data Repasse"] = date(2026, 4, 2)
    consolidado[0]["data"] = date(2026, 3, 1)
    consolidado[1]["Confirmacao MP"] = ""
    consolidado[1]["Data Recibo MP"] = ""
    consolidado[1]["data"] = date(2026, 9, 7)

    consolidado, _ = apply_confirmacoes_mp(
        consolidado,
        [_mp(**{"Confirmacao MP": 81, "Data Recibo MP": date(2026, 4, 8)})],
        set(),
    )

    assert consolidado[0]["Confirmacao MP"] == 81
    assert consolidado[1]["Confirmacao MP"] == ""


def test_positivo_sem_vaga_vira_esqueleto():
    id_ = "176784155259"
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_})],
        },
    )
    consolidado[0]["Confirmacao MP"] = 50
    consolidado[0]["Data Recibo MP"] = date(2026, 3, 1)

    consolidado, _ = apply_confirmacoes_mp(
        consolidado,
        [_mp(**{"Confirmacao MP": 80})],
        set(),
    )

    assert len(consolidado) == 2
    assert consolidado[0]["Parcela Recebivel"] == "1"
    assert consolidado[0]["Confirmacao MP"] == 50
    esqueleto = consolidado[1]
    assert esqueleto["ID Trans. Adquirente"] == id_
    assert esqueleto["Confirmacao MP"] == 80
    assert esqueleto["Data Recibo MP"] == date(2026, 4, 2)
    assert esqueleto["Cliente"] == ""
    assert esqueleto["Parcela Recebivel"] == ""
    assert esqueleto["Valor Repasse"] == ""


def test_positivo_orfao_nasce_so_com_id_e_mp():
    consolidado, _ = apply_confirmacoes_mp(
        [],
        [_mp(**{"Confirmacao MP": 80, "ID Trans. Adquirente": "orfao-1"})],
        set(),
    )

    assert len(consolidado) == 1
    linha = consolidado[0]
    assert linha["ID Trans. Adquirente"] == "orfao-1"
    assert linha["Confirmacao MP"] == 80
    assert linha["Data Recibo MP"] == date(2026, 4, 2)
    assert linha["Cliente"] == ""
    assert linha["data"] == ""
    assert linha["Parcela Recebivel"] == ""


def test_negativo_appenda_copia_transacao_e_nao_sobrescreve_parcela():
    id_ = "176784155259"
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": id_})],
        },
    )

    consolidado, _ = apply_confirmacoes_mp(
        consolidado,
        [_mp(**{"Confirmacao MP": -80})],
        set(),
    )

    assert len(consolidado) == 2
    assert consolidado[0]["Parcela Recebivel"] == "1"
    assert consolidado[0]["Confirmacao MP"] == ""
    estorno = consolidado[1]
    assert estorno["Confirmacao MP"] == -80
    assert estorno["Data Recibo MP"] == date(2026, 4, 2)
    assert estorno["Cliente"] == "TAXIBUS TRANSPORTES"
    assert estorno["ID Transacao"] == "3128"
    assert estorno["data"] == date(2026, 9, 7)
    assert estorno["Parcela Recebivel"] == ""
    assert estorno["Valor Repasse"] == ""
    assert estorno["Data Repasse"] == ""


def test_negativo_orfao_nasce_so_com_id_e_mp():
    consolidado, _ = apply_confirmacoes_mp(
        [],
        [_mp(**{"Confirmacao MP": -80, "ID Trans. Adquirente": "orfao-neg"})],
        set(),
    )

    assert len(consolidado) == 1
    linha = consolidado[0]
    assert linha["ID Trans. Adquirente"] == "orfao-neg"
    assert linha["Confirmacao MP"] == -80
    assert linha["Cliente"] == ""
    assert linha["Parcela Recebivel"] == ""


def test_lote_positivos_antes_de_negativos_por_data_recibo():
    lote = [
        _mp(**{"Confirmacao MP": -80, "Data Recibo MP": date(2026, 4, 1)}),
        _mp(**{"Confirmacao MP": 90, "Data Recibo MP": date(2026, 4, 8)}),
        _mp(**{"Confirmacao MP": 80, "Data Recibo MP": date(2026, 4, 2)}),
        _mp(**{"Confirmacao MP": 70, "Data Recibo MP": date(2026, 4, 2)}),
    ]

    consolidado, _ = apply_confirmacoes_mp([], lote, set())

    assert [linha["Confirmacao MP"] for linha in consolidado] == [80, 70, 90, -80]


def test_tupla_identica_nao_aplica_de_novo():
    lote = [_mp(**{"Confirmacao MP": 80}), _mp(**{"Confirmacao MP": 80})]
    consolidado, vistas = apply_confirmacoes_mp([], lote, set())

    assert len(consolidado) == 1
    assert consolidado[0]["Confirmacao MP"] == 80

    consolidado, vistas2 = apply_confirmacoes_mp(consolidado, lote, vistas)

    assert len(consolidado) == 1
    assert vistas2 == vistas


def test_completar_as_tres_colunas_depois_conta_como_tupla_nova():
    consolidado, vistas = apply_confirmacoes_mp(
        [],
        [_mp(**{"Confirmacao MP": ""})],
        set(),
    )
    assert consolidado == []
    assert vistas == set()

    consolidado, vistas = apply_confirmacoes_mp(
        consolidado,
        [_mp(**{"Confirmacao MP": 80})],
        vistas,
    )

    assert len(consolidado) == 1
    assert consolidado[0]["Confirmacao MP"] == 80
    assert vistas == {("176784155259", 80, date(2026, 4, 2))}
