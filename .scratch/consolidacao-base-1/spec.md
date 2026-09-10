Status: ready-for-agent

# Consolidação transações + recebíveis (`base_1`)

## Problem Statement

Dumps CSV de transações e recebíveis caem em `H:\Meu Drive\AUTOMACOES\dados\base_1` em horários diferentes. Preciso de uma planilha de output única, atualizada só neste computador, onde cada parcela é uma linha consolidada, as duas pontas se encontram pelo Id Transação Adquirente (mesmo se o recebível chegar primeiro), e eu não mexo nos CSVs de origem.

## Solution

Um processo Python que vive neste PC (Inicializar + `pythonw`), observa a pasta `base_1`, e quando um CSV de transação ou recebível **entra** na pasta aplica as regras de merge na planilha de output (`output.xlsx`: abas `consolidado` e `controle`). Não há backfill: arquivos que já estavam na pasta na largada são ignorados até saírem e entrarem de novo.

## User Stories

1. As an operador neste PC, I want um processo que sobe com o Windows, so that a pasta `base_1` é observada sem eu abrir terminal.
2. As an operador, I want o processo recusando rodar se o hostname não for `DaniGalera`, so that outro PC com o mesmo Drive não escreva na planilha de output.
3. As an operador, I want o processo gravando **somente** `output.xlsx` em `base_1`, so that os CSVs de origem permanecem intactos.
4. As an operador, I want abas `consolidado` (linhas consolidadas) e `controle` (hostname permitido e metadados do processo), so that dados e operação não se misturam.
5. As an operador, I want o watcher disparando só quando um arquivo **entra** na pasta (`created` ou rename/move para dentro de `base_1`), so that `modified` do Drive não reprocessa o mesmo arquivo.
6. As an operador, I want arquivos já presentes na pasta na largada ignorados, so that o histórico estático não entra sozinho na planilha de output.
7. As an operador, I want o CSV só lido depois que o tamanho estabilizar, so that um download incompleto do Drive não gera linha consolidada pela metade.
8. As an operador, I want prefixos `transacoes_`, `transações_`, `recebiveis_` e `recebíveis_` (case-insensitive, com ou sem acento), so that o nome real do exportador não quebra o gatilho.
9. As an operador, I want arquivos que não são CSV com esses prefixos ignorados, so that `output.xlsx` e outros arquivos na pasta não disparam merge.
10. As a leitor da planilha, I want cada recebível (parcela) como uma linha consolidada, so that `Parcela Recebivel`, `Valor Repasse` e `Data Repasse` cabem sem achatar parcelas.
11. As a leitor da planilha, I want transação sem recebível ainda assim na aba `consolidado` (colunas de recebível vazias), so that venda recém-chegada não some.
12. As a leitor da planilha, I want recebível que chegou antes da transação na aba `consolidado` (colunas de transação vazias), so that a parcela não espera o CSV de transações.
13. As a leitor da planilha, I want transação sem Id Transação Adquirente descartada, so that linha sem chave não polui o consolidado.
14. As a leitor da planilha, I want recebível sem Id Transação Adquirente descartado, so that parcela sem chave não entra.
15. As a leitor da planilha, I want, ao chegar uma transação cujo id já existe, as **colunas de transação de todas as linhas daquele id substituídas** pela nova (mesmo já preenchidas), so that correção no exportador vira a versão vigente sem segunda transação.
16. As a leitor da planilha, I want, ao chegar uma transação cujo id não existe, uma linha-esqueleto (transação preenchida, recebível vazio), so that o left join no tempo funciona.
17. As a leitor da planilha, I want, ao chegar recebível para um id que só tem esqueleto, esse esqueleto preenchido com a primeira parcela e as demais parcelas em linhas novas com as mesmas colunas de transação, so that não fica esqueleto órfão junto das parcelas.
18. As a leitor da planilha, I want, ao chegar recebível para um id que já tem pelo menos uma parcela, **sempre uma linha nova** (mesmo `id` + mesmo número de parcela já existente), so that sobreposição de delta de recebível não some.
19. As a leitor da planilha, I want, ao chegar transação para linhas que só tinham recebível, as colunas de transação dessas linhas preenchidas/substituídas via merge por id, so that o recebível-primeiro se completa.
20. As a leitor da planilha, I want todas as colunas do CSV de transações **exceto** `Ultima Atualizacao`, so that o consolidado não carrega timestamp operacional do exportador.
21. As a leitor da planilha, I want `Data/Hora` da transação partido em `data` e `hora`, e a coluna `Data/Hora` removida, so that filtro por dia e por hora no Excel funciona.
22. As a leitor da planilha, I want `Data Repasse` como coluna única, so that data de liquidação não é partida.
23. As a leitor da planilha, I want colunas de recebível `Parcela Recebivel`, `Total Parcelas`, `taxa % cliente` (ex-`Taxa %`), `taxa valor cliente` (ex-`Taxa Valor`), `Valor Repasse` e `Data Repasse`, so that taxa da liquidação não colide com taxa da transação.
24. As a leitor da planilha, I want `data` e `Data Repasse` como **data nativa do Excel**, and `hora` como **hora nativa do Excel**, so that a planilha ordena e filtra como planilha, não como texto.
25. As a leitor da planilha, I want ids, textos e valores monetários/percentuais no espírito do CSV (separador de colunas do CSV não entra no xlsx), so that não perco `80,00` / identificadores por conversão agressiva — datas/hora são a exceção nativa.
26. As an operador, I want CSV de origem com delimitador `;` e encoding UTF-8 (BOM opcional), so that os dumps atuais são lidos.
27. As an operador, I want se `output.xlsx` estiver aberto no Excel, o processo retentar cerca de um minuto e desistir só no stderr, so that lock do Excel não cria segundo arquivo de output.
28. As an operador, I want a aba `controle` registrando o hostname permitido, so that a trava de máquina é visível na própria planilha de output.
29. As an operador, I want um único escritor: este processo, so that não há `output.csv` nem planilha auxiliar.
30. As an operador, I want prefixo reconhecido mesmo se o Drive criar o arquivo com nome temporário e **renomear** para `transacoes_*.csv` / `recebiveis_*.csv`, so that o gatilho “entrou na pasta” cubra o fluxo real do Drive.

## Implementation Decisions

- Um processo Python de longa duração neste repositório de automações, com dependências `watchdog` e `openpyxl` (ou equivalente capaz de data/hora nativa no xlsx).
- Três camadas estreitas: (1) **motor de consolidação** puro (estado da aba `consolidado` + evento “chegou um CSV de transações|recebíveis já parseado” → novo estado); (2) **persistência xlsx** (ler/gravar `consolidado` + `controle`, tipos Excel para `data`/`hora`/`Data Repasse`, lock/retry); (3) **adaptador de pasta** (watchdog `created` + move/rename para dentro de `base_1`, debounce de tamanho, filtro de prefixo, hostname).
- O motor é o único lugar das regras de merge por id, descarte de id vazio, esqueleto, substituição de colunas de transação, append de recebível e expansão do esqueleto.
- Evento de entrada: path absoluto do arquivo que acabou de se tornar estável; o adaptador classifica transação vs recebível pelo prefixo do **nome final**; lê o CSV; chama o motor; grava xlsx.
- Hostname: se `socket.gethostname()` ≠ `DaniGalera`, o processo encerra sem escrever. A aba `controle` materializa esse hostname permitido.
- Pasta observada: `H:\Meu Drive\AUTOMACOES\dados\base_1`. Planilha de output: `output.xlsx` nessa pasta. Criar o arquivo com as duas abas se ainda não existir ou se o xlsx atual for casco vazio.
- Parse de `Data/Hora`: `dd/mm/aaaa HH:MM:SS` (e variantes razoáveis de espaço) → data Excel + hora Excel. `Data Repasse` / datas só-dia: `dd/mm/aaaa` → data Excel. Célula vazia permanece vazia.
- Colunas de transação no consolidado (ordem estável, nomes de cabeçalho): as do CSV menos `Ultima Atualizacao` e `Data/Hora`, mais `data` e `hora` no lugar de `Data/Hora`. Em seguida as colunas de recebível renomeadas.
- Retry de lock: tentativas durante ~60s; falha visível só em stderr; não criar `output.xlsx.tmp` permanente nem segundo nome.
- Startup: atalho na pasta Inicializar apontando para `pythonw` + script do watcher. O spec não exige serviço Windows.
- Sem ledger de “arquivo já processado” fora do xlsx; idempotência vem das regras do motor e de não escutar `modified`. Debounce de tamanho evita o created prematuro.
- Números e texto que não são as três colunas de data/hora: gravar de forma que o Excel não interprete id de adquirente como número científico; preferir texto para ids e para campos ambíguos.

## Testing Decisions

- Bom teste: só comportamento observável do **motor** (e, onde inevitável, round-trip xlsx de data/hora nativa). Sem assertar chamadas do watchdog, ordem de logs, ou estrutura interna de classes.
- **Seam único preferido:** função (ou módulo) que recebe o estado atual das linhas consolidadas + um lote tipado (`transacao` | `recebivel`) e devolve o novo estado. Fixtures são dicts/listas com os cabeçalhos reais dos CSVs, não arquivos na pasta Drive.
- Casos mínimos do motor: id vazio descartado (duas pontas); transação nova → esqueleto; recebível novo sem transação → linhas só-recebível; transação depois preenche/substitui todas as linhas daquele id; recebível em esqueleto expande; segundo recebível com mesma parcela **adiciona** linha; segunda transação **não** duplica transação e **substitui** colunas de transação; `Data/Hora` some; `Ultima Atualizacao` some; nomes `taxa % cliente` / `taxa valor cliente`.
- Seam secundário (só o necessário): gravar e reler um xlsx temporário e verificar que `data`, `hora` e `Data Repasse` são valores datetime/time do Excel, não string.
- Watcher, hostname e Inicializar: fora da suíte automatizada obrigatória (checagem manual neste PC), a menos que o adaptador de pasta seja extraído com um relógio/fs injetável — não é o seam principal.
- Não há prior art de testes neste repositório (hoje só docs/`CONTEXT.md`).

## Out of Scope

- Processar CSVs que já estão em `base_1` na largada (backfill).
- Outras pastas, outros prefixos, outros PCs.
- Alterar, mover ou apagar CSVs de origem.
- `output.csv` ou qualquer artefato além de `output.xlsx`.
- Serviço Windows, nuvem, ou watcher em máquina que não seja `DaniGalera`.
- Deduplicar recebível por `id` + número da parcela.
- Duplicar transação no mesmo Id Transação Adquirente.
- Usar `ID Transacao` (id interno) como chave.
- Converter `Data Repasse` em data+hora.
- Escutar evento `modified`.

## Further Notes

- Os dumps atuais usam `;`, ~2999 transações / ~1766 recebíveis; 296 transações e 1 recebível com id vazio devem ser descartados se um desses arquivos **entrar** de novo na pasta.
- Sobreposição de delta é normal: transação reenviada atualiza; recebível reenviado empilha linha.
- Glossário: `CONTEXT.md` na raiz (Transação, Recebível, Id Transação Adquirente, Linha consolidada, Merge por id, Planilha de output).
