# Arquitetura

## Visão geral

O projeto implementa a arquitetura sugerida no `contexto1.md` sem depender de OpenClaw:

- `Codex CLI` atua como Chief of Staff/orquestrador e browser specialist
- `Ollama` executa workers locais por especialidade
- os workers locais usam tools reais na Fase 2
- cada execução vira um `run` com artefatos em disco
- `gates` seguram o avanço até você aprovar a próxima fase

## Papéis

- `research`: coleta dores, concorrentes e integrações
- `analyst`: apoia score de ideias e critérios de viabilidade
- `dev`: transforma o spec em backlog técnico e patches
- `marketing`: gera landing, anúncios e mensagens de aquisição
- `orchestrator`: consolida contexto, decide, revisa, prioriza e assume browser/QA quando necessário

## Tools por worker

- `research`: Brave Search + fetch HTTP
- `analyst`: Brave Search + fetch HTTP
- `dev`: snapshot do repo + busca no repo + `git status`
- `marketing`: Brave Search + fetch HTTP + snapshot do repo

## Prontidao atual

- `research`: pronto para uso inicial
- `analyst`: pronto para uso inicial, pendente de validacao dedicada
- `dev/coder`: pendente de fase de fortalecimento como executor forte
- `marketing`: pendente de fase de validacao/ajuste operacional
- `Codex`: pronto como supervisor; browser real depende de `Playwright MCP`

## LangGraph

O runtime atual de tools funciona sem dependência externa nova.
`LangGraph` entra como próxima camada opcional para:

- supervisor graph
- checkpoints mais ricos
- handoffs explícitos entre subagentes
- tool routing mais sofisticado

## Fases

1. `scan`
2. `score`
3. `spec`
4. `build`
5. `marketing`

## Gates

- `idea`: valida a ideia escolhida após o score
- `mvp`: valida o escopo mínimo antes de build
- `build`: libera execução da etapa de implementação

## Estratégia de uso

- Rodar um `run` por vertical/problema
- Manter saídas versionadas por timestamp
- Usar o Codex para tarefas de alta alavancagem
- Usar workers locais para execução recorrente e barata
