_checkfiles = tackle/
checkfiles = $(_checkfiles) *.py

mypy_flags = --ignore-missing-imports --follow-imports=silent --check-untyped-defs --warn-no-return --warn-unused-ignores

flake8_flags = --max-line-length=140 --exclude db_migrations

pylint_flags = --max-line-length=140


help:
	@echo  "usage: make <target>"
	@echo  "Targets:"
	@echo  "	requirements		Update requirements files."
	@echo  "	requirements_ref	Update requirement_ref file to cement the dependencies' versions for the quickstart guide."
	@echo  "	deps				Ensure dependencies are installed."
	@echo  "	check				Runs some checking and linting."
	@echo  "	local_postgress_db	Creates local model DBs."
	@echo  "	test				Runs all tests."
	@echo  "	documents			Builds the documentation."

requirements:
	pip-compile -o requirements.txt etc/requirements.in -U
	pip-compile -o requirements_dev.txt etc/requirements_dev.in -U

requirements_ref: requirements
	cp requirements.txt requirements_ref.txt

deps:
	pip-sync requirements_dev.txt

check:
	@echo [setup.py check]:
	@python setup.py check -mrs
	@echo [mypy]:
	@mypy $(mypy_flags) --incremental $(_checkfiles)
	@echo [pylint]:
	@pylint -E $(pylint_flags) $(checkfiles)
	@echo [flake8]:
	@flake8 $(flake8_flags) $(checkfiles)

local_postgress_db:
	-psql -c "CREATE ROLE tackle WITH LOGIN PASSWORD 'tackle';"
	-psql -c "ALTER ROLE tackle WITH SUPERUSER CREATEROLE CREATEDB;"
	-createdb --encoding=UTF8 tackle --owner=tackle --username=tackle
	cd tackle; python manage_db.py db migrate --directory db_migrations; python manage_db.py db upgrade --directory db_migrations; cd ..
#	-createdb --encoding=UTF8 test_tackle --owner=tackle --username=tackle

test:
#   Unit tests without coverage:
#	@python -m unittest discover -s './tackle' -t './tackle'

#   Unit tests with coverage:
	@coverage run --rcfile=.coveragerc -m unittest discover -f -s './tackle' -t './tackle'

	@coverage html
	@coverage report
