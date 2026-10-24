# Upgrading

uproot projects pin a specific version so that a new release does not change the software used in your study. You can keep that reproducibility and still upgrade deliberately when you are ready.

This page assumes you have an existing project set up with [uv](getting-started/installation.md).

!!! warning "Check announcements as often as possible"
    In the [admin interface](running/admin.md#announcements), open **Status** (`/admin/status/`) and click **Check for important announcements**. Do this as often as possible—ideally every time you open the admin interface, and always before collecting data or upgrading.

    The check shows the recommended version and important notices, including security fixes and messages for your installed version. **uproot does not check automatically.**

    You can also [check from the terminal](reference/cli.md#uproot-announcements): `uv run uproot announcements`.

## Upgrade and keep an exact pin

Check [uproot-science on PyPI](https://pypi.org/project/uproot-science/) for the latest release. Stop your running server with ++ctrl+c++ in its terminal.

In your project directory—the folder containing `main.py` and `pyproject.toml`—run these commands. **Replace `X.Y.Z` with the release you want to use**; it is an example version here.

```console
uv add "uproot-science==X.Y.Z"
uv run uproot --version
```

The `==` is an **exact version pin**: it requires that particular version. Despite its name, [`uv add`](https://docs.astral.sh/uv/concepts/projects/dependencies/#changing-dependencies) also updates existing dependencies. It replaces the old pin in `pyproject.toml`, updates `uv.lock`, and installs the selected release and any required changes to other packages.

Restart with `uv run uproot run` and test your experiment before collecting data with the new version.

## Keep your study reproducible

The pin in `pyproject.toml` specifies your uproot version. The **lockfile**, `uv.lock`, records exact versions of the other Python packages your project needs, too. Keep both files with your experiment code, and archive the project version used for each dataset. If you use Git, commit both files together.

To recreate that software environment on another computer, use the saved project and run:

```console
uv sync --locked
```

This installs the recorded versions. `--locked` reports an error if the lockfile needs updating, so mismatched project files do not silently change your environment. Ordinary `uv sync` and `uv run` also reuse locked versions when they still satisfy your project’s requirements. See [uv’s lockfile documentation](https://docs.astral.sh/uv/concepts/projects/sync/).

## Editing the pin yourself

You can instead change the version after `==` in the `uproot-science` entry under `dependencies` in `pyproject.toml`, then run `uv sync`. Keep the other dependencies as they are.

Running `uv sync --upgrade-package uproot-science` alone respects the existing pin, so it cannot upgrade past that version.

If your [deployment](running/deployment.md) installs from `requirements.txt`, update its uproot pin to the same version too; `uv add` does not update that file.
