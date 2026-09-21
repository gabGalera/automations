# Painel de automações

Aplicação web que centraliza ligar e desligar os watchers declarados em `automacoes.yaml`.

## Language

**Automação**:
Uma capacidade de background declarada no manifesto, com módulo Python, pasta monitorada e regras próprias. No código de `scripts/`, cada automação é um pacote (`consolidacao_base_1`, `consolidacao_base_2`, …).
_Avoid_: script, job, serviço

**Watcher**:
Processo em background que observa arquivos e dispara o motor da automação. É o que o operador liga e desliga; não é a UI.
_Avoid_: automação (quando se refere só ao processo), daemon genérico

**Painel**:
A interface web (React + Vite) que mostra o estado de cada watcher e permite ligar/desligar via API.
_Avoid_: painel Tkinter (legado), app React Native (legado), dashboard

**Manifesto**:
Arquivo `automacoes.yaml` na raiz do Painel listando as automações controláveis: id, módulo Python, pasta, título exibido.
_Avoid_: config, registry, inventário

**API de controle**:
Backend HTTP no host Windows que o Painel consulta para status e para start/stop de cada watcher. Não processa CSV nem grava planilha. Sem Docker na v1.
_Avoid_: backend de consolidação, motor, container

**Agente**:
Processo Python que hospeda a API de controle e importa os módulos `processos` de cada automação declarada no manifesto.
_Avoid_: sidecar, microserviço
