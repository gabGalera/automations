import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

import pytest

from consolidacao.planilha import PlanilhaBloqueada, exportar


def test_lock_estourado_sinaliza_o_chamador_e_nao_cria_outro_arquivo(tmp_path: Path, monkeypatch):
    if sys.platform != "win32":
        pytest.skip("lock exclusivo de arquivo é do Windows")
    caminho = tmp_path / "output.xlsx"
    caminho.write_bytes(b"vigente")
    handle = _travar(caminho)
    relogio = {"t": 0.0}

    def agora():
        return relogio["t"]

    def dormir(segundos):
        relogio["t"] += segundos

    monkeypatch.setattr("consolidacao.planilha.time_mod.monotonic", agora)
    monkeypatch.setattr("consolidacao.planilha.time_mod.sleep", dormir)
    try:
        with pytest.raises(PlanilhaBloqueada):
            exportar(caminho, [{"Cliente": "NAO DEVE GRAVAR"}])
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)

    assert caminho.read_bytes() == b"vigente"
    assert [item.name for item in tmp_path.iterdir()] == ["output.xlsx"]
    assert 60 <= relogio["t"] <= 70


def _travar(caminho: Path):
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID = wintypes.HANDLE(-1).value
    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    CreateFileW.restype = wintypes.HANDLE
    handle = CreateFileW(
        str(caminho),
        GENERIC_READ | GENERIC_WRITE,
        0,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == INVALID:
        raise OSError("não foi possível travar o output.xlsx")
    return handle
