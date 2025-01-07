.PHONY: lint format check setup-stubs install-deps

install-deps:
	pip install -r requirements-dev.txt

setup-stubs: install-deps
	mkdir -p stubs/open_webui/models
	rm -f stubs/open_webui/models/*
	python scripts/setup_stubs.py
	python scripts/simplify_stubs.py

format:
	black .

lint: setup-stubs
	flake8 .

check: setup-stubs
	mypy .

all: setup-stubs format lint check
