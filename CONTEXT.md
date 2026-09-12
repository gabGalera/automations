# Consolidação de transações e recebíveis

Contexto da pasta `base_1`: dumps CSV de transações e recebíveis, e confirmações MP, viram linhas consolidadas em uma planilha de output.

## Language

**Transação**:
Uma venda (PIX, cartão, etc.) exportada nos arquivos `transacoes_` / `transações_`. No domínio, o Id Transação Adquirente de uma transação é único.
_Avoid_: transaction, pedido

**Recebível**:
Uma parcela de liquidação ligada a uma transação, exportada nos arquivos `recebiveis_` / `recebíveis_`. Vários recebíveis podem compartilhar o mesmo Id Transação Adquirente.
_Avoid_: parcela avulsa, boleto, recebimento

**Id Transação Adquirente**:
Identificador da transação no adquirente (`ID Trans. Adquirente`). É a chave de ligação entre transação, recebível e confirmação MP. Linha de transação, recebível ou confirmação MP com este id vazio é descartada.
_Avoid_: chave primária, PK, ID Transacao (esse é o id interno)

**Confirmação MP**:
Um valor de crédito (positivo) ou estorno (negativo) do Mercado Pago, com data de recibo (`Data Recibo MP`), no arquivo `Recebimentos_MP.xlsx`. Só existe como fato se as três colunas da linha (`ID Trans. Adquirente`, `Confirmacao MP`, `Data Recibo MP`) estão preenchidas e válidas: id não vazio (texto estável, sem notação científica), valor numérico diferente de zero, data interpretável (`DD-MM-YYYY` ou datetime). Não é um recebível.
_Avoid_: recebimento, Recebimentos_MP (o arquivo), parcela MP

**Tupla de confirmação MP**:
A identidade de uma confirmação MP: Id Transação Adquirente + valor de `Confirmacao MP` + `Data Recibo MP`. A mesma tupla é o mesmo fato.
_Avoid_: linha do Excel, PK, hash do arquivo

**Linha consolidada**:
Uma linha da aba `consolidado`: colunas da transação, do recebível e da confirmação MP. Pode nascer só com transação, só com recebível, só com confirmação MP, ou com combinações. Cada parcela é uma linha; a mesma parcela pode existir mais de uma vez. Estorno MP nasce como linha nova sem recebível; depois pode ganhar colunas de recebível sem deixar de ser a mesma linha.
_Avoid_: output.csv, registro mesclado, join row

**Merge por id**:
Quando chega uma transação cujo id já está no `consolidado`, só as colunas de transação dessas linhas são substituídas pela nova (inclusive se já estavam preenchidas). Não cria uma segunda transação para o mesmo id. Quando chega um recebível, preenche a primeira linha daquele id ainda sem recebível na ordem da aba (esqueleto de transação ou estorno MP), só as colunas de recebível; o resto da linha não muda. Se não houver essa vaga, o recebível entra como linha nova.
_Avoid_: duplicata de transação, ignorar transação já preenchida, deduplicar parcela, recebível apagar confirmação MP

**Planilha de output**:
O único artefato que o processo altera: `output.xlsx` na pasta `base_1` (abas `consolidado` e `controle`).
_Avoid_: output.csv, planilha csv
