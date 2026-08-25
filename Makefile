install:
	python3 -m pip install flake8 mypy pytest pygame

run:
	python3 -m fly_in

debug:
	python3 -m pdb -m fly_in

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
