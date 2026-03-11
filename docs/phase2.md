# Fase 2

## Objetivo

Sair de `prompt + modelo` e passar para `modelo + tools reais`.

## Estado atual

- `research`: Brave Search + fetch HTTP
- `analyst`: Brave Search + fetch HTTP
- `dev`: snapshot do repo + busca no repo + `git status`
- `marketing`: Brave Search + fetch HTTP + snapshot do repo
- `Codex`: supervisor/orquestrador e browser specialist

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
