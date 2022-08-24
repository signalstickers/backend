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
	bandit --ini .bandit -x ${SRC_DIR}/signalstickers/settings/dev.py -r ${SRC_DIR}

test:
	cd signalstickers/ ; \
	./manage.py test

check: lint sec test