# Webchat

## Objetivo

No estado final, a stack deve expor um `webchat` para conversar com o orquestrador/chief.

Esse webchat deve permitir:

- pedir novas tarefas
- pedir atualizacoes de andamento
- revisar estado dos workers
- disparar fluxos controlados
- receber respostas consolidadas do `Codex`

## Papel na arquitetura

- a interface fala com o `Codex/chief`
- o `Codex` decide, delega e consolida
- o `LangGraph` coordena os workers locais
- o `Playwright MCP` cobre browser/QA quando necessario

## Capacidades desejadas

- historico de conversa
- status dos runs
- resumo de artifacts relevantes
- aprovacao de gates
- pedidos ad hoc para research/dev/marketing

## Fase de implementacao

O `webchat` entra depois de:

1. `Playwright MCP`
2. `LangGraph` para controle dos workers
3. fortalecimento do `dev/coder worker`
4. validacao dos demais workers sob o grafo
