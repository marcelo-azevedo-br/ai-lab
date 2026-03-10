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

## Pull do Ollama sem saturar a rede

No WSL, prefira:

- `sudo bash bootstrap/pull_model_limited.sh --rate 20mbit qwen2.5:7b`

Se ainda pesar para os apps do Windows, reduza para:

- `15mbit`
- `10mbit`

Se o `ollama pull` mostrar velocidade muito acima do limite escolhido, o shaping estava no caminho errado.
O helper atual limita o trafego de entrada do WSL com `ifb`, que e o que importa para downloads.

## Ajuste de modelos locais

Se voce ja tem modelos instalados no Ollama, use `bootstrap/env.example` como base e sobrescreva:

- `AI_LAB_RESEARCH_MODEL`
- `AI_LAB_ANALYST_MODEL`
- `AI_LAB_DEV_MODEL`
- `AI_LAB_MARKETING_MODEL`

Isso evita editar o `config/factory.toml` toda vez.
