APP_NAME = telegram_assistant

.PHONY: help build run logs stop down clean-pyc clean-build clean ruff_check ruff_fix ruff_format diff test test-cov test-docker

help:
	@echo "================= Usage ================="
	@echo "make build        : Build docker images"
	@echo "make run          : Start app + postgres in background"
	@echo "make logs         : Follow app logs"
	@echo "make stop         : Stop running compose services"
	@echo "make down         : Stop and remove services/volumes"
	@echo "make clean        : Remove local build/test artifacts"
	@echo "make ruff_check   : Run lint checks"
	@echo "make ruff_fix     : Auto-fix lint issues"
	@echo "make ruff_format  : Format with ruff"
	@echo "make test         : Run tests locally"
	@echo "make test-cov     : Run tests with coverage locally"
	@echo "make test-docker  : Run tests in Docker"

build:
	@docker compose build

test:
	@PYTHONPATH=. pytest tests

test-cov:
	@PYTHONPATH=. pytest tests --cov=src

test-docker: build
	@docker compose run --rm binance_delisting pytest tests

run: build
	@docker compose up -d

logs:
	@docker compose logs -f $(APP_NAME)

stop:
	@docker compose stop

down:
	@docker compose down --remove-orphans --volumes

clean-pyc:
	find . -name '*.pyc' -exec rm -rf {} +
	find . -name '*.pyo' -exec rm -rf {} +

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean: clean-build clean-pyc
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -f .coverage

ruff_check:
	@ruff check || true

ruff_fix:
	@ruff check --fix || true

ruff_format:
	@ruff format . --check || true
	@ruff format || true

diff:
	@git diff
