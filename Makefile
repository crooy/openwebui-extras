.PHONY: lint format check setup-stubs

setup-stubs:
	python scripts/setup_stubs.py

format:
	black .

lint:
	flake8 .

check:
	mypy .

all: setup-stubs format lint check
