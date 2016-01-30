PROJECT_NAME = tmuxpair
PACKAGES =  pip pytest coverage
TESTPYPI = https://testpypi.python.org/pypi

TESTOPTIONS = -v -s -x --doctest-modules --cov=tmuxpair.py
TESTS = tmuxpair.py test_tmuxpair.py


install:
	pip install .

develop:
	pip install -e .[dev]

uninstall:
	pip uninstall $(PROJECT_NAME)

upload:
	python setup.py register
	python setup.py sdist upload

test-upload:
	python setup.py register -r $(TESTPYPI)
	python setup.py sdist upload -r $(TESTPYPI)

test-install:
	pip install -i $(TESTPYPI) $(PROJECT_NAME)

.venv/py27/bin/py.test:
	@conda create -y -m -p .venv/py27 python=2.7 $(PACKAGES)
	@.venv/py27/bin/pip install -e .[dev]

.venv/py33/bin/py.test:
	@conda create -y -m -p .venv/py33 python=3.3 $(PACKAGES)
	@.venv/py33/bin/pip install -e .[dev]

.venv/py34/bin/py.test:
	@conda create -y -m -p .venv/py34 python=3.4 $(PACKAGES)
	@.venv/py34/bin/pip install -e .[dev]

.venv/py35/bin/py.test:
	@conda create -y -m -p .venv/py35 python=3.5 $(PACKAGES)
	@.venv/py35/bin/pip install -e .[dev]

test27: .venv/py27/bin/py.test
	$< -v $(TESTOPTIONS) $(TESTS)

test33: .venv/py33/bin/py.test
	$< -v $(TESTOPTIONS) $(TESTS)

test34: .venv/py34/bin/py.test
	$< -v $(TESTOPTIONS) $(TESTS)

test35: .venv/py35/bin/py.test
	$< -v $(TESTOPTIONS) $(TESTS)

test: test27 test33 test34 test35

coverage: test35
	@rm -rf htmlcov/index.html
	.venv/py35/bin/coverage html

clean:
	@rm -f *.pyc
	@rm -rf __pycache__
	@rm -rf *.egg-info
	@rm -rf htmlcov

distclean: clean
	@rm -rf .venv

.PHONY: install develop uninstall upload test-upload test-install test clean distclean coverage
