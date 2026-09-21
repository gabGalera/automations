# Painel de automações

UI **web** (React + Vite + TypeScript) + agente **Python FastAPI** para ligar e desligar os watchers declarados em `automacoes.yaml`.

## Setup

```powershell
cd "C:\Users\danig\OneDrive\Área de Trabalho\automacoes\painel"
.\setup.ps1
```

## Uso (produção local)

```powershell
cd painel
.\start.ps1
```

Abra **http://127.0.0.1:8765** no navegador.

### Atalho na Área de Trabalho

```powershell
cd painel
.\install_atalho.ps1
```

Cria o atalho **Painel de Automações** — clique nele para subir o agente.

O agente serve a API e o frontend buildado (`web/dist/`).

## Desenvolvimento (hot-reload)

```powershell
# Terminal 1
cd painel
python -m agent

# Terminal 2
cd painel/web
npm run dev
```

Abra **http://localhost:5173** (proxy para a API na 8765).

## Estrutura

```
painel/
├── automacoes.yaml
├── agent/          # FastAPI
├── web/            # React + Vite
└── app/            # legado React Native (ignorar)
```

## Manifesto

```yaml
automacoes:
  - id: consolidacao_base_1
    titulo: Consolidação transações/recebíveis
    modulo: consolidacao_base_1
    pasta: "C:/Users/danig/OneDrive/Área de Trabalho/automacoes/dados/base_1"
```

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Status do agente |
| GET | `/automacoes` | Lista + estado |
| POST | `/automacoes/{id}/start` | Liga watcher |
| POST | `/automacoes/{id}/stop` | Desliga watcher |
| POST | `/automacoes/start-all` | Liga todos |
| POST | `/automacoes/stop-all` | Desliga todos |
