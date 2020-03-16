# This was based on a Makefile by Kirk Hansen <https://github.com/kirkhansen>

.PHONY: clean clean-test clean-pyc clean-build clean-setup clean-cython docs help test
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python3 -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-setup clean-cython ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

clean-setup: ## run python setup.py clean
	python setup.py clean

clean-cython: ## clean the cython files
	rm -f pyproj/*.so
	rm -f pyproj/*/*.so
	rm -f pyproj/*/*.c
	rm -f pyproj/*.c

lint: ## check style with flake8
	flake8 --max-line-length 88 setup.py pyproj/ test/ docs/
	flake8 --append-config=flake8/cython.cfg pyproj/

check-type:
	mypy pyproj

check: lint check-type ## flake8 black isort check
	black --check setup.py pyproj/ test/ docs/
	isort --check --recursive setup.py pyproj/ test/ docs/

isort: ## order imports
	isort --recursive setup.py pyproj/ test/ docs/

black: ## black format files
	black setup.py pyproj/ test/ docs/

test: ## run tests
	py.test

test-verbose: ## run tests with full verbosity
	py.test -vv -s

test-coverage:  ## run tests and generate coverage report
	py.test --cov-report term-missing --cov=pyproj -v -s

install-docs: ## Install requirements for building documentation
	pip install sphinx sphinx_rtd_theme

docs: ## generate Sphinx HTML documentation, including API docs
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

docs-browser: docs ## generate Sphinx HTML documentation, including API docs and open in a browser
	$(BROWSER) docs/_build/html/index.html

install: clean ## install the package to the active Python's site-packages
	python setup.py install

install-dev: clean ## install development version to active Python's site-packages
	pip install -U -r requirements-dev.txt
	PYPROJ_FULL_COVERAGE=YES pip install -e . --no-use-pep517 || PYPROJ_FULL_COVERAGE=YES pip install -e .
