PYTHON      ?= python3
CONFIG      ?= config.txt
AMAZING     ?= a_maze_ing.py
APT         ?= sudo apt-get
BUILD_FLAGS ?=

# Runtime: python-dotenv (config.txt reader)
# Dev tools: flake8, mypy, pytest, build
APT_PKGS = python3-dotenv \
           python3-flake8 python3-mypy python3-pytest \
           python3-build python3-setuptools python3-wheel

.PHONY: install install-pip install-check run debug clean lint lint-strict test check build

install:
	$(APT) update
	$(APT) install -y $(APT_PKGS)

run:
	$(PYTHON) $(AMAZING) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(AMAZING) $(CONFIG)

# flake8 and mypy settings live in setup.cfg
lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy .

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

test:
	$(PYTHON) -m pytest tests/ -q

# Run before submitting
check: lint test

# Offline: make build BUILD_FLAGS=--no-isolation
build:
	$(PYTHON) -m build $(BUILD_FLAGS) --outdir .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache build dist *.egg-info
