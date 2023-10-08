.PHONY: remove
remove:
	rm -rf dist build sqs_apolling.egg-info

.PHONY: dist
dist:
	pipenv run python setup.py sdist

.PHONY: bdist_wheel
bdist_wheel:
	pipenv run python setup.py bdist_wheel

.PHONY: build
build: remove dist bdist_wheel
