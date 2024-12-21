install:
	poetry install

run:
	poetry run python -m src.main

lint:
	poetry run pylint src tests

deploy:
	cdk deploy --require-approval never