from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import controle, manifesto
from agent.config import WEB_DIST

app = FastAPI(title="Painel de Automações", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AutomacaoStatus(BaseModel):
    id: str
    titulo: str
    modulo: str
    pasta: str
    ligado: bool


class AcaoEmLote(BaseModel):
    resultados: list[AutomacaoStatus]


def _status(item: manifesto.Automacao) -> AutomacaoStatus:
    try:
        ligado = controle.watcher_ligado(item.modulo)
    except Exception:
        ligado = False
    return AutomacaoStatus(
        id=item.id,
        titulo=item.titulo,
        modulo=item.modulo,
        pasta=item.pasta,
        ligado=ligado,
    )


def _buscar(id_automacao: str) -> manifesto.Automacao:
    for item in manifesto.carregar_manifesto():
        if item.id == id_automacao:
            return item
    raise HTTPException(status_code=404, detail=f"Automação '{id_automacao}' não encontrada")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/automacoes", response_model=list[AutomacaoStatus])
def listar_automacoes() -> list[AutomacaoStatus]:
    return [_status(item) for item in manifesto.carregar_manifesto()]


@app.post("/automacoes/{id_automacao}/start", response_model=AutomacaoStatus)
def iniciar(id_automacao: str) -> AutomacaoStatus:
    item = _buscar(id_automacao)
    try:
        controle.ligar_watcher(item.modulo)
    except OSError as erro:
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    return _status(item)


@app.post("/automacoes/{id_automacao}/stop", response_model=AutomacaoStatus)
def parar(id_automacao: str) -> AutomacaoStatus:
    item = _buscar(id_automacao)
    try:
        controle.desligar_watcher(item.modulo)
    except OSError as erro:
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    return _status(item)


@app.post("/automacoes/start-all", response_model=AcaoEmLote)
def iniciar_todos() -> AcaoEmLote:
    resultados: list[AutomacaoStatus] = []
    for item in manifesto.carregar_manifesto():
        try:
            controle.ligar_watcher(item.modulo)
        except OSError:
            pass
        resultados.append(_status(item))
    return AcaoEmLote(resultados=resultados)


@app.post("/automacoes/stop-all", response_model=AcaoEmLote)
def parar_todos() -> AcaoEmLote:
    resultados: list[AutomacaoStatus] = []
    for item in manifesto.carregar_manifesto():
        try:
            controle.desligar_watcher(item.modulo)
        except OSError:
            pass
        resultados.append(_status(item))
    return AcaoEmLote(resultados=resultados)


_FALLBACK_HTML = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Painel de Automações</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 520px; margin: 48px auto; padding: 0 20px; color: #111827; }
    code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }
    p { line-height: 1.6; }
  </style>
</head>
<body>
  <h1>Painel de Automações</h1>
  <p>O agente está online, mas o frontend ainda não foi buildado.</p>
  <p>Na pasta <code>painel/</code>, rode:</p>
  <pre><code>.\\setup.ps1</code></pre>
  <p>Ou manualmente:</p>
  <pre><code>cd web
npm install
npm run build</code></pre>
  <p>Depois reinicie o agente e abra <a href="/">esta página</a> novamente.</p>
</body>
</html>"""


if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
else:

    @app.get("/", response_class=HTMLResponse)
    def frontend_ausente() -> str:
        return _FALLBACK_HTML
