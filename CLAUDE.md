# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands
*Note: This project is in initial setup. The commands below are standard Python conventions and should be updated as the project configuration (pyproject.toml/requirements.txt) is established.*

- **Environment Setup**: `python3 -m venv venv && source venv/bin/activate`
- **Install Dependencies**: `pip install -r requirements.txt` (or `pip install -e .` if setup.py/pyproject.toml exists)
- **Run Tests**: `pytest`
- **Lint**: `flake8` or `pylint`
- **Format**: `black .` or `ruff format .`

## Code Architecture
- **Project Type**: Python CLI/Utility (Inferred from repo name `obsidian-auto-link-python`)
- **Status**: Initial setup (Empty repository)
- **Goal**: Likely a tool to automate linking in Obsidian markdown vaults.

## Style Guidelines
- Follow PEP 8 standards.
- Use type hints (mypy) for public interfaces.
- Docstrings should follow Google or NumPy style.
