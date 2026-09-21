# Context Map

## Contexts

- [Consolidação](./scripts/CONTEXT.md): dumps CSV e confirmações MP viram linhas na planilha de output
- [Painel](./painel/CONTEXT.md): aplicação desktop que liga e desliga watchers das automações

## Relationships

- **Painel → Consolidação**: o Painel controla o ciclo de vida dos Watchers; não altera dados nem planilhas
- **Painel ↔ scripts/**: lê o manifesto e invoca os módulos `processos` de cada automação declarada
