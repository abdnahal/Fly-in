install:
	pip install pygame flake8 mypy

run:
	python3 -m src file.txt

debug:
	python3 -m pdb main.py file.txt

clean:
	rm -rf  __pycache__
	rm -rf .mypy*

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
