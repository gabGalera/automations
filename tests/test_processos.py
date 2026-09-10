from consolidacao_base_1.processos import eh_comando_watcher


def test_marca_watcher_nao_e_o_painel():
    assert eh_comando_watcher(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_1.watcher',
        pid=10,
        meu_pid=1,
    )
    assert not eh_comando_watcher(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_1',
        pid=10,
        meu_pid=1,
    )
    assert not eh_comando_watcher(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_1.watcher',
        pid=1,
        meu_pid=1,
    )


def test_legado_sem_marca_watcher_ainda_e_controlado():
    from consolidacao_base_1.processos import eh_processo_a_controlar

    assert eh_processo_a_controlar(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_1',
        pid=10,
        meu_pid=1,
    )
    assert not eh_processo_a_controlar(
        r'"C:\Python\pythonw.exe" -m consolidacao_base_1',
        pid=1,
        meu_pid=1,
    )
