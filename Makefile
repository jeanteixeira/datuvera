#!/usr/bin/env make

.PHONY: reset-demo
reset-demo:
	@echo "Resetting only the demo Postgres database (datuvera-demo-db)"
	@echo "Stopping demo container if running..."
	-docker compose stop datuvera-demo-db
	@echo "Finding demo container ID (previous instance)..."
	CID=$(shell docker compose ps -q datuvera-demo-db) || true
	@if [ -n "$(CID)" ]; then \
	  echo "Removing demo container..."; \
	  docker rm -f $(CID); \
	fi
	@echo "Discovering anonymous volume used by demo DB (mounted at /var/lib/postgresql/data)..."
	VOL=$(shell docker volume ls -q --filter label=com.docker.compose.service=datuvera-demo-db | head -n1)
	@if [ -n "$(VOL)" ]; then \
	  echo "Removing volume $(VOL)"; \
	  docker volume rm -f $(VOL); \
	else \
	  echo "No named compose volume found; attempting to detect unnamed volume via inspect..."; \
	  OLD_CID=$$(docker ps -a -q --filter name=datuvera-datuvera-demo-db); \
	  if [ -n "$$OLD_CID" ]; then \
	    VNAME=$$(docker inspect -f '{{ range .Mounts }}{{ if eq .Destination "/var/lib/postgresql/data" }}{{ .Name }}{{ end }}{{ end }}' $$OLD_CID); \
	    if [ -n "$$VNAME" ]; then \
	      echo "Removing discovered volume $$VNAME"; docker volume rm -f $$VNAME; fi; \
	  fi; \
	fi
	@echo "Starting demo DB (will run init scripts)..."
	 docker compose up -d datuvera-demo-db
	@echo "Demo DB reset complete. Use 'docker compose logs -f datuvera-demo-db' to follow init output."
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
