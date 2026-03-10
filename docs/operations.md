# Operacao

## Fases

1. `python3 run_factory.py check`
2. `python3 run_factory.py new-run --vertical ... --objective ...`
3. `python3 run_factory.py run --run-id <RUN_ID>`
4. aprovar `idea`
5. `python3 run_factory.py run --run-id <RUN_ID>`
6. aprovar `mvp`
7. `python3 run_factory.py run --run-id <RUN_ID>`
8. aprovar `build`
9. `python3 run_factory.py run --run-id <RUN_ID>`

## Checks recomendados

- `python3 -m unittest discover -s tests`
- `python3 run_factory.py check`
- `bash bootstrap/check.sh`

## Ajuste de modelos locais

Se voce ja tem modelos instalados no Ollama, use `bootstrap/env.example` como base e sobrescreva:

- `AI_LAB_RESEARCH_MODEL`
- `AI_LAB_ANALYST_MODEL`
- `AI_LAB_DEV_MODEL`
- `AI_LAB_MARKETING_MODEL`

Isso evita editar o `config/factory.toml` toda vez.
