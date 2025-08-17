# Environment variable for container vs local execution
# Check if we're actually in a dev container by looking for dev container environment variables
DEV_CONTAINER := $(shell if [ -n "$$DEV_CONTAINER_ID" ] || [ -n "$$REMOTE_CONTAINERS" ] || [ -f /.dockerenv ]; then echo true; else echo false; fi)

# Help generator
help: ## Display this help.
	@echo "Please use 'make <target>' where <target> is one of the following:"
	@echo "Current mode: $(if $(filter true,$(DEV_CONTAINER)),Dev Container,Host - Docker Compose)"
	@echo "DEV_CONTAINER value: $(DEV_CONTAINER)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Development commands
lock: ## Update dependencies
	make uv args="lock"

# Example: manually add a package ->make uv args="add package==version"
uv: ## Run UV commands in the container
	docker compose run ${exec_args} --rm  \
		fastapi sh -c " \
		uv ${args} \
		"

up: ## Run compose
	docker compose up -d

build: ## Build docker compose
	docker compose build

down: ## Stop docker compose
	docker compose down --remove-orphans

down-volumes: ## Stop docker compose and clean up volumes
	docker compose down --volumes --remove-orphans

restart: ## Restart docker compose
	docker compose down && docker compose up -d && docker compose logs -f -t

full-restart: ## Restart docker compose with volume cleanup and rebuilding images
	docker compose down --volumes --remove-orphans && docker buildx bake && docker compose up -d && docker compose logs -f -t

logs: ## Follow logs
	docker compose logs -f -t

pre-commit: ## Run the pre-commit checks
	docker compose run ${exec_args} --rm fastapi pre-commit run ${args}

install-pre-commit: ## Install pre-commit hooks that run on Docker
	printf '#!/usr/bin/env bash\nset -eo pipefail\nmake -f "$(PWD)/Makefile" pre-commit exec_args="-T"\n' > "$(PWD)/.git/hooks/pre-commit"
	chmod ug+x "$(PWD)/.git/hooks/pre-commit"
	printf '#!/bin/bash\nMSG_FILE=$$1\ndocker compose run -T fastapi cz check --allow-abort --commit-msg-file $$MSG_FILE\n' > "$(PWD)/.git/hooks/commit-msg"
	chmod ug+x "$(PWD)/.git/hooks/commit-msg"

test: ## Run the tests
ifeq ($(DEV_CONTAINER),true)
	pytest --cov --cov-report=term --cov-report=html --cov-report=xml --cov-report=json ${args}
else
	docker compose run ${exec_args} --rm fastapi sh -c " \
                set -e; \
		pytest --cov --cov-report=term --cov-report=html --cov-report=xml --cov-report=json ${args}; \
	"
endif

bash: ## Open bash (container) or shell (local)
ifeq ($(DEV_CONTAINER),true)
	bash
else
	docker compose run ${exec_args} --rm fastapi bash
endif

make-migrations: ## Create migrations
ifeq ($(DEV_CONTAINER),true)
	alembic -c src/event_sourcing/infrastructure/database/alembic/alembic.ini revision --autogenerate
else
	docker compose run ${exec_args} --rm fastapi alembic -c /app/src/event_sourcing/infrastructure/database/alembic/alembic.ini revision --autogenerate
endif

migrate: ## Apply migrations
ifeq ($(DEV_CONTAINER),true)
	alembic -c src/event_sourcing/infrastructure/database/alembic/alembic.ini upgrade head
else
	docker compose run ${exec_args} --rm migrator alembic -c /app/src/event_sourcing/infrastructure/database/alembic/alembic.ini upgrade head
endif

dbshell: ## Open PSQL shell
	docker compose exec postgres psql -U admin -d event_sourcing

command: ## Run CLI commands (e.g., make command args="users create-admin --help")
ifeq ($(DEV_CONTAINER),true)
	python -m event_sourcing.cli $(args)
else
	docker compose run ${exec_args} --rm fastapi python -m event_sourcing.cli $(args)
endif

localstack: ## Open a shell on localstack
	docker compose exec localstack bash

shell: ## Open Python shell with enhanced experience
ifeq ($(DEV_CONTAINER),true)
	python -c 'from event_sourcing.main import app; from event_sourcing.config.settings import Settings' && \
	ipython -i -c 'from event_sourcing.main import app; from event_sourcing.config.settings import Settings; from event_sourcing.infrastructure.database.models import *; from event_sourcing.infrastructure.database.session import DatabaseManager, AsyncDBContextManager; from event_sourcing.config.celery_app import app as celery_app; from sqlalchemy import select; import asyncio; settings = Settings(); db_manager = DatabaseManager(settings.DATABASE_URL); print("FastAPI Shell Plus - Available imports: app, settings, celery_app"); print("Database manager ready: db_manager"); print("Models available: EventStream, UserEventStream, User, UserSnapshot"); print("Example query: async with AsyncDBContextManager(db_manager) as session: result = await session.execute(select(User).limit(5))")'
else
	docker compose run ${exec_args} --rm fastapi sh -c " \
		python -c 'from event_sourcing.main import app; from event_sourcing.config.settings import Settings' && \
		ipython -i -c 'from event_sourcing.main import app; from event_sourcing.config.settings import Settings; from event_sourcing.infrastructure.database.models import *; from event_sourcing.infrastructure.database.session import DatabaseManager, AsyncDBContextManager; from event_sourcing.config.celery_app import app as celery_app; from sqlalchemy import select; import asyncio; settings = Settings(); db_manager = DatabaseManager(settings.DATABASE_URL); print(\"FastAPI Shell Plus - Available imports: app, settings, celery_app\"); print(\"Database manager ready: db_manager\"); print(\"Models available: EventStream, UserEventStream, User, UserSnapshot\"); print(\"Example query: async with AsyncDBContextManager(db_manager) as session: result = await session.execute(select(User).limit(5))\")' \
	"
endif

# Presentation commands
install-marp: ## Install marp-cli globally
	@echo "Installing Marp CLI..."
	npm install -g @marp-team/marp-cli
	@echo "Marp CLI installed successfully!"

install-mermaid-cli: ## Install mermaid-cli globally
	@echo "Installing Mermaid CLI..."
	npm install -g @mermaid-js/mermaid-cli
	@echo "Mermaid CLI installed successfully!"

create-directories: ## Create necessary directories for diagrams
	@echo "Creating directories..."
	mkdir -p docs/presentation/diagrams/source
	mkdir -p docs/presentation/diagrams/generated
	@echo "Directories created successfully!"

generate-diagrams: create-directories ## Generate diagrams from Mermaid source files
	@echo "Generating diagrams..."
	@if [ -d "docs/presentation/diagrams/source" ]; then \
		echo "Found docs/presentation/diagrams/source directory"; \
		file_count=$$(find docs/presentation/diagrams/source -name "*.mmd" | wc -l); \
		echo "Found $$file_count .mmd files"; \
		if [ $$file_count -gt 0 ]; then \
			for file in docs/presentation/diagrams/source/*.mmd; do \
				if [ -f "$$file" ]; then \
					filename=$$(basename $$file .mmd); \
					echo "Generating $$filename.png from $$file"; \
					npx --yes @mermaid-js/mermaid-cli -i $$file -o docs/presentation/diagrams/generated/$$filename.png; \
				fi; \
			done; \
			echo "Diagrams generated successfully!"; \
		else \
			echo "No .mmd files found in docs/presentation/diagrams/source/"; \
			echo "Creating example diagram..."; \
			echo 'graph TD\n    A[Client Request] --> B[FastAPI]\n    B --> C[Event Store]\n    B --> D[Event Bus]\n    D --> E[Celery Workers]\n    E --> F[Read Model]\n    F --> G[Client Response]' > docs/presentation/diagrams/source/architecture.mmd; \
			npx --yes @mermaid-js/mermaid-cli -i docs/presentation/diagrams/source/architecture.mmd -o docs/presentation/diagrams/generated/architecture.png; \
			echo "Example architecture diagram created!"; \
		fi; \
	else \
		echo "docs/presentation/diagrams/source directory not found"; \
	fi

pptx: install-marp generate-diagrams ## Generate presentation PowerPoint from markdown with speaker notes
	@echo "Generating presentation PowerPoint with speaker notes..."
	marp docs/presentation/presentation.md --pptx --allow-local-files --output docs/presentation/presentation.pptx
	@echo "Presentation PowerPoint with speaker notes generated successfully!"

clean: ## Clean generated files
	@echo "Cleaning generated files..."
	rm -f docs/presentation/presentation.pptx
	rm -rf docs/presentation/diagrams/generated/*
	@echo "Cleanup completed!"

setup: install-marp install-mermaid-cli create-directories ## Complete setup for presentation development
	@echo "Setup completed! You can now:"
	@echo "  - Run 'make pptx' to generate PowerPoint"
	@echo "  - Add Mermaid diagrams to docs/presentation/diagrams/source/"

.PHONY: $(shell grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | cut -d ':' -f 1)
