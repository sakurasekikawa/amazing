VENV        ?= .venv
# 仮想環境があればそれを使う（make install の後は自動で切り替わる）
PYTHON      ?= $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)
CONFIG      ?= config.txt
AMAZING     ?= a_maze_ing.py
# GUI 用: 42 配布の mlx wheel のパス（例: make install-mlx MLX_WHL=path/to/mlx-2.2-py3-none-any.whl）
MLX_WHL     ?=

# Runtime: python-dotenv (config.txt reader)
# Dev tools: flake8, mypy, pytest, build
PIP_PKGS = python-dotenv flake8 mypy pytest build

.PHONY: install install-mlx run run-ascii debug clean lint lint-strict test check build

# sudo 不要。仮想環境 .venv を作って pip で入れる（校舎の PC でも動く）
install:
	python3 -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install $(PIP_PKGS)

# 任意: GUI (MLX)。wheel は 42 配布の mlx-2.2-py3-none-any.whl
install-mlx:
	@test -n "$(MLX_WHL)" || { echo "usage: make install-mlx MLX_WHL=<mlx-2.2-py3-none-any.whl>"; exit 1; }
	$(VENV)/bin/python -m pip install $(MLX_WHL)

run:
	$(PYTHON) $(AMAZING) $(CONFIG)

run-ascii:
	$(PYTHON) $(AMAZING) $(CONFIG) --ascii

debug:
	$(PYTHON) -m pdb $(AMAZING) $(CONFIG)

# flake8 and mypy settings live in setup.cfg
lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy .

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache build dist *.egg-info

# Additional
test:
	$(PYTHON) -m pytest tests/ -q

# Run before submitting
check: lint test

# Offline: make build
build:
	$(PYTHON) -m build --outdir .
