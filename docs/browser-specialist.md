# Browser Specialist

## Papel do Codex

Na Fase 2, o `Codex` fica como:

- chief of staff
- gatekeeper de qualidade
- browser specialist para navegacao, verificacao e QA web

## Playwright MCP

O caminho recomendado para dar browser real ao Codex e conectar o Playwright MCP.

Comando recomendado pela documentacao oficial do Playwright MCP para Codex:

```bash
codex mcp add playwright npx "@playwright/mcp@latest"
```

Depois:

```bash
codex mcp list
```

## Exemplos de uso

Depois de configurar o MCP, use prompts como:

```text
Abra https://meusite.com, valide a home mobile e desktop, teste o CTA principal e me entregue um relatorio com bugs, riscos e melhorias.
```

```text
Navegue pelo fluxo de login em https://meusite.com/login, tente credenciais invalidas, valide mensagens de erro e proponha um patch se houver falhas.
```

Ou pelo helper do repo:

```bash
python3 run_factory.py browser-review --url https://meusite.com/login --task "Validar login invalido e mensagens de erro"
```

## Observacao

Neste repo, os workers locais nao dependem do browser para operar.
O browser fica no `Codex`, o que preserva o papel dele como supervisor/especialista em tarefas de maior valor.
