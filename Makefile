install:
	pip install pygame flake8 mypy

run:
	python3 -m src file.txt

debug:
	python3 -m pdb src/main.py 

clean:
	rm -rf src/__pycache__ __pycache__

lint:
	flake8 src
	mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
	flake8 .