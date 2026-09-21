# 04: Painel, hostname e Inicializar

**What to build:** O operador liga e desliga o watcher de confirmação MP por um painel próprio, com atalho de Inicializar distinto do CSV. O processo recusa máquina que não seja `DaniGalera`. Desligar mata só o watcher MP. A aba `controle` continua mostrando o hostname permitido.

**Blocked by:** 03 Watcher em Recebimentos_MP

**Status:** resolved

- [x] Painel Ligar/Desligar controla apenas `consolidacao_base_2.watcher`
- [x] Desligar o MP não encerra o watcher de transações/recebíveis
- [x] Hostname diferente de `DaniGalera` encerra sem escrever na planilha de output
- [x] Atalho de Inicializar próprio abre o painel MP (não o painel de CSV)
- [x] `controle` materializa o hostname permitido
- [ ] Checagem manual neste PC: login/atalho abre o painel; ligar sobe o watcher; desligar derruba só ele

## Answer

Painel e atalho próprios para confirmação MP. Ligar/desligar usa a marca `consolidacao_base_2.watcher`; o matcher do CSV não reconhece essa marca. Hostname `DaniGalera` é exigido no painel e em `observar()` antes de gravar; `gravar_output` segue materializando `hostname_permitido` em `controle`.

- `pythonw -m consolidacao_base_2` abre o painel
- `install_startup_base_2.ps1` cria `consolidacao-base-2.lnk` na pasta Inicializar
- Tests: `tests/test_processos_mp.py` (isolamento das marcas); checagem de painel/atalho continua manual neste PC
