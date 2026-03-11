# Fase 2

## Objetivo

Sair de `prompt + modelo` e passar para `modelo + tools reais`.

## Estado atual

- `research`: Brave Search + fetch HTTP
- `analyst`: Brave Search + fetch HTTP
- `dev`: snapshot do repo + busca no repo + `git status`
- `marketing`: Brave Search + fetch HTTP + snapshot do repo
- `Codex`: supervisor/orquestrador e browser specialist

## Maturidade por worker

- `research`: pronto para uso inicial
- `analyst`: pronto para uso inicial, ainda precisa validacao pratica dedicada
- `dev/coder`: base pronta, mas ainda nao e um executor forte
- `marketing`: base pronta, mas ainda nao foi validado como worker operacional forte
- `Codex`: pronto como chief of staff; browser real ainda depende de `Playwright MCP`

## Fases pendentes por worker

### `dev/coder`

Fase dedicada de fortalecimento:

- loop de execucao real
- rodar testes, lint e comandos do projeto
- gerar patch e revalidar
- produzir saida tecnica consistente para `build`

### `marketing`

Fase dedicada de validacao:

- rodar um fluxo real de copy/oferta/landing
- validar qualidade da saida com evidencias web
- ajustar templates e ferramentas conforme necessidade

### `analyst`

Fase menor de validacao:

- validar um run dedicado
- confirmar que score/riscos/recomendacao se mantem consistentes
- ajustar apenas se aparecer ruido relevante

## Decisao de escopo

Nesta interacao, o objetivo principal passa a ser `stack pronta para uso`, nao `construcao do produto`.

Por isso:

- o vertical `guincho` fica como fixture de validacao da stack
- o pipeline foi validado ate o gate `idea`
- `spec` e `build` ficam pausados por enquanto
- a prioridade sai de artefatos de produto e vai para browser, runtime e orquestracao

## Runtime

O repo agora usa `tool-agent` como runtime local padrao.

`LangGraph` nao e necessario para o estado funcional atual, mas passa a ser a camada-alvo da arquitetura para controlar todos os workers com mais rigor.

Objetivo dessa proxima fase:

- grafo supervisor para `research`, `analyst`, `dev` e `marketing`
- checkpoints explicitos
- handoffs controlados
- retries e branches mais previsiveis
- estado persistente mais rico entre etapas

## Artifacts

Cada worker tool-enabled gera um artifact adicional por etapa:

- `01-scan.tools.md`
- `04-build.tools.md`

Esses arquivos mostram:

- quais tools rodaram
- o status de cada uma
- quais evidencias reais entraram no contexto do modelo

## Brave Search

Configure:

```bash
export BRAVE_SEARCH_API_KEY="seu-token"
```

Sem isso, os workers de web research entram em modo degradado e registram o skip no `*.tools.md`.

## LangGraph como proxima camada

Quando formos subir para a camada seguinte:

```bash
python3 -m pip install -r bootstrap/phase2-requirements.txt
```

Depois vamos ligar o runtime de workers a um grafo real.

### Escopo esperado do grafo

- `Codex` continua fora do grafo como chief of staff e browser specialist
- `LangGraph` controla os workers locais
- cada worker vira um node com estado, tools, saida estruturada e criterio de handoff
- o `dev/coder` ganha o loop multi-etapa mais rico
- `research`, `analyst` e `marketing` passam a operar com checkpoints mais controlados

## Proximos passos sugeridos

1. Consolidar o `Codex` como browser specialist usando o helper `browser-review`
2. Integrar `Playwright MCP` ao `Codex`
3. Validar navegacao/teste web real em um fluxo simples
4. Introduzir `LangGraph` como camada de controle de todos os workers
5. Fortalecer o `dev/coder worker` como executor forte
6. Adaptar `research`, `analyst` e `marketing` para handoffs/checkpoints controlados
7. Adicionar um `webchat` para conversar com o orquestrador/chief
8. Fechar um checklist final de `stack pronta para uso`

## Ordem recomendada

Se a meta e prontidao do ambiente, a ordem recomendada e:

1. `Playwright MCP`
2. `browser-review` real
3. `LangGraph` para controle dos workers
4. fortalecimento do `dev/coder worker`
5. adaptacao/validacao de `research`, `analyst` e `marketing` sob o grafo
6. `webchat` com o orquestrador/chief
7. checklist operacional final

## Objetivo final desta linha

Stack pronta para:

- conversar com um `chief/orchestrator` por webchat
- delegar tarefas aos workers
- acompanhar estado e progresso
- usar browser/QA real pelo `Codex`
- manter os workers locais sob controle via `LangGraph`
