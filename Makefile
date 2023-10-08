.PHONY: freeze
freeze:
	pipenv requirements --exclude-markers > requirements.txt

.PHONY: dist
dist: requirements
	pipenv run python setup.py sdist
