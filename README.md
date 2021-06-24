
![](https://github.com/signalstickers/backend/workflows/Test/badge.svg)

# Backend for signalstickers


This Django app provides an API for `signalstickers.com` to use, as well as a
control panel to manage packs.


## Dev

Install the pipenv (`pipenv install --dev`), and open a pipenv shell (`pipenv
shell`). You'll then be able to use `manage.py` (e.g. `./manage.py runserver`).

Run tests with `./manage.py test`


## Production

Copy `signalstickers/settings/prod.py.dist` to `signalstickers/settings/prod.py`
and edit values.


## Contribution process

TODO
