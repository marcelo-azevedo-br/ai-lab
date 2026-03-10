# Arquitetura

## Visão geral

O projeto implementa a arquitetura sugerida no `contexto1.md` sem depender de OpenClaw:

- `Codex CLI` atua como Chief of Staff/orquestrador
- `Ollama` executa workers locais por especialidade
- cada execução vira um `run` com artefatos em disco
- `gates` seguram o avanço até você aprovar a próxima fase

## Papéis

- `research`: coleta dores, concorrentes e integrações
- `analyst`: apoia score de ideias e critérios de viabilidade
- `dev`: transforma o spec em backlog técnico e patches
- `marketing`: gera landing, anúncios e mensagens de aquisição
- `orchestrator`: consolida contexto, decide, revisa e prioriza

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
