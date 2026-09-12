from datetime import date
from pathlib import Path

from consolidacao_base_1.motor import apply_lote
from consolidacao_base_1.persistencia import carregar_consolidado, gravar_output
from consolidacao_base_2.motor import apply_confirmacoes_mp
from consolidacao_base_2.persistencia import controle_com_vistas, vistas_de_controle
from tests.test_motor import _transacao
from tests.test_motor_mp import _mp


def test_xlsx_roundtrip_data_nativa_confirmacao_numero_e_id_texto(tmp_path: Path):
    consolidado, vistas = apply_confirmacoes_mp(
        [],
        [_mp(**{"Confirmacao MP": 80, "ID Trans. Adquirente": 176784155259})],
        set(),
    )
    caminho = tmp_path / "output.xlsx"
    gravar_output(
        caminho,
        consolidado,
        hostname_permitido="DaniGalera",
        controle=controle_com_vistas(vistas),
    )
    relido, controle = carregar_consolidado(caminho)

    assert relido[0]["ID Trans. Adquirente"] == "176784155259"
    assert relido[0]["Confirmacao MP"] == 80
    assert isinstance(relido[0]["Confirmacao MP"], (int, float))
    assert relido[0]["Data Recibo MP"] == date(2026, 4, 2)
    assert isinstance(relido[0]["Data Recibo MP"], date)
    assert vistas_de_controle(controle) == {("176784155259", 80, date(2026, 4, 2))}


def test_writer_csv_preserva_colunas_mp_e_tuplas_em_controle(tmp_path: Path):
    caminho = tmp_path / "output.xlsx"
    consolidado, vistas = apply_confirmacoes_mp(
        [],
        [_mp(**{"Confirmacao MP": -80})],
        set(),
    )
    gravar_output(
        caminho,
        consolidado,
        hostname_permitido="DaniGalera",
        controle=controle_com_vistas(vistas),
    )
    relido, controle = carregar_consolidado(caminho)
    consolidado = apply_lote(
        relido,
        {
            "tipo": "transacao",
            "linhas": [_transacao(**{"Cliente": "DEPOIS"})],
        },
    )
    gravar_output(
        caminho,
        consolidado,
        hostname_permitido="DaniGalera",
        controle=controle,
    )
    relido2, controle2 = carregar_consolidado(caminho)

    assert relido2[0]["Cliente"] == "DEPOIS"
    assert relido2[0]["Confirmacao MP"] == -80
    assert relido2[0]["Data Recibo MP"] == date(2026, 4, 2)
    assert vistas_de_controle(controle2) == {("176784155259", -80, date(2026, 4, 2))}
