# Custom settings forms

When an experimenter creates a session, they can adjust the config's default [session settings](../building/data.md#session-settings) by editing raw JSON in the admin interface. Raw JSON is flexible, but it is also easy to get wrong: a mistyped key or a string where a list is expected, and the session runs with the wrong parameters.

An app can replace that JSON editor with its own settings form. If your app folder contains a file named `AdminSettings.html`, the admin's new-session page shows your form instead of the JSON editor whenever a config containing your app is selected.

!!! warning "Super advanced"
    This is one of the most advanced features in uproot. You will write raw HTML, [Jinja](https://jinja.palletsprojects.com/) template code, and [JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript) by hand — uproot's [form fields](../building/forms.md) are not available here. Most apps are perfectly fine with the JSON editor. This page assumes you have read [Session settings](../building/data.md#session-settings).

## A minimal example

Suppose your app defines a default number of rounds in its constants class and reads it from the session settings:

```python
class C:
    DEFAULT_ROUNDS = 3
```

Create `AdminSettings.html` next to your app's `__init__.py`:

```html+jinja
{% set n_rounds = settings.get("n_rounds", C.DEFAULT_ROUNDS) %}

<div class="border rounded p-3" id="{{ editor_id }}">
    <label class="form-label" for="{{ editor_id }}-rounds">Number of rounds</label>
    <input class="form-control" id="{{ editor_id }}-rounds"
        min="1" step="1" type="number" value="{{ n_rounds }}">
</div>

<script>
registerSessionSettingsEditor("{{ editor_id }}", () => {
    const rounds = Number(document.getElementById("{{ editor_id }}-rounds").value);

    if (!Number.isInteger(rounds) || rounds < 1) {
        throw new TypeError("Number of rounds must be a positive integer.");
    }

    return { n_rounds: rounds };
});
</script>
```

Three things happen here:

1. The fragment prefills the input from `settings` (the config's defaults), falling back to `C.DEFAULT_ROUNDS` — so the form always starts at the values the session would get anyway.
2. The inline script registers a *reader* function for this editor with `registerSessionSettingsEditor`.
3. When the experimenter clicks **Create session**, the reader runs. It validates the input and returns an object whose keys are merged into the session settings. Throwing an error blocks session creation and shows the error message to the experimenter — this is your validation mechanism.

The fragment is not a full page: do not extend `Base.html` or any other template. Write only the form markup and its script. Admin pages load [Bootstrap 5](https://getbootstrap.com/docs/5.3/forms/overview/), so classes like `form-control` and `form-label` work as expected.

## Where uproot looks

- `your_app/AdminSettings.html` — used for every config that includes `your_app`. If a config contains several apps with such a file, all their forms are shown, stacked in the config's app order.
- `AdminSettings.html` at the project root — a project-level form that takes over for *all* configs; app-level fragments are then ignored.
- A fragment that renders to only whitespace is skipped, so you can opt out per config with a Jinja `{% if %}` around the whole file.
- Configs without any fragment keep the plain JSON editor.

## Template variables

Fragments are rendered server-side when the new-session page loads, once per config. They receive:

| Variable | Meaning |
|----------|---------|
| `config` | Name of the config this rendering belongs to |
| `apps` | List of app names in that config |
| `appname` | The app the fragment belongs to (`None` for a project-level fragment) |
| `settings` | The config's default settings, as declared via `load_config(..., settings={...})` |
| `editor_id` | Unique id for this editor — use it as your root element's `id` and pass it to `registerSessionSettingsEditor` |
| `C` | The app's constants class (app fragments only) |
| `appstatic` | URL helper for the app's static files (app fragments only) |

!!! warning
    The same app can appear in several configs, so your fragment may be rendered several times into the same admin page. Never hard-code element ids — always derive them from `editor_id`, as in the example above.

## The reader function

The reader you register runs when the experimenter submits the form. It receives one argument, an object with:

- `config` — the selected config's name
- `settings` — the settings collected so far: the config's defaults, already merged with the contributions of readers registered before yours

Return a JSON-serializable object; its keys are merged over those settings. Keys your form does not touch keep their default values. Return `undefined` to contribute nothing. Throw an `Error` with a human-readable message to abort session creation and display the message.

## What the experimenter sees

When a config with a custom form is selected, the **Keep default settings** checkbox starts unchecked and the form is shown, prefilled with the defaults. Checking the box hides the form and uses the config's defaults unchanged. For such configs, the custom form fully replaces the JSON editor — there is no raw JSON fallback in the UI.

If a fragment raises an error while rendering, or a config's default settings are not a JSON object, the new-session page shows a red error message for that config instead of a form, and the config falls back to the JSON editor. The full traceback lands in the server log.

## Complete example

The double auction example ships a settings form covering eight settings, including comma-separated integer lists and values that may be either a scalar or one entry per round:

:material-github: [See AdminSettings.html in the double_auction example](https://github.com/mrpg/uproot-examples/blob/master/double_auction/AdminSettings.html)
