# 03: Watcher em Recebimentos_MP

**What to build:** Um processo de longa duração observa a pasta `base_1` e, quando `Recebimentos_MP.xlsx` é modificado, criado ou movido para dentro (tamanho estável + debounce), relê a planilha de output, aplica o lote de confirmações MP e grava. Arquivo de origem intacto. Outros arquivos da pasta não disparam este processo. Retry se o Excel estiver com o output aberto; sem segundo arquivo de output.

**Blocked by:** 02 Aplicar confirmações MP com cursor

**Status:** ready-for-agent

- [ ] `modified` / `created` / `moved` de `Recebimentos_MP.xlsx` disparam o ciclo depois do tamanho estabilizar
- [ ] CSV, `output.xlsx` e demais nomes não disparam este watcher
- [ ] Origem `Recebimentos_MP.xlsx` não é alterada, movida nem apagada
- [ ] Ciclo: reler output → aplicar → gravar; lock ~60s; falha só em stderr
- [ ] Primeira largada só semeia tuplas já no arquivo; linha válida nova depois disso entra no consolidado
- [ ] `modified` sem tupla nova é no-op (não duplica)
- [ ] Dá para exercitar o módulo watcher neste PC e ver o consolidado atualizar
