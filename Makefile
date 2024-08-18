install:
	pip install -r requirements.txt

test:
	PYTHONPATH=. pytest tests/

.PHONY: test