Status: ready-for-agent

# 04: Adaptador, largada e os dois watchers

**What to build:** Os dois processos continuam separados, no hostname `DaniGalera`, gravando no mesmo banco um lote de cada vez. Na criação do banco, a pasta é lida uma vez, nesta ordem: CSV de transação do mais antigo ao mais novo, CSV de recebível na mesma ordem, por último o `Recebimentos_MP.xlsx` inteiro. Cada arquivo vira um lote no seam do ticket 01. Reinício com banco já criado não repete essa leitura. O watcher de CSV dispara só quando o arquivo entra na pasta. O watcher de MP dispara em alteração, criação e move. O arquivo só é lido depois que o tamanho estabiliza. CSV de origem e `Recebimentos_MP.xlsx` não são alterados. A planilha é exportada do consolidado vigente depois de cada lote; se o lock estourou, a próxima exportação (o merge seguinte ou ao subir o processo) grava de novo.

**Blocked by:** 02 Banco SQLite, 03 Exportar a planilha de output

- [ ] Hostname diferente de `DaniGalera` encerra sem escrever
- [ ] Prefixos `transacoes_`, `transações_`, `recebiveis_` e `recebíveis_` (case-insensitive, com ou sem acento); CSV com `;` e UTF-8 (BOM opcional)
- [ ] Largada única na ordem do spec; arquivo que já entrou não é reprocessado pelo watcher de CSV
- [ ] Watcher de CSV ignora `modified`; watcher de MP escuta `modified`, `created` e `moved` só de `Recebimentos_MP.xlsx`
- [ ] Ao ver transação ou recebível de um id da Maquinha, o adaptador lê no `Recebimentos_MP.xlsx` as tuplas válidas daquele id, coloca-as no estado como ainda não aplicadas, e o seam aplica o lote e em seguida essas tuplas. O motor não abre arquivo
- [ ] Confirmação nova, depois da criação, cujo id ainda não está em transação nem recebível, vai para a Maquinha
- [ ] Linha nova nascida de CSV fica com confirmação MP vazia
- [ ] Ciclo: ler estado no banco, aplicar o lote, gravar o estado, exportar a planilha
- [ ] Os painéis continuam ligando e desligando cada processo sozinho
- [ ] O caminho antigo (reler `output.xlsx` para decidir o merge, aba `controle`, semear sem aplicar) sai. Watcher, hostname, painel e a leitura única da pasta ficam de checagem manual; a suíte obrigatória continua sendo o seam

## Comments

Spec: `.scratch/consolidado-no-banco/spec.md`. Notas: `consolidado-no-banco-notes/exploration.md`.
