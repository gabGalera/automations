# 02: Aplicar confirmações MP com cursor

**What to build:** Dado o consolidado, um lote de linhas do xlsx MP e o conjunto de tuplas vistas, só confirmações MP válidas e ainda não vistas entram no consolidado: positivo liga na vaga (Data Repasse, depois `data`); sem vaga ou id ausente vira esqueleto; negativo sempre linha nova (copia transação se houver); lote positivos então negativos; mesma tupla no máximo uma vez. Primeira semente une tuplas válidas ao conjunto visto sem mutar o consolidado. O conjunto persiste em `controle` e sobrevive a uma gravação posterior do processo de CSV.

**Blocked by:** 01 Planilha e merge CSV conhecem confirmação MP

**Status:** resolved

- [x] Linha incompleta, id vazio, valor zero/não numérico ou data ilegível não vira confirmação MP
- [x] Id numérico vira texto estável (sem notação científica)
- [x] Semear vistas não altera o consolidado; apply posterior da mesma tupla é no-op
- [x] Positivo preenche primeira vaga daquele id sem Confirmação MP, ordem Data Repasse então `data`; senão esqueleto
- [x] Negativo appenda (cópia de transação se existir; senão só id + MP); não sobrescreve parcela
- [x] No mesmo lote: positivos antes de negativos; cada grupo por `Data Recibo MP` (empate: ordem física)
- [x] Tupla idêntica não aplica de novo; completar as três colunas depois conta como tupla nova
- [x] Relida da planilha: tuplas em `controle` e colunas MP intactas após o writer de CSV gravar

## Answer

Só confirmação MP válida e ainda não vista entra no consolidado; semear une tuplas ao cursor sem mutar linhas. O conjunto vive em `controle.tuplas_mp` (JSON) e reusa `gravar_output`/`carregar_consolidado`.

- `consolidacao_base_2/motor.py`: `apply_confirmacoes_mp(consolidado, lote, vistas, *, semear=False) -> (consolidado, vistas)`
- `consolidacao_base_2/persistencia.py`: `controle_com_vistas`, `vistas_de_controle`
- Tests: `tests/test_motor_mp.py`, `tests/test_persistencia_mp.py`
