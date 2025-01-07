.PHONY: lint format check

format:
	black .

lint:
	flake8 .

check:
	mypy .

all: format lint check
