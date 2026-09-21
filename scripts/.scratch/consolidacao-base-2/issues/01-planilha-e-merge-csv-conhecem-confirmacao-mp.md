# 01: Planilha e merge CSV conhecem confirmação MP

**What to build:** A aba `consolidado` passa a ter as colunas de confirmação MP de primeira classe. O merge de transação e recebível não apaga esses fatos; o recebível preenche a primeira linha daquele id ainda sem recebível (esqueleto ou estorno), só com colunas de recebível; transação substitui só colunas de transação. A aba `controle` deixa de apagar chaves que o processo de CSV não é dono. Round-trip da planilha de output: `Confirmacao MP` numérico, `Data Recibo MP` data nativa, ids texto. O fluxo CSV atual permanece correto.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] Cabeçalho estável do `consolidado` inclui `Confirmacao MP` e `Data Recibo MP` depois das colunas de transação e recebível
- [x] Transação nova / substituição de transação não zera nem dropa colunas de confirmação MP
- [x] Recebível preenche a primeira vaga sem recebível na ordem da aba (incluindo linha de estorno), sem alterar o resto da linha
- [x] Sem vaga, recebível ainda entra como linha nova (colunas de transação copiadas, MP vazio)
- [x] Gravar e reler xlsx preserva número em `Confirmacao MP`, data nativa em `Data Recibo MP`, e chaves extras de `controle`
- [x] Testes existentes de `apply_lote` e persistência CSV continuam verdes, mais os casos acima

## Answer

Merge CSV e persistência da planilha de output conhecem confirmação MP de primeira classe; `controle` extras sobrevivem à gravação do CSV. Watcher de CSV relê e devolve o dict de controle ao gravar.

