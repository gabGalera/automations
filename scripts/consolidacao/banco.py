from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from consolidacao.motor import (
    COL_CONFIRMACAO,
    COL_DATA_RECIBO,
    ID_ADQUIRENTE,
    Estado,
    _id_estavel,
    _parse_confirmacao,
    _tuplas_aplicadas,
    apply_lote,
)


class ConflitoDeLote(Exception):
    pass


@dataclass(frozen=True)
class Chegada:
    tipo: str
    linha: dict


@dataclass
class EstadoBanco:
    consolidado: list[dict]
    maquinha: set[str]
    pendentes: set[tuple]
    aplicadas: set[tuple]
    chegadas: list[Chegada]
    revisao: int

    def para_seam(self) -> Estado:
        return Estado(
            consolidado=[dict(linha) for linha in self.consolidado],
            maquinha=set(self.maquinha),
            pendentes=set(self.pendentes),
        )


class Banco:
    def __init__(self, caminho: Path, criado: bool, conn: sqlite3.Connection):
        self.caminho = caminho
        self.criado = criado
        self._conn = conn

    def __enter__(self) -> Banco:
        return self

    def __exit__(self, *args: object) -> None:
        self.fechar()

    def fechar(self) -> None:
        self._conn.close()

    def ler(self) -> EstadoBanco:
        self._conn.execute("BEGIN")
        try:
            estado = _ler(self._conn)
            self._conn.commit()
            return estado
        except Exception:
            self._conn.rollback()
            raise

    def gravar(self, base: EstadoBanco, estado: Estado, lote: dict) -> EstadoBanco:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            atual = self._conn.execute("SELECT revisao FROM meta WHERE id = 1").fetchone()
            if atual is None or atual[0] != base.revisao:
                self._conn.rollback()
                raise ConflitoDeLote("outro processo gravou um lote")
            _escrever_snapshot(self._conn, estado)
            _fundir_chegadas(self._conn, lote, estado)
            self._conn.execute(
                "UPDATE meta SET revisao = ? WHERE id = 1",
                (atual[0] + 1,),
            )
            self._conn.commit()
        except ConflitoDeLote:
            raise
        except Exception:
            self._conn.rollback()
            raise
        return self.ler()


def caminho_padrao() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise RuntimeError("LOCALAPPDATA não está definido")
    return Path(base) / "automacoes" / "base_1" / "consolidado.sqlite"


def abrir(caminho: Path | None = None) -> Banco:
    destino = caminho if caminho is not None else caminho_padrao()
    destino.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(destino, timeout=60)
    conn.isolation_level = None
    try:
        conn.execute("PRAGMA journal_mode=WAL").fetchone()
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("BEGIN IMMEDIATE")
        try:
            if _tem_esquema(conn):
                criado = False
            else:
                _criar_esquema(conn)
                criado = True
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    except Exception:
        conn.close()
        raise
    return Banco(destino, criado, conn)


def refazer(chegadas: list[Chegada]) -> Estado:
    estado = Estado(consolidado=[], maquinha=set(), pendentes=set())
    for chegada in chegadas:
        estado = apply_lote(estado, {"tipo": chegada.tipo, "linhas": [dict(chegada.linha)]})
    return estado


def _tem_esquema(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'meta'"
    ).fetchone()
    return row is not None


def _criar_esquema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE meta (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            revisao INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE consolidado (
            ordem INTEGER PRIMARY KEY,
            linha TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE TABLE maquinha (id_adquirente TEXT PRIMARY KEY)")
    conn.execute(
        """
        CREATE TABLE pendentes (
            id_adquirente TEXT NOT NULL,
            valor TEXT NOT NULL,
            data_recibo TEXT NOT NULL,
            PRIMARY KEY (id_adquirente, valor, data_recibo)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE aplicadas (
            id_adquirente TEXT NOT NULL,
            valor TEXT NOT NULL,
            data_recibo TEXT NOT NULL,
            PRIMARY KEY (id_adquirente, valor, data_recibo)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE chegadas (
            ordem INTEGER PRIMARY KEY,
            tipo TEXT NOT NULL,
            id_adquirente TEXT NOT NULL,
            identidade TEXT NOT NULL,
            linha TEXT NOT NULL,
            UNIQUE (tipo, id_adquirente, identidade)
        )
        """
    )
    conn.execute("INSERT INTO meta (id, revisao) VALUES (1, 0)")


def _ler(conn: sqlite3.Connection) -> EstadoBanco:
    revisao = conn.execute("SELECT revisao FROM meta WHERE id = 1").fetchone()[0]
    consolidado = [
        _loads(row[0])
        for row in conn.execute("SELECT linha FROM consolidado ORDER BY ordem")
    ]
    maquinha = {row[0] for row in conn.execute("SELECT id_adquirente FROM maquinha")}
    pendentes = _ler_tuplas(conn, "pendentes")
    aplicadas = _ler_tuplas(conn, "aplicadas")
    chegadas = [
        Chegada(row[0], _loads(row[1]))
        for row in conn.execute("SELECT tipo, linha FROM chegadas ORDER BY ordem")
    ]
    return EstadoBanco(consolidado, maquinha, pendentes, aplicadas, chegadas, revisao)


def _ler_tuplas(conn: sqlite3.Connection, tabela: str) -> set[tuple]:
    sql = {
        "pendentes": "SELECT id_adquirente, valor, data_recibo FROM pendentes",
        "aplicadas": "SELECT id_adquirente, valor, data_recibo FROM aplicadas",
    }[tabela]
    return {
        (row[0], _valor_de_texto(row[1]), date.fromisoformat(row[2]))
        for row in conn.execute(sql)
    }


def _escrever_snapshot(conn: sqlite3.Connection, estado: Estado) -> None:
    conn.execute("DELETE FROM consolidado")
    conn.executemany(
        "INSERT INTO consolidado (ordem, linha) VALUES (?, ?)",
        ((i, _dumps(dict(linha))) for i, linha in enumerate(estado.consolidado)),
    )
    conn.execute("DELETE FROM maquinha")
    conn.executemany(
        "INSERT INTO maquinha (id_adquirente) VALUES (?)",
        ((id_,) for id_ in estado.maquinha),
    )
    _escrever_tuplas(conn, "pendentes", estado.pendentes)
    _escrever_tuplas(conn, "aplicadas", _tuplas_aplicadas(estado.consolidado))


def _escrever_tuplas(conn: sqlite3.Connection, tabela: str, tuplas: set[tuple]) -> None:
    apagar = {
        "pendentes": "DELETE FROM pendentes",
        "aplicadas": "DELETE FROM aplicadas",
    }[tabela]
    inserir = {
        "pendentes": "INSERT INTO pendentes (id_adquirente, valor, data_recibo) VALUES (?, ?, ?)",
        "aplicadas": "INSERT INTO aplicadas (id_adquirente, valor, data_recibo) VALUES (?, ?, ?)",
    }[tabela]
    conn.execute(apagar)
    conn.executemany(inserir, (_campos_tupla(tupla) for tupla in tuplas))


def _campos_tupla(tupla: tuple) -> tuple[str, str, str]:
    if (
        not isinstance(tupla, tuple)
        or len(tupla) != 3
        or not isinstance(tupla[0], str)
        or isinstance(tupla[1], bool)
        or not isinstance(tupla[1], (int, float))
        or not isinstance(tupla[2], date)
        or isinstance(tupla[2], datetime)
    ):
        raise TypeError("tupla de confirmação MP inválida")
    return tupla[0], _valor_texto(tupla[1]), tupla[2].isoformat()


def _fundir_chegadas(conn: sqlite3.Connection, lote: dict, estado: Estado) -> None:
    tipo = lote.get("tipo")
    linhas = lote.get("linhas") or []
    if tipo == "transacao":
        for linha in linhas:
            _fundir_transacao(conn, linha)
    elif tipo == "recebivel":
        for linha in linhas:
            _fundir_recebivel(conn, linha)
    elif tipo == "confirmacao_mp":
        _fundir_confirmacoes(conn, linhas)
    _fundir_tuplas_ausentes(conn, estado)


def _fundir_transacao(conn: sqlite3.Connection, linha: dict) -> None:
    if not isinstance(linha, dict):
        return
    chave = _id_estavel(linha.get(ID_ADQUIRENTE))
    if not chave:
        return
    _upsert_chegada(conn, "transacao", chave, "", linha, substituir=True)


def _fundir_recebivel(conn: sqlite3.Connection, linha: dict) -> None:
    if not isinstance(linha, dict):
        return
    chave = _id_estavel(linha.get(ID_ADQUIRENTE))
    if not chave:
        return
    parcela = linha.get("Parcela Recebivel") or ""
    _upsert_chegada(
        conn,
        "recebivel",
        chave,
        json.dumps(parcela, ensure_ascii=False),
        linha,
        substituir=True,
    )


def _fundir_confirmacoes(conn: sqlite3.Connection, linhas: list) -> None:
    novas: list[tuple[tuple, dict]] = []
    vistas: set[tuple] = set()
    for linha in linhas:
        if not isinstance(linha, dict):
            continue
        tupla = _parse_confirmacao(linha)
        if tupla is None or tupla in vistas or _chegada_existe(conn, "confirmacao_mp", tupla[0], _identidade_tupla(tupla)):
            continue
        vistas.add(tupla)
        novas.append((tupla, linha))
    novas.sort(key=lambda item: (item[0][1] < 0, item[0][2]))
    for tupla, linha in novas:
        _upsert_chegada(
            conn,
            "confirmacao_mp",
            tupla[0],
            _identidade_tupla(tupla),
            linha,
            substituir=False,
        )


def _fundir_tuplas_ausentes(conn: sqlite3.Connection, estado: Estado) -> None:
    vistas = set(estado.pendentes) | _tuplas_aplicadas(estado.consolidado)
    ausentes = [
        tupla
        for tupla in vistas
        if not _chegada_existe(conn, "confirmacao_mp", tupla[0], _identidade_tupla(tupla))
    ]
    ausentes.sort(key=lambda tupla: (tupla[1] < 0, tupla[2]))
    for tupla in ausentes:
        linha = {
            ID_ADQUIRENTE: tupla[0],
            COL_CONFIRMACAO: tupla[1],
            COL_DATA_RECIBO: tupla[2],
        }
        _upsert_chegada(
            conn,
            "confirmacao_mp",
            tupla[0],
            _identidade_tupla(tupla),
            linha,
            substituir=False,
        )


def _chegada_existe(
    conn: sqlite3.Connection, tipo: str, id_adquirente: str, identidade: str
) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM chegadas
        WHERE tipo = ? AND id_adquirente = ? AND identidade = ?
        """,
        (tipo, id_adquirente, identidade),
    ).fetchone()
    return row is not None


def _upsert_chegada(
    conn: sqlite3.Connection,
    tipo: str,
    id_adquirente: str,
    identidade: str,
    linha: dict,
    *,
    substituir: bool,
) -> None:
    payload = _dumps(dict(linha))
    row = conn.execute(
        """
        SELECT ordem FROM chegadas
        WHERE tipo = ? AND id_adquirente = ? AND identidade = ?
        """,
        (tipo, id_adquirente, identidade),
    ).fetchone()
    if row is None:
        ordem = conn.execute("SELECT COALESCE(MAX(ordem), -1) FROM chegadas").fetchone()[0] + 1
        conn.execute(
            """
            INSERT INTO chegadas (ordem, tipo, id_adquirente, identidade, linha)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ordem, tipo, id_adquirente, identidade, payload),
        )
        return
    if substituir:
        conn.execute("UPDATE chegadas SET linha = ? WHERE ordem = ?", (payload, row[0]))


def _identidade_tupla(tupla: tuple) -> str:
    valor = tupla[1]
    marca = "i" if isinstance(valor, int) else "f"
    return json.dumps([marca, valor, tupla[2].isoformat()], ensure_ascii=False)


def _valor_texto(valor: int | float) -> str:
    marca = "i" if isinstance(valor, int) else "f"
    return json.dumps({"t": marca, "v": valor}, ensure_ascii=False)


def _valor_de_texto(texto: str) -> int | float:
    dado = json.loads(texto)
    if dado["t"] == "i":
        return int(dado["v"])
    return float(dado["v"])


def _dumps(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, default=_json_default)


def _loads(texto: str) -> Any:
    return json.loads(texto, object_hook=_object_hook)


def _json_default(obj: Any) -> dict:
    if isinstance(obj, datetime):
        return {"__tipo": "datetime", "v": obj.isoformat()}
    if isinstance(obj, date):
        return {"__tipo": "date", "v": obj.isoformat()}
    if isinstance(obj, time):
        return {"__tipo": "time", "v": obj.isoformat()}
    raise TypeError(f"não serializo {type(obj).__name__}")


def _object_hook(obj: dict) -> Any:
    tipo = obj.get("__tipo")
    if tipo == "date":
        return date.fromisoformat(obj["v"])
    if tipo == "time":
        return time.fromisoformat(obj["v"])
    if tipo == "datetime":
        return datetime.fromisoformat(obj["v"])
    return obj
