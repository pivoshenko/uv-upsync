format:
  find src -type f -name '*.py' | xargs uv run pyupgrade --py313-plus
  find tests -type f -name '*.py' | xargs uv run pyupgrade --py313-plus
  uv run ruff format .

lint:
  uv run ty check .
  uv run ruff check .

test:
  uv run pytest .

update:
  uv lock --upgrade
  uvx uv-upsync --exclude click --exclude tomlkit

demo:
  uv tool install --from . uv-upsync --force
  vhs assets/demo.tape
