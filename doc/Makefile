#!/usr/bin/make -f

# If sphinx-build is not installed or if too early a version is installed make
# will attempt to install latest sphinx-build via a virtualenv.
#
# export SPHINX_DEV_MODE='true' to prevent the virtualenv from being deleted
# after the build completes.

# Installation of sphinx via a virtualenv.
env-path = ../venv
sphinx-dev-mode := $(shell echo "${SPHINX_DEV_MODE}")
min-sphinx-version = 1.5.3
sphinx-install := $(shell scripts/sphinx-install $(env-path) $(min-sphinx-version))

# Build parameters.
pypath = ../lib/python
build-dir = sphinx/_build

# Command to tidy the virtualenv if required.
tidy-venv =
ifneq	"$(sphinx-dev-mode)" "true"
	tidy-venv = rm -rf $(env-path)
endif

# Command to activate the virtualenv if required.
venv =
ifneq	"$(sphinx-install)"	""
venv = . $(env-path)/bin/activate;
endif

all: clean doctest html tidy

html: sphinx-build
	$(venv) PYTHONPATH=../$(pypath) make -C sphinx html

doctest: sphinx-build
	$(venv) PYTHONPATH=../$(pypath) make -C sphinx doctest

sphinx-build: $(sphinx-install)
	$(venv) PYTHONPATH=$(pypath) sphinx-build -aEW -b dummy sphinx sphinx/_build

sphinx-install:
	$(tidy-venv)
	virtualenv --python=python2.7 "$(env-path)"
	$(venv) pip install sphinx
	$(venv) pip install sphinx_rtd_theme
	$(venv) pip install https://github.com/mapio/GraphvizAnim/archive/0.2-alpha.zip

sphinx-activate:

tidy:
	$(tidy-venv)

clean:
	rm -rf $(build-dir)
	$(tidy-venv)
