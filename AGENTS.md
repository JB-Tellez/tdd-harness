# AGENTS.md

## Setup

Activate the virtual environment before running anything:

```sh
source .venv/bin/activate
```

If `.venv/` is missing, recreate it:

```sh
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Running tests

```sh
pytest
```

## Adding dependencies

```sh
pip install <package> && pip freeze > requirements.txt
```
