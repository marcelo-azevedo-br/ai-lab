# Fase 2

## Objetivo

Sair de `prompt + modelo` e passar para `modelo + tools reais`.

## Estado atual

- `research`: Brave Search + fetch HTTP
- `analyst`: Brave Search + fetch HTTP
- `dev`: snapshot do repo + busca no repo + `git status`
- `marketing`: Brave Search + fetch HTTP + snapshot do repo
- `Codex`: supervisor/orquestrador e browser specialist

## Decisao de escopo

Nesta interacao, o objetivo principal passa a ser `stack pronta para uso`, nao `construcao do produto`.

Por isso:

- o vertical `guincho` fica como fixture de validacao da stack
- o pipeline foi validado ate o gate `idea`
- `spec` e `build` ficam pausados por enquanto
- a prioridade sai de artefatos de produto e vai para browser, runtime e orquestracao

## Runtime

O repo agora usa `tool-agent` como runtime local padrao.

`LangGraph` ainda nao e obrigatorio para a execucao atual.
Ele entra como proxima camada opcional para workflows mais sofisticados, checkpoints mais ricos e subagentes composicionais.

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

## LangGraph opcional

Quando voce quiser subir para a camada seguinte:

```bash
python3 -m pip install -r bootstrap/phase2-requirements.txt
```

Depois podemos ligar o runtime de workers a um grafo real.

## Proximos passos sugeridos

1. Consolidar o `Codex` como browser specialist usando o helper `browser-review`
2. Integrar `Playwright MCP` ao `Codex`
3. Validar navegacao/teste web real em um fluxo simples
4. Decidir se `LangGraph` entra agora ou fica como camada opcional
5. Fechar um checklist final de `stack pronta para uso`

## Ordem recomendada

Se a meta e prontidao do ambiente, a ordem recomendada e:

1. `Playwright MCP`
2. `browser-review` real
3. checklist operacional final
4. `LangGraph`, se ainda fizer sentido
