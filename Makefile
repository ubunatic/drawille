# Python Testing
# ==============
.PHONY: test clean tox

unexport PYTHONPATH
PY  := $(shell python -c 'import sys; sys.stdout.write(str(sys.version_info.major))')
TAG := py$(subst .,,$(PY))  # tox env name for current python version

test:
	python -m flake8 drawille                       # run flake8 linter
	python -m pytest -sxv tests                     # run unit tests
	tests/test-modules.sh                           # run CLI module usage test

clean: ; rm -rf .build; pyclean . || true           # cleanup pyc files and build dir
tox: clean install-tox ; tox -e $(TAG)              # run tox tests for current python

# Software Installation
# =====================
.PHONY: install uninstall test-install install-tox
install:      ; pip install --user -e .
uninstall:    ; pip uninstall -y drawille || true
test-install: ;	turtille -h                         # ensure turtille binary is installed
install-tox:  ; which tox || pip install tox        # install tox if not present

# Development Helpers
# ===================
.PHONY: amend docker-build docker-all
amend: clean
	# commit code changes to test repo in docker
	git add --all
	git commit --amend --no-edit --allow-empty

.build:
	# create clean side-effect-free copy of the repo for safe testing
	git clone . .build && rm -rf .build/.git

docker-build: .build
	# run all tests in docker using the currently commited code
	docker build --build-arg PY=$(PY) -t drawille .
	docker run --rm -it --entrypoint turtille drawille -h

docker-all: clean
	# run all tests in docker for the most common Python versions
	$(MAKE) docker-build PY=3
	$(MAKE) docker-build PY=2
	$(MAKE) docker-build PY=3.6
	$(MAKE) docker-build PY=3.5
	$(MAKE) docker-build PY=2.7

