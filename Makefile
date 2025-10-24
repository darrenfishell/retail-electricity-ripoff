# Variables
ENV_NAME := retail-electricity
ENV_FILE := retail-electricity.yml
PYTHON_SCRIPT := run_pipeline.py

# Default target
.PHONY: all
all: env run

# Create conda environment
.PHONY: env
env:
	@echo "Creating Conda environment from $(ENV_FILE)..."
	conda env create -f $(ENV_FILE) -n $(ENV_NAME) || echo "Environment may already exist."ç

# Run Python script in environment
.PHONY: run
run:
	@echo "Running $(PYTHON_SCRIPT) using Conda environment $(ENV_NAME)..."
	conda run -n $(ENV_NAME) python $(PYTHON_SCRIPT)

# Remove the environment
.PHONY: clean
clean:
	@echo "Removing Conda environment $(ENV_NAME)..."
	conda remove -n $(ENV_NAME) --all -y

# Recreate environment (force)
.PHONY: reset
reset: clean env

# Help message
.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  make env      - Create Conda environment from $(ENV_FILE)"
	@echo "  make run      - Run $(PYTHON_SCRIPT) in environment"
	@echo "  make clean    - Remove the Conda environment"
	@echo "  make reset    - Clean and recreate the environment"
	@echo "  make help     - Show this help message"