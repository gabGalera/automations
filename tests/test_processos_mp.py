from consolidacao_base_2.processos import eh_comando_watcher, eh_processo_a_controlar


def test_marca_watcher_mp_nao_e_o_painel():
    assert eh_comando_watcher(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_2.watcher',
        pid=10,
        meu_pid=1,
    )
    assert not eh_comando_watcher(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_2',
        pid=10,
        meu_pid=1,
    )
    assert not eh_comando_watcher(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_2.watcher',
        pid=1,
        meu_pid=1,
    )


def test_desligar_mp_nao_controla_watcher_csv():
    cmd = r'"C:\Python\pythonw.exe" -m consolidacao_base_1.watcher'
    assert not eh_comando_watcher(cmd, pid=10, meu_pid=1)
    assert not eh_processo_a_controlar(cmd, pid=10, meu_pid=1)
    assert not eh_processo_a_controlar(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_1',
        pid=10,
        meu_pid=1,
    )
