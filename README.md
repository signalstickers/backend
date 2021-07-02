
![](https://github.com/signalstickers/backend/workflows/Test/badge.svg)

# Backend for signalstickers


This Django app provides an API for `signalstickers.com` to use, as well as a
control panel to manage packs.


## Dev

Install the pipenv (`pipenv install --dev`), and open a pipenv shell (`pipenv
shell`). You'll then be able to use `manage.py` (e.g. `./manage.py runserver`).

Run tests with `./manage.py test`.

You can import packs from signalstickers' YML format with `manage.py import_from_yml path/to/yml`

### Docker
We use Docker containers for postgres. An `adminer` container is available to
browse the DB from a web browser at http://localhost:9988. (Serveur: postgres)
Credentials of the DB are stored into `docker/postgres.env`.

#### Launch the containers

```
sudo docker-compose up -d
```

#### Stop containers

```
sudo docker-compose down
```

#### Reset containers

```
sudo docker-compose down                # If needed
sudo rm -rf .pgdata                     # Remove the data directory of postgres
sudo docker-compose up --force-recreate
```

## Production

Copy `signalstickers/settings/prod.py.dist` to `signalstickers/settings/prod.py`
and edit values.


## Contribution process

TODO
