# Makefile for net-latency-monitor

.PHONY: all test venv install-dev clean help

# Variables
PYTHON ?= python3
VENV_DIR := .venv_monitor_net
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python
REQUIREMENTS_FILE := requirements.txt

# Check if we're inside a virtual environment already
# VIRTUAL_ENV environment variable is set when a virtual environment is active.
# Default to system python if VIRTUAL_ENV is not set, otherwise use current python.
# For targets that *require* the venv python (like install-dev), we use VENV_PYTHON directly.
CURRENT_PYTHON := $(shell command -v $(PYTHON))
ifeq ($(VIRTUAL_ENV),)
    # Not in a virtual environment, or VIRTUAL_ENV is not exported/set.
    # Prefer venv's python if venv exists for targets like 'test'.
    PYTHON_FOR_TESTS := $(shell if [ -f "$(VENV_PYTHON)" ]; then echo "$(VENV_PYTHON)"; else echo "$(PYTHON)"; fi)
else
    # Already in a virtual environment. Use the current Python.
    PYTHON_FOR_TESTS := $(PYTHON)
endif

all: help

help:
	@echo "Available targets:"
	@echo "  venv          - Create/recreate the Python virtual environment in $(VENV_DIR)"
	@echo "  install-dev   - Install development dependencies into the virtual environment (creates venv if needed)"
	@echo "  test          - Run pytest tests using the virtual environment's Python (if available) or system Python"
	@echo "  clean         - Remove virtual environment, build artifacts, and __pycache__ directories"
	@echo "  help          - Show this help message"

venv:
	@if [ ! -d "$(VENV_DIR)" ]; then 		echo "INFO: Creating virtual environment in $(VENV_DIR)..."; 		$(PYTHON) -m venv $(VENV_DIR); 		echo "INFO: Virtual environment created."; 		echo "INFO: To activate, run: source $(VENV_DIR)/bin/activate"; 		echo "INFO: Install dependencies with: make install-dev"; 	else 		echo "INFO: Virtual environment $(VENV_DIR) already exists. To recreate, run 'make clean venv'."; 	fi

install-dev: venv
	@echo "INFO: Installing/updating development dependencies from pyproject.toml..."
	$(VENV_PYTHON) -m pip install --disable-pip-version-check --no-cache-dir -e .[dev]
	@echo "INFO: Development dependencies installed."

test:
	@echo "INFO: Running tests with $(PYTHON_FOR_TESTS)..."
	$(PYTHON_FOR_TESTS) -m pytest tests/

clean:
	@echo "INFO: Cleaning up..."
	@if [ -d "$(VENV_DIR)" ]; then 		echo "INFO: Removing virtual environment $(VENV_DIR)..."; 		rm -rf $(VENV_DIR); 	fi
	@echo "INFO: Removing build artifacts..."
	@rm -rf dist build *.egg-info
	@echo "INFO: Removing __pycache__ directories and .pyc files..."
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type f -name '*.pyc' -delete
	@echo "INFO: Cleanup complete."
