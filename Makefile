DOCKER_COMPOSE=docker compose

.PHONY: up down build logs test shell
up:
	$(DOCKER_COMPOSE) up --build -d

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build --pull

logs:
	$(DOCKER_COMPOSE) logs -f --tail=200

test:
	@echo "Running backend tests inside Docker..."
	$(DOCKER_COMPOSE) run --rm datuvera-api pytest -q

shell:
	$(DOCKER_COMPOSE) exec datuvera-api /bin/sh
