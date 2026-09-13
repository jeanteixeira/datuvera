DOCKER_COMPOSE = docker compose
.DEFAULT_GOAL := help

.PHONY: help up down build logs test reset-demo shell
help:
	@echo "make up          Build and start the local environment"
	@echo "make down        Stop the environment; keep database volumes"
	@echo "make build       Build API and web images"
	@echo "make logs        Follow API, web and database logs"
	@echo "make test        Run the backend test suite"
	@echo "make reset-demo  Replace only the demo database's public schema and seed"
	@echo "make shell       Open a shell in the running API container"

up:
	$(DOCKER_COMPOSE) up --build -d --wait

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build datuvera-api datuvera-web

logs:
	$(DOCKER_COMPOSE) logs -f --tail=100 datuvera-api datuvera-web datuvera-db datuvera-demo-db

test:
	$(DOCKER_COMPOSE) up -d --wait datuvera-db datuvera-demo-db
	$(DOCKER_COMPOSE) run --build --rm datuvera-api sh -c "alembic upgrade head && pytest -q"

reset-demo:
	sh scripts/reset-demo.sh

shell:
	$(DOCKER_COMPOSE) exec datuvera-api /bin/sh
