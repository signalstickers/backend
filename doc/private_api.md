# `signalstickers.com'` public API 

This documents presents the `signalstickers.com'` **private** API, used by the
website. If you are a third-party project and want to interact with
`signalstickers.com`, please use the [public API](public_api.md) 

## API routes

### `/packs/`

#### `GET`

Get the list of all `ONLINE` packs. This endpoint is called by the main page on
`signalstickers.com`.


Example response (formatted):

```json
[
    {
        "meta": {
            "id": "2be4e9e48dca160d94fc73eadf9079e5",
            "key": "f54b47073e41e8794cff855e5667e0042e1fc7d6d20e3992c8f08d5ca59dfaaf",
            "source": "",
            "tags": [
                "animal",
                "animated",
                "cat",
                "cute",
                "dog",
                "line",
                "meow"
            ],
            "nsfw": false,
            "original": false,
            "animated": true
        },
        "manifest": {
            "title": "NaughtyMiao and PuppyWang",
            "author": "J.X.H (LINE)",
            "cover": {
                "id": 0
            }
        },
        "status": "ONLINE"
    },
    ...
]
```


### `/contributionrequest/`

#### `POST`

Request a `ContributionRequest`. Do an empty `HTTP POST` on this endpoint to
obtain a `contribution_id` and a `contribution_question`. A
`ContributionRequest` is valid for 2 hours.

When submitting a pack via `PUT /packs/`, include the `contribution_id` and the
answer to the `contribution_question`.

Example response: 

```json
{
    "contribution_id": "6da38f85-834b-455b-a207-433a8adf240e",
    "contribution_question": "What is big, grey and have big lovely ears?"
}
```


### Proposing a pack

First, an empty HTTP `POST` request has to be made to `/contributionrequest/`.
This will return a `contribution_id` and a `question`. When the form is filled,
send it with a HTTP `PUT` to `/contribute/`, with the following format:

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
    "contribution_answer" : "elephant",
    "submitter_comments": "Thanks for validating my pack!"
}
```

The proposed pack will not appear `ONLINE` as it need to be validated first by
admins.