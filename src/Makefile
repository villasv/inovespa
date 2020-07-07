.PHONY: lint

lint:
	black . -l 80
	pylint *.py -d C0114,C0115,C0116,C0330
	flake8 . --max-line-length 80
