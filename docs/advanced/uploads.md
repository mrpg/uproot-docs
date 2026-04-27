# File uploads

uproot supports file uploads from participants using `FileField`. Uploaded files are handled as stealth fields—they are not stored in the database automatically, giving you full control over how to process them.

## Basic file upload

Add a `FileField` to your page:

```python
class Upload(Page):
    fields = dict(
        cv=FileField(label="Please upload your curriculum vitæ."),
    )

    @classmethod
    async def handle_stealth_fields(page, player, data):
        cv = data["cv"]
        contents = await cv.read()
        player.file_name = cv.filename
        player.file_size = cv.size
```

`FileField` is always treated as a stealth field. The uploaded file is passed to `handle_stealth_fields` as a [Starlette UploadFile](https://www.starlette.io/requests/#request-files) object.

:material-github: [See the upload example](https://github.com/mrpg/uproot-examples/tree/master/upload)

## The UploadFile object

The uploaded file has these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `filename` | `str` | Original filename |
| `size` | `int` | File size in bytes |
| `content_type` | `str` | MIME type (e.g., `image/png`) |

And this method:

| Method | Returns | Description |
|--------|---------|-------------|
| `await file.read()` | `bytes` | Read the full file contents |

## Storing uploaded files

Since uploads are stealth fields, you decide where to store the data. Common approaches:

### Save to disk

```python
@classmethod
async def handle_stealth_fields(page, player, data):
    photo = data["photo"]
    if photo.size > 0:
        contents = await photo.read()
        path = f"uploads/{player.session.name}_{player.name}_{photo.filename}"
        with open(path, "wb") as f:
            f.write(contents)
        player.photo_path = path
```

### Store metadata only

```python
@classmethod
async def handle_stealth_fields(page, player, data):
    doc = data["document"]
    player.doc_name = doc.filename
    player.doc_size = doc.size
    player.doc_type = doc.content_type
```

## Validating uploads

Return error messages from `handle_stealth_fields` to reject the submission:

```python
@classmethod
async def handle_stealth_fields(page, player, data):
    photo = data["photo"]

    if photo.size == 0:
        return "Please select a file"

    if photo.size > 5_000_000:
        return "File too large (max 5 MB)"

    if photo.content_type not in ("image/png", "image/jpeg"):
        return "Only PNG and JPEG files are accepted"

    contents = await photo.read()
    player.photo_size = len(contents)
```

## Combining uploads with regular fields

You can mix file uploads with regular fields on the same page. Regular fields are saved automatically; the file field goes through `handle_stealth_fields`:

```python
class UploadPage(Page):
    fields = dict(
        name=StringField(label="Your name"),
        photo=FileField(label="Upload a photo"),
    )

    @classmethod
    async def handle_stealth_fields(page, player, data):
        photo = data["photo"]
        if photo.size > 0:
            contents = await photo.read()
            player.photo_name = photo.filename
```

The `name` field saves to `player.name` automatically. The `photo` field is handled separately.

## Rendering in templates

Use the standard field rendering:

```html+jinja
{% extends "Base.html" %}

{% block main %}
{{ field(form.cv) }}
{% endblock main %}
```

Or render all fields at once:

```html+jinja
{{ fields() }}
```

## Summary

| Feature | Purpose |
|---------|---------|
| `FileField(label=...)` | File upload field |
| `handle_stealth_fields(page, player, data)` | Process uploaded files |
| `await file.read()` | Get file contents as bytes |
| `file.filename` | Original filename |
| `file.size` | File size in bytes |
| `file.content_type` | MIME type |
| Return a string from handler | Validation error message |
