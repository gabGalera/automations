# Consolidação de transações e recebíveis

Contexto da pasta `base_1`: dumps CSV de transações e recebíveis viram linhas consolidadas em uma planilha de output.

## Language

**Transação**:
Uma venda (PIX, cartão, etc.) exportada nos arquivos `transacoes_` / `transações_`. No domínio, o Id Transação Adquirente de uma transação é único.
_Avoid_: transaction, pedido

**Recebível**:
Uma parcela de liquidação ligada a uma transação, exportada nos arquivos `recebiveis_` / `recebíveis_`. Vários recebíveis podem compartilhar o mesmo Id Transação Adquirente.
_Avoid_: parcela avulsa, boleto, recebimento

**Id Transação Adquirente**:
Identificador da transação no adquirente (`ID Trans. Adquirente`). É a chave de ligação entre transação e recebível. Linha de transação ou de recebível com este id vazio é descartada.
_Avoid_: chave primária, PK, ID Transacao (esse é o id interno)

**Linha consolidada**:
Uma linha da aba `consolidado`: colunas da transação mais colunas do recebível. Pode nascer só com transação, só com recebível, ou com os dois. Cada parcela é uma linha; a mesma parcela pode existir mais de uma vez.
_Avoid_: output.csv, registro mesclado, join row

**Merge por id**:
Quando chega uma transação cujo id já está no `consolidado`, as colunas de transação dessas linhas são substituídas pela nova (inclusive se já estavam preenchidas). Não cria uma segunda transação para o mesmo id. Quando chega um recebível, entra como linha nova; se já existir transação sem recebível, essa linha-esqueleto é preenchida.
_Avoid_: duplicata de transação, ignorar transação já preenchida, deduplicar parcela

**Planilha de output**:
O único artefato que o processo altera: `output.xlsx` na pasta `base_1` (abas `consolidado` e `controle`).
_Avoid_: output.csv, planilha csv
