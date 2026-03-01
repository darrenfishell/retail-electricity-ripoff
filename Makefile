PYTHON_SCRIPT := run_pipeline.py

.PHONY: all
all: install run

.PHONY: install
install:
	uv sync

.PHONY: run
run:
	uv run python $(PYTHON_SCRIPT)

.PHONY: clean
clean:
	rm -rf .venv

.PHONY: reset
reset: clean install

.PHONY: dev
dev: install
	cd observable && npm install && uv run npx observable preview

.PHONY: build
build: install
	cd observable && npm install && uv run npx observable build

.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  make install  - Install Python dependencies via uv"
	@echo "  make run      - Run the data pipeline"
	@echo "  make dev      - Start Observable dev server (local preview)"
	@echo "  make build    - Build Observable static site to observable/dist/"
	@echo "  make clean    - Remove the virtual environment"
	@echo "  make reset    - Clean and reinstall dependencies"
	@echo "  make help     - Show this help message"
