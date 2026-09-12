# 03: Watcher em Recebimentos_MP

**What to build:** Um processo de longa duração observa a pasta `base_1` e, quando `Recebimentos_MP.xlsx` é modificado, criado ou movido para dentro (tamanho estável + debounce), relê a planilha de output, aplica o lote de confirmações MP e grava. Arquivo de origem intacto. Outros arquivos da pasta não disparam este processo. Retry se o Excel estiver com o output aberto; sem segundo arquivo de output.

**Blocked by:** 02 Aplicar confirmações MP com cursor

**Status:** resolved

- [x] `modified` / `created` / `moved` de `Recebimentos_MP.xlsx` disparam o ciclo depois do tamanho estabilizar
- [x] CSV, `output.xlsx` e demais nomes não disparam este watcher
- [x] Origem `Recebimentos_MP.xlsx` não é alterada, movida nem apagada
- [x] Ciclo: reler output → aplicar → gravar; lock ~60s; falha só em stderr
- [x] Primeira largada só semeia tuplas já no arquivo; linha válida nova depois disso entra no consolidado
- [x] `modified` sem tupla nova é no-op (não duplica)
- [x] Dá para exercitar o módulo watcher neste PC e ver o consolidado atualizar

## Answer

Watcher de `consolidacao_base_2` observa só `Recebimentos_MP.xlsx` (`modified` / `created` / `moved`), espera tamanho estável + debounce de 4s, relê `output.xlsx`, aplica e grava. Largada semeia o cursor sem mutar o consolidado. Origem só é lida.

- `python -m consolidacao_base_2.watcher`
- `consolidacao_base_2/watcher.py`: `sincronizar_mp`, `observar`
- `consolidacao_base_2/pasta.py`: `eh_origem_mp`, `ler_xlsx_mp`
- Tests: `tests/test_watcher_mp.py` (ciclo sem Observer)
