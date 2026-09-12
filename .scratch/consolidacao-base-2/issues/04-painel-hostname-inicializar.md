# 04: Painel, hostname e Inicializar

**What to build:** O operador liga e desliga o watcher de confirmação MP por um painel próprio, com atalho de Inicializar distinto do CSV. O processo recusa máquina que não seja `DaniGalera`. Desligar mata só o watcher MP. A aba `controle` continua mostrando o hostname permitido.

**Blocked by:** 03 Watcher em Recebimentos_MP

**Status:** ready-for-agent

- [ ] Painel Ligar/Desligar controla apenas `consolidacao_base_2.watcher`
- [ ] Desligar o MP não encerra o watcher de transações/recebíveis
- [ ] Hostname diferente de `DaniGalera` encerra sem escrever na planilha de output
- [ ] Atalho de Inicializar próprio abre o painel MP (não o painel de CSV)
- [ ] `controle` materializa o hostname permitido
- [ ] Checagem manual neste PC: login/atalho abre o painel; ligar sobe o watcher; desligar derruba só ele
