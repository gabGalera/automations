Status: ready-for-agent

# 03: Exportar a planilha de output

**What to build:** A planilha de output passa a ser só a aba `consolidado`, regravada inteira a partir das linhas do seam. O merge não a relê. Sem aba `controle`, sem segundo nome de arquivo. Se o Excel estiver com o arquivo aberto, a gravação espera cerca de um minuto; se o lock estourar, a falha não cria outro artefato — a próxima exportação grava o consolidado vigente.

**Blocked by:** 01 Seam do motor

- [ ] `output.xlsx` só com a aba `consolidado`, cabeçalho estável do spec, arquivo inteiro a cada exportação
- [ ] `data`, `Data Repasse` e `Data Recibo MP` como data Excel; `hora` como hora Excel; `Confirmacao MP` como número; ids, textos e valores monetários no espírito do CSV continuam texto
- [ ] Retry de lock de cerca de 60 segundos; falha só sinalizada ao chamador; sem `output.csv` e sem arquivo auxiliar permanente
- [ ] A exportação não lê a planilha para decidir o merge
- [ ] Testes que exigem a aba `controle` ou o round-trip antigo deixam de travar a suíte; round-trip de xlsx continua fora da suíte deste spec

## Comments

Spec: `.scratch/consolidado-no-banco/spec.md` (histórias 6–11 e 48, Implementation Decisions). Notas: `consolidado-no-banco-notes/exploration.md`. O caminho do `output.xlsx` continua `dados/base_1`. Quem chama a exportação depois de gravar o banco é o ticket 04.
