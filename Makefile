.PHONY: package
package:
	pipenv requirements --exclude-markers > requirements.txt
	pipenv run python setup.py sdist
