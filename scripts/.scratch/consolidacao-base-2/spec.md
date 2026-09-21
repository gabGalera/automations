Status: ready-for-agent

# Confirmações MP → planilha de output (`consolidacao_base_2`)

## Problem Statement

Em `base_1` o arquivo `Recebimentos_MP.xlsx` ganha linhas no fim com Id Transação Adquirente, Confirmacao MP e Data Recibo MP. Preciso que, neste PC, cada confirmação MP válida nova se ligue à planilha de output única (`output.xlsx`): positivo preenche a parcela ainda sem confirmação (ordem de Data Repasse); negativo nasce como linha consolidada de estorno. Não quero reprocessar o histórico que já está no arquivo na primeira largada, nem um segundo xlsx.

## Solution

Um segundo processo Python neste PC (painel próprio + Inicializar + `pythonw`), hostname `DaniGalera`, observa `Recebimentos_MP.xlsx` (`modified` / `created` / `moved`). Lê só linhas com as três colunas válidas; persiste na aba `controle` o conjunto de tuplas de confirmação MP já vistas; aplica só tuplas novas no `consolidado` (colunas `Confirmacao MP` e `Data Recibo MP` de primeira classe). O processo de CSV (`consolidacao_base_1`) passa a preservar essas colunas e as chaves extras de `controle`, relendo o xlsx antes de gravar para não apagar o lote do outro escritor.

## User Stories

1. As an operador neste PC, I want um processo `consolidacao_base_2` que sobe com o Windows via painel, so that eu ligo/desligo a consolidação MP sem terminal.
2. As an operador, I want um atalho de Inicializar distinto (`consolidacao-base-2`), so that o painel MP não depende do painel de CSV.
3. As an operador, I want o Desligar do painel MP matando só o watcher `consolidacao_base_2`, so that o watcher de CSV continua se eu só desligar o MP.
4. As an operador, I want o processo recusando rodar se o hostname não for `DaniGalera`, so that outro PC com o mesmo Drive não escreva na planilha de output.
5. As an operador, I want a aba `controle` registrando o hostname permitido, so that a trava de máquina continua visível.
6. As an operador, I want o processo gravando somente a planilha de output em `base_1`, so that `Recebimentos_MP.xlsx` permanece intacto.
7. As an operador, I want o watcher disparando em `modified`, `created` e `moved` de `Recebimentos_MP.xlsx`, so that uma linha acrescentada no mesmo arquivo dispara o merge.
8. As an operador, I want outros arquivos da pasta ignorados por este watcher, so that CSV e `output.xlsx` não disparam consolidação MP.
9. As an operador, I want o xlsx MP só lido depois que o tamanho estabilizar, com debounce, so that save/download pela metade não gera confirmação pela metade.
10. As an operador, I want, na primeira largada, as tuplas válidas já presentes no arquivo marcadas como vistas e **não** aplicadas, so that o histórico estático não entra sozinho no consolidado.
11. As an operador, I want o conjunto de tuplas vistas persistido na aba `controle`, so that restart aplica só o que é novo (incluindo o que chegou com o processo morto).
12. As an operador, I want `modified` repetido do Drive sem linha nova sendo no-op, so that sync não duplica confirmação.
13. As a leitor da planilha, I want só linha com as três colunas preenchidas e válidas virar confirmação MP, so that rascunho incompleto não entra.
14. As a leitor da planilha, I want Id Transação Adquirente vazio ou só espaço descartado, so that linha sem chave não polui o consolidado.
15. As a leitor da planilha, I want id numérico do Excel virar texto estável (sem notação científica), so that a ligação com o consolidado não quebra.
16. As a leitor da planilha, I want `Confirmacao MP` que não seja número, ou que seja zero, descartado, so that lixo e zero não viram linha consolidada.
17. As a leitor da planilha, I want `Data Recibo MP` em `DD-MM-YYYY` ou datetime Excel aceita, e o que não parseia descartado, so that data inválida não entra.
18. As a leitor da planilha, I want linha incompleta ignorada até as três colunas ficarem válidas, so that preencher a terceira célula vira tupla nova.
19. As a leitor da planilha, I want a mesma tupla `(id, valor, data)` aplicada no máximo uma vez, so that duas linhas idênticas no arquivo não duplicam o fato.
20. As a leitor da planilha, I want colunas `Confirmacao MP` e `Data Recibo MP` no `consolidado`, so that a confirmação mora na mesma linha consolidada.
21. As a leitor da planilha, I want `Data Recibo MP` como data nativa do Excel e `Confirmacao MP` como número (sinal no valor), so that filtro e soma funcionam.
22. As a leitor da planilha, I want ids continuando como texto, so that o Excel não come dígitos.
23. As a leitor da planilha, I want confirmação positiva preenchendo a primeira linha daquele id **sem** Confirmação MP, ordenada por Data Repasse e depois `data` da transação, so that o recibo liga na parcela ainda nua na ordem de liquidação.
24. As a leitor da planilha, I want, se não houver vaga positiva naquele id, uma linha nova (esqueleto: id + colunas MP; transação/recebível vazios se o id ainda não existir), so that o positivo órfão não espera o CSV.
25. As a leitor da planilha, I want confirmação negativa sempre em linha nova, so that estorno não sobrescreve parcela.
26. As a leitor da planilha, I want a linha de estorno copiando as colunas de transação da primeira linha daquele id se existir, recebível vazio, MP preenchido, so that o estorno herda a venda sem fingir parcela.
27. As a leitor da planilha, I want estorno sem id no consolidado nascendo só com id + colunas MP, so that estorno-primeiro não espera o CSV.
28. As a leitor da planilha, I want, num mesmo lote, positivos aplicados antes dos negativos, cada grupo por `Data Recibo MP` (empate: ordem física no arquivo), so that o estorno não “rouba” a vaga do positivo do mesmo save.
29. As a leitor da planilha, I want transação posterior substituindo **somente** as colunas de transação em **todas** as linhas daquele id (esqueleto MP e estorno incluídos), so that correção do exportador completa o órfão sem apagar confirmação nem recebível.
30. As a leitor da planilha, I want recebível preenchendo a primeira linha daquele id ainda sem recebível na ordem da aba (esqueleto clássico ou estorno), **só** colunas de recebível, so that a Confirmação MP da linha não some.
31. As a leitor da planilha, I want, se já existir parcela **e** um estorno ainda sem recebível, a próxima parcela preencher esse estorno, so that vaga vazia de recebível ganha prioridade sobre append.
32. As a leitor da planilha, I want recebível em append (cópia das colunas de transação, MP vazio) só quando não houver vaga sem recebível naquele id, so that sobreposição de delta de parcela continua empilhando quando não há esqueleto.
33. As an operador, I want o writer de CSV preservando `Confirmacao MP` e `Data Recibo MP` no cabeçalho estável, so that o próximo dump não apaga a consolidação MP.
34. As an operador, I want linha nova nascida de CSV com as colunas MP vazias, so that venda/parcela recém-chegada não inventa recibo.
35. As an operador, I want o writer de CSV preservando as chaves de `controle` que ele não possui (tuplas vistas), so that gravar um CSV não zera o cursor do MP.
36. As an operador, I want cada gravação relendo a planilha de output na hora, aplicando o lote em memória e então salvando, so that dois processos não sobrescrevem o lote um do outro com estado velho.
37. As an operador, I want retry de lock ~60s se o Excel estiver com o arquivo aberto, falha só em stderr, sem segundo nome de output, so that lock não cria `output.csv` nem arquivo auxiliar.
38. As an operador, I want `Recebimentos_MP.xlsx` reconhecido mesmo se o Drive criar temporário e renomear para esse nome, so that `moved` cobre o fluxo real.

## Implementation Decisions

- Segundo processo de longa duração no mesmo repositório (`watchdog`, `openpyxl`), espelhando as três camadas do CSV: motor puro, persistência da planilha de output, adaptador de pasta. Painel Ligar/Desligar e atalho de Inicializar próprios; marca de processo distinta da do watcher de CSV.
- Cabeçalho estável da aba `consolidado`: colunas de transação + recebível + `Confirmacao MP` + `Data Recibo MP`. Essas duas são de primeira classe no motor e na persistência do processo de CSV, não pass-through anônimo.
- Motor de CSV: ao substituir transação, só colunas de transação mudam; ao aplicar recebível, primeira linha daquele id com recebível vazio (predicado já usado: parcela e valor de repasse vazios) recebe só colunas de recebível; senão append com colunas de transação copiadas e MP vazio. Esqueleto de transação nova nasce com colunas MP vazias.
- Motor de confirmação MP (pacote novo): recebe estado do `consolidado` + linhas já parseadas do xlsx MP + conjunto de tuplas vistas; devolve novo consolidado e novo conjunto. Único lugar das regras: validade das três colunas, descarte de zero/id vazio/data ilegível, normalização de id e de data, ordenação do lote (positivos então negativos, cada grupo por data de recibo e ordem física), ligação positiva, append de estorno, órfão, idempotência por tupla. Semear na largada é a mesma extração de tuplas válidas unida ao conjunto visto, **sem** passar pelo apply.
- Tupla de confirmação MP: identidade `(Id Transação Adquirente texto, Confirmacao MP numérico, Data Recibo MP data)`. Persistida na aba `controle` de forma estável; os dois escritores preservam chaves de controle que não são donos.
- Ciclo de escrita (os dois processos): reler planilha de output → aplicar lote em memória → gravar. Retry de lock ~60s; não criar arquivo permanente com outro nome.
- Pasta observada: a mesma `base_1` do CSV. Artefato de origem: somente `Recebimentos_MP.xlsx`. Planilha de output: somente `output.xlsx`. Sem poll periódico de reentrada.
- Parse de `Data Recibo MP`: texto `DD-MM-YYYY` e datetime/date Excel → data nativa. `Confirmacao MP` → número (não texto). Id → texto estável.
- Hostname: `socket.gethostname()` ≠ `DaniGalera` encerra sem escrever.
- Sem ledger fora do xlsx. Sem mutex entre processos além de lock/retry do arquivo e releitura.

## Testing Decisions

- Bom teste: só comportamento observável do motor (e, onde inevitável, round-trip xlsx). Sem assertar watchdog, logs ou classes internas.
- **Seam principal (confirmação MP):** função que recebe linhas consolidadas + lote de linhas do xlsx MP (dicts com os três cabeçalhos reais) + conjunto de tuplas vistas, e devolve `(consolidado, vistas)`. Fixtures em memória, não arquivos na pasta Drive. Semear = unir tuplas válidas ao conjunto sem mutar o consolidado (pode ser a mesma função com flag ou um helper puro testado junto).
- Casos mínimos desse seam: incompleta/id vazio/zero/data ilegível descartados; id float vira texto estável; primeira largada não aplica o que já estava; tupla repetida não aplica de novo; positivo preenche vaga por Data Repasse então `data`; sem vaga → esqueleto; negativo appenda com cópia de transação; órfão positivo e negativo; lote misto positivo-então-negativo; completar as três colunas depois vira tupla nova.
- **Seam do motor de CSV (estender testes existentes `apply_lote`):** transação não apaga colunas MP; recebível preenche primeira vaga sem recebível inclusive estorno, sem alterar MP; com parcela já preenchida e estorno vazio, próximo recebível preenche o estorno; sem vaga, recebível ainda faz append; transação substitui só colunas de transação em todas as linhas do id.
- **Seam secundário (persistência):** round-trip temporário: `Data Recibo MP` data nativa, `Confirmacao MP` número, ids texto; gravar CSV depois de MP não dropa colunas MP nem o conjunto de tuplas em `controle`.
- Watcher, hostname, painel e Inicializar: fora da suíte obrigatória (checagem manual neste PC).
- Prior art: `tests/test_motor.py`, `tests/test_persistencia.py` do consolidação CSV; mesmo estilo de fixtures dict e `tmp_path` para xlsx.

## Out of Scope

- Backfill do `Recebimentos_MP.xlsx` já presente na primeira instalação (além de semear vistas).
- Poll de reentrada se o Drive apagar e recriar o arquivo sem `modified`/`created`/`moved`.
- Mutex dedicado entre os dois processos.
- Um único `pythonw` para CSV e MP.
- Outras pastas, outros nomes de arquivo MP, outros PCs.
- Alterar, mover ou apagar `Recebimentos_MP.xlsx`.
- `output.csv` ou qualquer artefato além de `output.xlsx`.
- Serviço Windows ou nuvem.
- Tratar zero como confirmação válida.
- Aplicar a mesma tupla mais de uma vez.
- Usar `ID Transacao` interno como chave.
- Deduplicar recebível por id + número de parcela (inalterado quando não há vaga).
- Escutar `modified` de CSV (o watcher de CSV continua só entrada na pasta).

## Further Notes

- O arquivo MP atual tem milhares de linhas e ids repetidos com pares +X/−X no mesmo dia; isso só entra no consolidado se a tupla for **nova depois** da semente da primeira largada.
- Glossário: `CONTEXT.md` (Confirmação MP, Tupla de confirmação MP, Merge por id, Linha consolidada, Planilha de output). Evitar “chave primária”, “recebimento”, “parcela MP”.
- A user story 18 do spec de CSV (“já tem parcela → sempre append”) fica **restringida**: append só se não houver linha daquele id sem recebível. Estorno vazio conta como essa vaga.
- Dois escritores no mesmo xlsx é deliberado: o risco de lost update trata-se com releitura, não com processo único.
