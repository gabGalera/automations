# Consolidação de transações e recebíveis

Contexto da pasta `base_1`: dumps CSV de transações e recebíveis, e confirmações MP, viram linhas consolidadas. A planilha de output é a leitura desse consolidado.

## Language

**Transação**:
Uma venda (PIX, cartão, etc.) exportada nos arquivos `transacoes_` / `transações_`. No domínio, o Id Transação Adquirente de uma transação é único.
_Avoid_: transaction, pedido

**Recebível**:
Uma parcela de liquidação exportada nos arquivos `recebiveis_` / `recebíveis_`. A identidade é Id Transação Adquirente + número da parcela. Várias parcelas (1, 2, 3…) podem compartilhar o mesmo Id Transação Adquirente. Outra chegada da mesma parcela, com valor positivo, substitui essa parcela.
_Avoid_: parcela avulsa, boleto, recebimento, ID Transacao (o id interno não liga a parcela)

**Id Transação Adquirente**:
Identificador da transação no adquirente (`ID Trans. Adquirente`). É a chave de ligação entre transação, recebível e confirmação MP. Linha de transação, recebível ou confirmação MP com este id vazio é descartada.
_Avoid_: chave primária, PK, ID Transacao (esse é o id interno)

**Confirmação MP**:
Um valor de crédito (positivo) ou estorno (negativo) do Mercado Pago, com data de recibo (`Data Recibo MP`), no arquivo `Recebimentos_MP.xlsx`. Só existe como fato se as três colunas da linha (`ID Trans. Adquirente`, `Confirmacao MP`, `Data Recibo MP`) estão preenchidas e válidas: id não vazio (texto estável, sem notação científica), valor numérico diferente de zero, data interpretável (`DD-MM-YYYY` ou datetime). Não é um recebível. Taxa negativa e `Status` `Estornado` não são estorno.
_Avoid_: recebimento, Recebimentos_MP (o arquivo), parcela MP, taxa, Total Reembolsado

**Tupla de confirmação MP**:
A identidade de uma confirmação MP: Id Transação Adquirente + valor de `Confirmacao MP` + `Data Recibo MP`. A mesma tupla não entra de novo. Outra data é outra tupla. Enquanto o id está na Maquinha, a tupla não entra no consolidado. Quando o id sai, ela entra.
_Avoid_: linha do Excel, PK, hash do arquivo, aba controle

**Maquinha**:
O Id Transação Adquirente que está no `Recebimentos_MP.xlsx` e ainda não está em transação nem em recebível. Quando uma transação ou um recebível desse id chega, o id sai da Maquinha e as confirmações entram no consolidado.
_Avoid_: consolidado, órfão, parcela

**Linha consolidada**:
Uma linha do consolidado: colunas da transação, do recebível e da confirmação MP. Pode nascer só com transação, só com recebível, só com confirmação MP, ou com combinações. Cada parcela é uma linha. Estorno MP nasce como linha nova sem recebível e não recebe parcela. A parcela desse id entra em outra linha.
_Avoid_: output.csv, registro mesclado, join row, linha da planilha

**Consolidado**:
A lista de linhas consolidadas, na ordem em que o merge por id as deixou. É o conteúdo da aba `consolidado` do `output.xlsx`. Nasce do merge dos arquivos que já estão na pasta, não de uma cópia da planilha anterior.
_Avoid_: join, cópia do output.xlsx

**Chegada**:
Uma transação, um recebível ou uma confirmação MP que o merge viu, na ordem em que viu. Nova chegada da mesma parcela substitui esse recebível. As chegadas refazem o consolidado.
_Avoid_: log, evento, join

**Merge por id**:
Quando chega uma transação cujo id já está no consolidado, só as colunas de transação dessas linhas são substituídas pela nova (inclusive se já estavam preenchidas). Não cria uma segunda transação para o mesmo id. Quando chega um recebível cuja parcela já está no consolidado, só as colunas de recebível dessa linha são substituídas. Quando a parcela ainda não existe, preenche a primeira linha daquele id ainda sem recebível e que não seja estorno, na ordem do consolidado, só as colunas de recebível; o resto da linha não muda. Se não houver essa vaga, o recebível entra como linha nova. A linha de estorno não recebe parcela. Confirmação MP positiva ocupa a primeira linha daquele id sem confirmação, na ordem de Data Repasse.
_Avoid_: duplicata de transação, ignorar transação já preenchida, empilhar a mesma parcela, recebível apagar confirmação MP, estorno receber parcela, numerar parcela pela data do recibo

**Planilha de output**:
A leitura do consolidado, em `output.xlsx` na pasta `base_1`, só com a aba `consolidado`. O merge não a relê.
_Avoid_: output.csv, planilha csv, estado do merge, aba controle
