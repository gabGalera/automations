Status: completed

# 02: Banco SQLite

**What to build:** O estado do seam passa a viver num SQLite neste PC, fora da pasta do Drive observada e fora do OneDrive. Os dois processos, mais tarde, leem e gravam o mesmo arquivo, um lote de cada vez. Este ticket é a persistência: abrir o banco, ler o estado, gravar o estado novo, guardar chegadas para refazer o consolidado. Não exporta a planilha e não observa a pasta.

**Blocked by:** 01 Seam do motor

- [x] Arquivo em `%LOCALAPPDATA%\automacoes\base_1\consolidado.sqlite`, não em `dados/base_1` e não no repositório OneDrive
- [x] Persistidos: consolidado na ordem das vagas, ids da Maquinha (só o id), tuplas pendentes, tuplas já aplicadas, chegadas
- [x] Transação vigente é uma por id; recebível é um por id + número da parcela; chegada nova da mesma parcela substitui o recebível guardado
- [x] Chegadas ficam na ordem em que o merge as viu, o bastante para refazer o consolidado chamando o seam
- [x] Gravação de um lote é uma transação: quem escreve não apaga o lote que o outro processo acabou de aplicar
- [x] Banco já criado não implica reler a pasta; criação versus reabertura fica distinguível para o ticket 04
- [x] Round-trip de SQLite fica fora da suíte; o seam do ticket 01 continua sendo o teste

## Comments

Spec: `.scratch/consolidado-no-banco/spec.md` (Implementation Decisions, histórias 1, 4, 5, 14, 43). Notas: `consolidado-no-banco-notes/exploration.md`. Não usar o `dados/base_1/consolidado.sqlite` que já está na pasta.
