from consolidacao_base_1.pasta import nomes_reentrantes


def test_reentrada_e_nome_que_nao_estava_no_conjunto_anterior():
    assert nomes_reentrantes({"a.csv"}, {"a.csv", "b.csv"}) == {"b.csv"}
    assert nomes_reentrantes({"a.csv", "b.csv"}, {"a.csv"}) == set()
    assert nomes_reentrantes(set(), {"transacoes_x.csv"}) == {"transacoes_x.csv"}
