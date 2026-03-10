# AI Lab

Arquitetura híbrida para uma "AI SaaS Factory" com:

- `Codex CLI` como orquestrador cloud via sua assinatura ChatGPT Plus
- `Ollama` como camada de workers locais
- pipeline versionado com `runs`, `gates` de aprovação e artefatos auditáveis

## Estrutura

- `bootstrap/`: setup e checks do ambiente
- `config/`: configuração versionada da fábrica
- `factory/agents/`: definição dos papéis dos agentes
- `factory/prompts/`: prompts versionados por etapa
- `factory/runs/`: saídas por execução
- `products/`: produtos gerados/evoluídos pela fábrica
- `src/ai_lab/`: motor da orquestração
- `tests/`: checks locais sem dependências externas

## Fluxo

1. Criar um `run`
2. Executar `scan -> score -> spec -> build -> marketing`
3. Travar a execução em `gates` de aprovação
4. Usar o `Codex CLI` para decisões e revisão final
5. Usar `Ollama` para workers locais especializados

## Comandos

```bash
python3 run_factory.py check
python3 run_factory.py new-run --vertical guincho --objective "Automacao de atendimento via WhatsApp"
python3 run_factory.py run --run-id <RUN_ID> --through score
python3 run_factory.py approve --run-id <RUN_ID> --gate idea
python3 run_factory.py run --run-id <RUN_ID> --through marketing
```

## Se voce ja tem modelo Ollama instalado

Voce nao precisa baixar exatamente os modelos sugeridos no `factory.toml`.
Pode sobrescrever o mapeamento dos workers via ambiente:

```bash
export AI_LAB_RESEARCH_MODEL="seu-modelo"
export AI_LAB_ANALYST_MODEL="seu-modelo"
export AI_LAB_DEV_MODEL="seu-modelo"
export AI_LAB_MARKETING_MODEL="seu-modelo"
```

Ou copie o exemplo:

```bash
cp bootstrap/env.example .env.local
```

Depois ajuste os valores e exporte no shell.

## Observações

- Os scripts de bootstrap instalam e baixam dependências, mas eu não os executei automaticamente.
- A integração com `codex` e `ollama` usa shell/CLI para manter o projeto leve e reproduzível.
- Os `runs` são ignorados no Git, exceto pelo placeholder do diretório.
