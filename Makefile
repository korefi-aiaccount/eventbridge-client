install:
	pip install -r requirements.txt

test:
	PYTHONPATH=. pytest tests/

lint:
	flake8 . --exclude .venv,__init__.py --ignore E203,E501,W503

.PHONY: test lint