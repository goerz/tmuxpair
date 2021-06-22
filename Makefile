.DEFAULT_GOAL := help

PROJECT_NAME = tmuxpair
PACKAGES =  pip pytest coverage
TESTPYPI = https://testpypi.python.org/pypi

TESTOPTIONS = -v -s -x --doctest-modules --cov=tmuxpair
TESTS = tmuxpair.py test_tmuxpair.py

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
    match = re.match(r'^([a-z0-9A-Z_-]+):.*?## (.*)$$', line)
    if match:
        target, help = match.groups()
        print("%-20s %s" % (target, help))
print("""
""")
endef
export PRINT_HELP_PYSCRIPT


help:  ## show this help
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

install:  ## install the script into the current environment
	pip install .

develop: ## install the script into the current environment, in development mode
	pip install -e .[dev]

uninstall:  ## uninstall the script from the current environment
	pip uninstall $(PROJECT_NAME)

upload:  ## upload a release to PyPI
	python setup.py register
	python setup.py sdist upload

test-upload: # upload a release to test-PyPI
	python setup.py register -r $(TESTPYPI)
	python setup.py sdist upload -r $(TESTPYPI)

test-install: ## install the script from test-PyPI
	pip install -i $(TESTPYPI) $(PROJECT_NAME)

.venv/py27/bin/py.test:
	@conda create -y -m -p .venv/py27 python=2.7 $(PACKAGES)
	@.venv/py27/bin/pip install -e .[dev]

.venv/py34/bin/py.test:
	@conda create -y -m -p .venv/py34 python=3.4 $(PACKAGES)
	@.venv/py34/bin/pip install -e .[dev]

.venv/py35/bin/py.test:
	@conda create -y -m -p .venv/py35 python=3.5 $(PACKAGES)
	@.venv/py35/bin/pip install -e .[dev]

.venv/py36/bin/py.test:
	@conda create -y -m -p .venv/py36 python=3.6 $(PACKAGES)
	@.venv/py36/bin/pip install -e .[dev]

.venv/py37/bin/py.test:
	@conda create -y -m -p .venv/py37 python=3.7 $(PACKAGES)
	@.venv/py37/bin/pip install -e .[dev]

.venv/py38/bin/py.test:
	@conda create -y -m -p .venv/py38 python=3.8 $(PACKAGES)
	@.venv/py38/bin/pip install -e .[dev]

.venv/py39/bin/py.test:
	@conda create -y -m -p .venv/py39 python=3.9 $(PACKAGES)
	@.venv/py39/bin/pip install -e .[dev]

test27: .venv/py27/bin/py.test  ## run tests under python2.7
	$< -v $(TESTOPTIONS) $(TESTS)

test34: .venv/py34/bin/py.test  ## run tests under python 3.4
	$< -v $(TESTOPTIONS) $(TESTS)

test35: .venv/py35/bin/py.test  ## run tests under python 3.5
	$< -v $(TESTOPTIONS) $(TESTS)

test36: .venv/py36/bin/py.test  ## run tests under python 3.6
	$< -v $(TESTOPTIONS) $(TESTS)

test37: .venv/py37/bin/py.test  ## run tests under python 3.7
	$< -v $(TESTOPTIONS) $(TESTS)

test38: .venv/py38/bin/py.test  ## run tests under python 3.8
	$< -v $(TESTOPTIONS) $(TESTS)

test39: .venv/py39/bin/py.test  ## run tests under python 3.9
	$< -v $(TESTOPTIONS) $(TESTS)

test: test27 test35 test39 ## run tests covering the full range of supported Python versions

coverage: test39  ## create a coverage report
	@rm -rf htmlcov/index.html
	.venv/py39/bin/coverage html

clean:  ## clean up compilation and testing artifacts
	@rm -f *.pyc
	@rm -rf __pycache__
	@rm -rf *.egg-info
	@rm -rf htmlcov

distclean: clean  ## restore to a clean checkout
	@rm -rf .venv

.PHONY: install develop uninstall upload test-upload test-install test clean distclean coverage test27 test34 test35 test36 test37 test38 test39
