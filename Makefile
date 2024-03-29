SHELL := /bin/bash
CURRENT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

version = 3

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

all: .installed.cfg

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.installed.cfg: bin/buildout *.cfg
	bin/buildout

bin/buildout: bin/pip
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	bin/pip install pip install black==$$(awk '/^black =/{print $$NF}' versions.cfg)
	@touch -c $@

bin/python bin/pip:
	python$(version) -m venv . || virtualenv --clear --python=python$(version) .

py2:
	virtualenv --clear --python=python2 .
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt

.PHONY: Build Plone 5.2
build: .installed.cfg  ## Build Plone 5.2
	bin/pip install --upgrade pip
	bin/pip install -r requirements.txt
	bin/buildout

.PHONY: Test
test:  ## Test
	bin/test

.PHONY: Test Performance
test-performance:
	jmeter -n -t performance.jmx -l jmeter.jtl

.PHONY: Code Analysis
code-analysis:  ## Code Analysis
	bin/code-analysis
	if [ -f "bin/black" ]; then bin/black src/ --check ; fi

.PHONY: Black
black:  ## Black
	if [ -f "bin/black" ]; then bin/black src/ setup.py; fi

.PHONY: Flake 8
flake8:  ## Flake 8
	if [ -f "bin/flake8" ]; then bin/flake8 src/ setup.py; fi

.PHONY: zpretty
zpretty:  ## zpretty
	if [ -f "bin/zpretty" ]; then find src/ -name *.zcml | xargs bin/zpretty -i; fi

.PHONY: Build Docs
docs:  ## Build Docs
	bin/sphinxbuilder

.PHONY: Test Release
test-release:  ## Run Pyroma and Check Manifest
	bin/pyroma -n 10 -d .

.PHONY: Release
release:  ## Release
	bin/fullrelease

.PHONY: Clean
clean:  ## Clean
	git clean -Xdf

.PHONY: all clean
