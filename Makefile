.PHONY: default lint sec check


SRC_DIR=signalstickers

default:
	@echo 'No action.'
	@exit 1


venv:
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev

lint:
	pylint ${SRC_DIR} --rcfile .pylintrc
	black --check ${SRC_DIR} --exclude 'migrations'
	isort --sp .isort.cfg --check ${SRC_DIR}

sec:
	bandit --ini .bandit -r ${SRC_DIR}

test:
	cd signalstickers/ ; \
	./manage.py test

check: test lint sec 

fix:
	pylint ${SRC_DIR} --rcfile .pylintrc
	black  ${SRC_DIR} --exclude 'migrations'
	isort --sp .isort.cfg ${SRC_DIR}