# Backend for `signalstickers.com`

This Django app provides an API for `signalstickers.com` to use, as well as a
control panel to manage packs.

## Installation

Copy `signalstickers/settings/prod.py.dist` to `signalstickers/settings/prod.py` and edit values.


## API

### Proposing a pack

First, an empty HTTP `POST` request has to be made to `/contributionrequest/`. This will return a `contribution_id` and a `question`.
When the form is filled, send it with a HTTP `PUT` to `/packs/`, with the following format:

```json
{
    "pack": {
        "pack_id": "4830e258138fca961ab2151d9596755c", 
        "pack_key": "87078ee421bad8bf44092ca72166b67ae5397e943452e4300ced9367b7f6a1a1",
        "source": "signalstickers.com", 
        "tags": ["Foo", "Bar", "Foobar"], 
        "nsfw": true, 
        "original": false
    },
    "contribution_id": "3666c1a6-daf0-4e5c-1337-e6e6875f75e7",
    "contribution_answer" : "yes",
    "submitter_comments": "Thanks for validating my pack!"
}
```