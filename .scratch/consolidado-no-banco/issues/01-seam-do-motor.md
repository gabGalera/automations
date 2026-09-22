Status: ready-for-agent

# 01: Seam do motor

**What to build:** Uma função pura que recebe o estado (consolidado, ids da Maquinha, tuplas de confirmação MP ainda não aplicadas) e um lote (`transacao`, `recebivel` ou confirmação MP, dicts com os cabeçalhos reais) e devolve o estado novo. É o único lugar das regras de merge. A largada é essa função em sequência, não uma segunda implementação. Os watchers continuam no caminho atual da planilha até o ticket 04; este ticket não troca a persistência.

**Blocked by:** None (can start immediately)

- [ ] Id vazio descartado nas três pontas; id vira texto estável, sem notação científica
- [ ] Transação nova vira esqueleto (sem `Ultima Atualizacao`, `Data/Hora` partida em `data` e `hora`, confirmação MP vazia); `Status` `Estornado` não cria linha; taxa negativa não cria estorno
- [ ] Segunda transação do mesmo id substitui só colunas de transação em todas as linhas daquele id
- [ ] Parcela nova preenche a primeira vaga sem recebível que não seja estorno; sem vaga, entra em linha nova
- [ ] A mesma parcela (id + número), com valor positivo, substitui só colunas de recebível e preserva a confirmação MP
- [ ] Estorno (confirmação MP negativa) nasce sem parcela e não a recebe depois; a parcela desse id entra em outra linha; a linha de estorno copia as colunas de transação da primeira linha daquele id, se existir
- [ ] Confirmação positiva ocupa a linha sem confirmação de Data Repasse mais cedo; a mesma tupla não reaplica; outra data aplica
- [ ] No mesmo lote, positivos antes dos negativos, cada grupo por data do recibo
- [ ] Id sem transação e sem recebível vai para a Maquinha e a tupla fica pendente
- [ ] Chegada de transação ou recebível desse id tira o id da Maquinha e aplica as tuplas pendentes depois do lote, com a mesma regra de positivo e estorno
- [ ] Três chamadas em sequência (transação, recebível, confirmação MP) produzem o estado final da largada
- [ ] Testes só deste seam, fixtures em memória, sem arquivo, Excel, watcher ou ordem de log

## Comments

Spec: `.scratch/consolidado-no-banco/spec.md`. Notas: o diretório `consolidado-no-banco-notes` fora do repo (exploration.md). ADR 0003 e a história 28 vencem a frase de empilhar recebível repetido no ADR 0002: a mesma parcela substitui.
