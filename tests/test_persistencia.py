from datetime import date, time
from pathlib import Path

from consolidacao_base_1.motor import apply_lote
from consolidacao_base_1.persistencia import carregar_consolidado, gravar_output
from tests.test_motor import _transacao, _recebivel


def test_xlsx_grava_data_e_hora_nativas(tmp_path: Path):
    caminho = tmp_path / "output.xlsx"
    consolidado = apply_lote([], {"tipo": "transacao", "linhas": [_transacao()]})
    consolidado = apply_lote(
        consolidado,
        {
            "tipo": "recebivel",
            "linhas": [_recebivel(**{"ID Trans. Adquirente": "176784155259"})],
        },
    )
    gravar_output(caminho, consolidado, hostname_permitido="DaniGalera")
    relido, controle = carregar_consolidado(caminho)

    assert relido[0]["data"] == date(2026, 9, 7)
    assert relido[0]["hora"] == time(11, 59, 50)
    assert relido[0]["Data Repasse"] == date(2026, 4, 2)
    assert isinstance(relido[0]["data"], date)
    assert isinstance(relido[0]["hora"], time)
    assert isinstance(relido[0]["Data Repasse"], date)
    assert relido[0]["ID Trans. Adquirente"] == "176784155259"
    assert relido[0]["Valor Transacao"] == "80,00"
    assert controle["hostname_permitido"] == "DaniGalera"
