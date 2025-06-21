# Makefile for PyCon Athens Presentation
# Event Sourcing & CQRS with FastAPI and Celery

.PHONY: help install-marp install-mermaid-cli create-presentation generate-diagrams clean

# Help generator
help: ## Display this help.
	@echo "Please use 'make <target>' where <target> is one of the following:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

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
	mkdir -p diagrams/source
	mkdir -p diagrams/generated
	@echo "Directories created successfully!"

generate-diagrams: install-mermaid-cli create-directories ## Generate diagrams from Mermaid source files
	@echo "Generating diagrams..."
	@if [ -d "diagrams/source" ] && [ "$(ls -A diagrams/source)" ]; then \
		for file in diagrams/source/*.mmd; do \
			if [ -f "$$file" ]; then \
				filename=$$(basename $$file .mmd); \
				echo "Generating $$filename.png from $$file"; \
				mmdc -i $$file -o diagrams/generated/$$filename.png; \
			fi; \
		done; \
		echo "Diagrams generated successfully!"; \
	else \
		echo "No diagram source files found in diagrams/source/"; \
		echo "Creating example diagram..."; \
		echo 'graph TD\n    A[Client Request] --> B[FastAPI]\n    B --> C[Event Store]\n    B --> D[Event Bus]\n    D --> E[Celery Workers]\n    E --> F[Read Model]\n    F --> G[Client Response]' > diagrams/source/architecture.mmd; \
		mmdc -i diagrams/source/architecture.mmd -o diagrams/generated/architecture.png; \
		echo "Example architecture diagram created!"; \
	fi

create-presentation: install-marp generate-diagrams ## Generate presentation PDF from markdown
	@echo "Generating presentation PDF..."
	marp presentation.md --pdf --allow-local-files --output presentation.pdf
	@echo "Presentation PDF generated successfully!"

create-html: install-marp generate-diagrams ## Generate presentation HTML from markdown
	@echo "Generating presentation HTML..."
	marp presentation.md --html --allow-local-files --output presentation.html
	@echo "Presentation HTML generated successfully!"

create-pptx: install-marp generate-diagrams ## Generate presentation PowerPoint from markdown
	@echo "Generating presentation PowerPoint..."
	marp presentation.md --pptx --allow-local-files --output presentation.pptx
	@echo "Presentation PowerPoint generated successfully!"

serve-presentation: install-marp generate-diagrams ## Serve presentation locally for preview
	@echo "Starting local server for presentation preview..."
	@echo "Open http://localhost:8080 in your browser"
	marp presentation.md --server --allow-local-files

clean: ## Clean generated files
	@echo "Cleaning generated files..."
	rm -f presentation.pdf presentation.html presentation.pptx
	rm -rf diagrams/generated/*
	@echo "Cleanup completed!"

setup: install-marp install-mermaid-cli create-directories ## Complete setup for presentation development
	@echo "Setup completed! You can now:"
	@echo "  - Run 'make create-presentation' to generate PDF"
	@echo "  - Run 'make serve-presentation' to preview locally"
	@echo "  - Add Mermaid diagrams to diagrams/source/"

watch: ## Watch for changes and regenerate presentation
	@echo "Watching for changes in presentation.md..."
	@echo "Press Ctrl+C to stop"
	@while true; do \
		inotifywait -e modify presentation.md; \
		echo "Change detected, regenerating..."; \
		make create-presentation; \
	done

# Development helpers
check-marp: ## Check if Marp is installed
	@if command -v marp >/dev/null 2>&1; then \
		echo "Marp CLI is installed"; \
		marp --version; \
	else \
		echo "Marp CLI is not installed. Run 'make install-marp'"; \
	fi

check-mermaid: ## Check if Mermaid CLI is installed
	@if command -v mmdc >/dev/null 2>&1; then \
		echo "Mermaid CLI is installed"; \
		mmdc --version; \
	else \
		echo "Mermaid CLI is not installed. Run 'make install-mermaid-cli'"; \
	fi

validate: check-marp check-mermaid ## Validate all dependencies are installed
	@echo "All dependencies validated!"

# Quick commands
pdf: create-presentation ## Quick alias for create-presentation
html: create-html ## Quick alias for create-html
pptx: create-pptx ## Quick alias for create-pptx
serve: serve-presentation ## Quick alias for serve-presentation 