install:
	pip install pygame flake8 mypy

run:
	python3 src/main.py

debug:
	python3 -m pdb src/main.py 

clean:
	rm -rf src/__pycache__ __pycache__

lint:
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
	flake8 .