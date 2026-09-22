Status: ready-for-agent

# Consolidado no banco, planilha só de leitura (`base_1`)

## Problem Statement

O merge por id grava direto na planilha de output. Com o Excel aberto, o lock segura a lista. A aba `controle` guarda anotação de processo no meio do que o financeiro lê. A mesma parcela exportada de novo empilha outra linha. Confirmação MP de id que não está em transação nem em recebível não tem para onde ir sem sujar o consolidado, e o histórico do `Recebimentos_MP.xlsx` ficou marcado como visto sem entrar na lista.

## Solution

Neste PC, o processo altera um banco local, fora do Drive. O consolidado nasce uma vez do merge dos arquivos que já estão na pasta. Id do Mercado Pago que ainda não tem transação nem recebível fica na Maquinha. Quando a venda chega, o id sai da Maquinha e as confirmações entram no consolidado. A planilha de output é só a aba `consolidado`, regravada a partir dessa lista. O merge não a relê.

## User Stories

1. As an operador neste PC, I want o merge gravando o consolidado num banco local, fora do Drive, so that o Excel aberto não segura a lista.
2. As an operador, I want o processo recusando rodar se o hostname não for `DaniGalera`, so that outro PC com o mesmo Drive não escreva.
3. As an operador, I want os dois processos de hoje (CSV e `Recebimentos_MP.xlsx`) continuando separados, so that eu ligo e desligo cada um como já faço.
4. As an operador, I want os dois processos gravando no mesmo banco, um lote de cada vez, so that um não apaga o que o outro acabou de aplicar.
5. As an operador, I want o banco guardando o consolidado e as chegadas na ordem em que o merge as viu, so that a lista possa ser refeita.
6. As an operador, I want a planilha de output gerada a partir do consolidado, só com a aba `consolidado`, so that eu continue lendo no Excel.
7. As an operador, I want a aba `controle` fora da planilha, so that tupla já vista e hostname não apareçam no arquivo que eu abro.
8. As an operador, I want cada merge regravando a planilha inteira, so that ela seja o consolidado vigente e não um delta.
9. As an operador, I want o retry de lock de cerca de um minuto se o Excel estiver com o arquivo aberto, so that a gravação espere o arquivo fechar.
10. As an operador, I want, se o lock estourar, a próxima exportação (o merge seguinte ou ao subir o processo) gravando o consolidado vigente, so that linha não se perca.
11. As an operador, I want o merge não relendo a planilha, so that a lista mandante seja o banco.
12. As an operador, I want os CSV de origem e o `Recebimentos_MP.xlsx` intactos, so that o processo só leia esses arquivos.
13. As an operador, I want o consolidado nascendo do merge dos arquivos que já estão na pasta, so that a lista não seja uma cópia da planilha anterior.
14. As an operador, I want essa leitura da pasta uma vez só, na criação do banco, so that reiniciar o processo não refaça a lista.
15. As an operador, I want, depois da criação, só chegada nova, so that arquivo que já entrou não seja reprocessado pelo watcher.
16. As an operador, I want a largada na ordem: CSV de transação do mais antigo para o mais novo, depois CSV de recebível na mesma ordem, por último o `Recebimentos_MP.xlsx` inteiro, so that a parcela já esteja na lista quando a confirmação procurar Data Repasse.
17. As an operador, I want prefixos `transacoes_`, `transações_`, `recebiveis_` e `recebíveis_` (case-insensitive, com ou sem acento), so that o nome real do exportador não quebre a largada nem o watcher.
18. As an operador, I want CSV com delimitador `;` e UTF-8 (BOM opcional), so that os dumps atuais sejam lidos.
19. As a leitor da planilha, I want linha sem Id Transação Adquirente descartada, nas três pontas, so that linha sem ligação não entre.
20. As a leitor da planilha, I want o Id Transação Adquirente como texto estável, sem notação científica, so that a ligação não quebre.
21. As a leitor da planilha, I want o ID Transacao só como coluna, so that o id interno não ligue transação, recebível e confirmação MP.
22. As a leitor da planilha, I want uma transação por Id Transação Adquirente, so that reenvio substitua as colunas de transação em todas as linhas daquele id e não crie segunda venda.
23. As a leitor da planilha, I want transação nova sem recebível ainda assim no consolidado, so that a venda não espere a parcela.
24. As a leitor da planilha, I want `Ultima Atualizacao` de fora e `Data/Hora` partida em `data` e `hora`, so that o consolidado não carregue o timestamp do exportador e o dia filtre separado da hora.
25. As a leitor da planilha, I want `Status` `Estornado` e `Total Reembolsado` só como colunas da transação, so that estorno de venda não vire linha nova.
26. As a leitor da planilha, I want taxa negativa continuando taxa, so that `-0,16` ou `-1.495,30` não virem estorno.
27. As a leitor da planilha, I want cada parcela como uma linha, identificada por Id Transação Adquirente + número da parcela, so that as doze parcelas de uma venda caibam uma a uma.
28. As a leitor da planilha, I want outra chegada da mesma parcela, com valor positivo, substituindo só as colunas de recebível, so that o dia 8 com o mesmo número não empilhe linha e não apague a confirmação MP já preenchida.
29. As a leitor da planilha, I want parcela que ainda não existe preenchendo a primeira linha daquele id sem recebível e que não seja estorno, so that esqueleto de transação ou confirmação positiva ainda nua receba a parcela.
30. As a leitor da planilha, I want, se não houver essa vaga, a parcela em linha nova, so that a segunda parcela não sobrescreva a primeira.
31. As a leitor da planilha, I want colunas de recebível `Parcela Recebivel`, `Total Parcelas`, `taxa % cliente`, `taxa valor cliente`, `Valor Repasse` e `Data Repasse`, so that a taxa da liquidação não colida com a taxa da transação.
32. As a leitor da planilha, I want `Data Repasse` como data única, so that a liquidação não seja partida em data e hora.
33. As a leitor da planilha, I want confirmação MP só com as três colunas válidas: id não vazio, valor numérico diferente de zero, data interpretável, so that rascunho, zero e data ilegível não entrem.
34. As a leitor da planilha, I want a mesma tupla (id + valor + data do recibo) aplicada no máximo uma vez, so that salvar o arquivo de novo não duplique o fato.
35. As a leitor da planilha, I want outra data do mesmo id como outra tupla, so that `188,33` em março e `188,33` em abril sejam duas confirmações.
36. As a leitor da planilha, I want confirmação positiva na primeira linha daquele id sem confirmação, na ordem de Data Repasse, so that o recibo ligue na parcela pela data de liquidação e não pelo número inventado a partir da data do recibo.
37. As a leitor da planilha, I want, sem essa vaga, a confirmação positiva em linha nova, so that recibo a mais não sobrescreva parcela que já tem confirmação.
38. As a leitor da planilha, I want estorno só na confirmação MP negativa, em linha nova, sem parcela, so that `-25660,54` não seja uma parcela.
39. As a leitor da planilha, I want a linha de estorno sem receber parcela depois, so that a parcela 1 do mesmo id entre em outra linha.
40. As a leitor da planilha, I want a linha de estorno copiando as colunas de transação da primeira linha daquele id, se existir, so that o estorno herde a venda sem fingir parcela.
41. As a leitor da planilha, I want, num mesmo lote de confirmações, positivos antes dos negativos, cada grupo por data do recibo, so that o estorno não ocupe o lugar do crédito do mesmo save.
42. As an operador, I want id que está no `Recebimentos_MP.xlsx` e ainda não está em transação nem em recebível na Maquinha, so that esses ids não entrem no consolidado.
43. As an operador, I want a Maquinha guardando esse id, e o valor e a data continuando no `Recebimentos_MP.xlsx`, so that a tabela não duplique o recibo.
44. As an operador, I want tupla de id na Maquinha sem contar como já aplicada, so that ela ainda possa entrar quando a venda chegar.
45. As a leitor da planilha, I want, ao chegar transação ou recebível de um id da Maquinha, o id saindo da Maquinha e as tuplas dele entrando no consolidado, so that o recibo que esperou a venda apareça na lista.
46. As a leitor da planilha, I want essas tuplas entrando depois do lote de transação ou recebível que trouxe o id, com a mesma regra de positivo e estorno, so that a parcela exista antes do recibo procurar Data Repasse.
47. As an operador, I want chegada nova de confirmação, depois da criação, cujo id ainda não está em transação nem recebível, indo para a Maquinha, so that o dia a dia use a mesma regra da largada.
48. As a leitor da planilha, I want `data`, `Data Repasse` e `Data Recibo MP` como data nativa do Excel, `hora` como hora nativa, `Confirmacao MP` como número, e o restante no espírito do CSV (ids e valores como texto), so that filtro e soma funcionem sem o Excel comer dígito.
49. As an operador, I want linha nova nascida de CSV com confirmação MP vazia, so that venda ou parcela recém-chegada não invente recibo.
50. As an operador, I want o watcher de CSV disparando só quando o arquivo entra na pasta, so that `modified` do Drive não reprocesse o mesmo CSV.
51. As an operador, I want o watcher de MP disparando em alteração, criação e move do `Recebimentos_MP.xlsx`, so that linha nova no mesmo arquivo entre.
52. As an operador, I want o arquivo só lido depois que o tamanho estabilizar, so that download pela metade não vire linha pela metade.

## Implementation Decisions

- O banco é SQLite, neste PC, fora da pasta do Drive observada pelos watchers. O Drive continua sendo a origem dos CSV e do `Recebimentos_MP.xlsx` e o destino da planilha de output.
- Três camadas, como hoje: motor puro, persistência, adaptador de pasta. Os dois processos continuam. A persistência deixa de ser a planilha e passa a ser o banco. A planilha é exportação.
- Seam único do motor: uma função que recebe o estado (consolidado, ids da Maquinha, tuplas de confirmação MP ainda não aplicadas) e um lote (`transacao`, `recebivel` ou confirmação MP, dicts com os cabeçalhos reais) e devolve o estado novo. A largada é essa função chamada na ordem dos arquivos, não uma segunda implementação do merge.
- O adaptador, ao ver transação ou recebível de um id da Maquinha, lê no `Recebimentos_MP.xlsx` as tuplas válidas daquele id, coloca-as no estado como ainda não aplicadas, aplica o lote do CSV e em seguida essas tuplas. O motor não abre arquivo.
- Tupla aplicada sai do conjunto de pendentes e não entra de novo. Tupla na Maquinha permanece pendente.
- Cabeçalho estável do consolidado: colunas de transação (sem `Ultima Atualizacao`, com `data` e `hora` no lugar de `Data/Hora`), colunas de recebível renomeadas, `Confirmacao MP`, `Data Recibo MP`. A ordem das linhas é a ordem das vagas.
- Maquinha persiste o Id Transação Adquirente, um id por linha. Não persiste valor nem data.
- Chegadas de transação e de recebível ficam na ordem, para refazer o consolidado. Recebível é um por id + número da parcela; chegada nova da mesma parcela substitui. Transação vigente é uma por id.
- Ciclo de escrita: ler o estado no banco, aplicar o lote, gravar o estado, exportar a planilha. Retry de lock cerca de 60 segundos. Sem segundo nome de output. Sem reler a planilha para decidir o merge.
- A criação do banco, se ainda não houve, faz a leitura única da pasta antes dos watchers passarem a ignorar o que já estava lá. Reinício com banco já criado não repete essa leitura.
- Exportação: `data`, `Data Repasse` e `Data Recibo MP` como data Excel; `hora` como hora Excel; `Confirmacao MP` como número; ids, textos e valores monetários das colunas que hoje são texto no CSV continuam texto.

## Testing Decisions

- Bom teste: só o seam do motor. Fixtures em memória, dicts com os cabeçalhos reais. Sem arquivo, sem Excel, sem watcher, sem assertar ordem de log.
- A largada entra no mesmo seam: três chamadas em sequência (lote de transação, lote de recebível, lote de confirmação MP) e o estado final.
- Casos mínimos: id vazio descartado; transação nova vira esqueleto; segunda transação do mesmo id substitui só colunas de transação; `Status` `Estornado` não cria linha; taxa negativa não cria estorno; parcela nova preenche a primeira vaga sem recebível que não seja estorno; a mesma parcela substitui colunas de recebível e preserva confirmação MP; sem vaga, parcela entra em linha nova; estorno nasce sem parcela e não a recebe depois; a parcela desse id entra em outra linha; confirmação positiva ocupa a linha sem confirmação de Data Repasse mais cedo; a mesma tupla não reaplica; outra data aplica; id sem transação e sem recebível vai para a Maquinha e a tupla fica pendente; chegada de transação ou recebível desse id tira o id da Maquinha e aplica as tuplas pendentes depois do lote.
- Prior art: os testes do motor de CSV e do motor de confirmação MP, mesmo estilo de fixture dict. Esse seam passa a ser o lugar dessas regras. Round-trip de xlsx e de SQLite fica fora da suíte deste spec.
- Watcher, hostname, painel e a leitura única da pasta no disco: checagem manual neste PC.

## Out of Scope

- Copiar o `output.xlsx` atual como consolidado inicial.
- Religa a pasta inteira toda vez que o processo sobe.
- Aba `controle` na planilha de output.
- Numerar parcela pela ordem da Data Recibo MP.
- Tratar taxa negativa, `Total Reembolsado` ou `Status` `Estornado` como estorno.
- Ligar parcela pelo ID Transacao.
- Empilhar a mesma parcela de novo.
- Gravar valor e data da confirmação na Maquinha.
- Um processo só no lugar dos dois.
- Outro PC lendo o banco.
- Banco na pasta do Drive.
- Planilha nova de parcelas.
- Deduplicar pela parcela quando o valor muda de sinal: valor negativo de confirmação MP é estorno; valor positivo da mesma parcela substitui.

## Further Notes

- Glossário em `scripts/CONTEXT.md`. Decisões em `scripts/docs/adr/0001` a `0006`.
- Uma carga já feita da Maquinha, a partir do backup do `Recebimentos_MP.xlsx` (o arquivo ao vivo estava aberto), tem 8491 ids. A criação do banco deve reler o arquivo ao vivo, não esse backup.
- No backup, o mesmo id com o mesmo valor em meses seguidos é parcela diferente porque a data muda. Confirmação no mesmo dia com valor negativo e uma sobra positiva (id `156715476638`: `191,05`, depois `-198` e `10,88`) segue a regra atual: a positiva ocupa vaga por Data Repasse, a negativa é estorno. Não vira numeração de parcela.
