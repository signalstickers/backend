# `signalstickers.com'` public API 

This documents presents the `signalstickers.com'` public API, that must be used
by third-parties projects to interact with `signalstickers.com`. 

## Prerequisites

- A token, delivered by signalstickers' admins.

## Propose a pack

To propose a pack to `signalstickers.com`, send a HTTP `PUT` request to
`https://api.signalstickers.com/v1/contribute/`. You must send your token in a
`X-Auth-Token` header.

Here's the JSON format you must use:

```json
{
    "pack": {
        "pack_id": "b2e52b07dfb0af614436508c51aa24eb",
        "pack_key": "66224990b3e956ad4a735830df8cd071275afeae79db9797e57d99314daffc77",
        "source": "signalstickers.com",
        "tags": [
            "Foo",
            "Bar",
            "Foobar"
        ],
        "nsfw": true,
        "original": false
    }
}
```

### Success: `HTTP 200`

The pack has been successfully proposed.

### Bad token: `HTTP 401`

The provided token is invalid.

### Validation error: `HTTP 400`

In case of validation error (bad pack format, etc.), the API will return a HTTP
`400` code, along with a `error` message in the JSON response body. The message
can be displayed to the final user. For example:

```json
{
    "error": "This pack already exists, or has already been proposed (and is waiting for its approval)."
}
```

## Check a pack status

When a pack is proposed to `signalstickers.com`, it is not immediately
published; it has to go through a moderation stage. To check the status of a
pack (published, still in review, refused), do a HTTP `POST` request to
`https://api.signalstickers.com/v1/packs/status/`, with the following body
format:

```json
{
    "pack_id": "b2e52b07dfb0af614436508c51aa24eb",
    "pack_key": "66224990b3e956ad4a735830df8cd071275afeae79db9797e57d99314daffc77"
}
```

Note that this endpoint does not require a token.
A GUI is available for this feature at [https://signalstickers.com/contribution-status](https://signalstickers.com/contribution-status)

### The pack exists: `HTTP 200`

The pack exists in `signalstickers.com`'s database. The API will return a JSON,
containing various information.

```json
{
    "error": "",
    "pack_id": "b2e52b07dfb0af614436508c51aa24eb",
    "pack_title": "Test pack",
    "status": "IN_REVIEW",
    "status_comments": ""
}
```

`status` can be `ONLINE`, `IN_REVIEW` or `REFUSED`. In this last case,
`status_comments` could be filled by moderators, explaining why the pack was
refused.

### The pack is unknown: `HTTP 404`

The packs is not in `signalstickers.com`'s database.

### Validation error: `HTTP 400`

Your request is invalid, or `pack_id` or `pack_key` are not correctly formatted.