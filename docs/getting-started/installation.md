# Installation

This guide uses [uv](https://docs.astral.sh/uv/), a fast Python package manager that handles Python installation automatically. If you prefer traditional tools, see the [pip installation guide](https://github.com/mrpg/uproot/blob/main/INSTALLATION-PIP.md).

## 1. Install uv

=== "macOS / Linux"

    ```console
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"

    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

??? note "Other installation methods"
    - **macOS with Homebrew**: `brew install uv`
    - **Windows with winget**: `winget install --id=astral-sh.uv -e`

    See the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) for more options.

After installation, you may need to restart your terminal or run `source ~/.bashrc` (Linux) / `source ~/.zshrc` (macOS) for the `uv` command to be available.

## 2. Create a project

Run the following command to create a new uproot project:

```console
uv run --with 'uproot-science[dev] @ git+https://github.com/mrpg/uproot.git@main' uproot setup my_project
```

This command:

1. Downloads and installs the latest version of uproot
2. Creates a new directory called `my_project`
3. Generates starter files including a sample experiment

You should see output like this:

```
📂 A new project has been created in 'my_project'.
✅ 'main.py' and some other files have been written.
🚶 Go to the new project directory by running
	cd my_project
📖 Get started by reading 'main.py'.
🚀 Then you may run this project using
	uv run uproot run
```

## 3. Run uproot

Navigate to your new project and run the command shown in the output above:

```console
cd my_project
uv run uproot run
```

The first run will set up a virtual environment and install dependencies automatically. You'll see:

```
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:uproot:This is uproot 0.0.1 (https://uproot.science/)
INFO:uproot:Server is running at http://127.0.0.1:8000/
```

## 4. Access the admin interface

Open your browser and go to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

The server output includes an auto-login URL that looks like:

```
Auto login:
     http://127.0.0.1:8000/admin/login/#aBcDeFgHiJkL...
```

Click this URL or copy it to your browser to log in automatically. This auto-login feature only appears when using the default administrator with an empty password.

## Set up AI-assisted development

We recommend developing uproot experiments with an agentic coding tool such as [Claude Code](https://claude.ai/code) or [Codex](https://openai.com/index/introducing-codex/). These tools understand uproot's patterns and can build pages, write form logic, set up multiplayer interactions, and debug issues far faster than working from scratch.

If your coding agent supports skills (Claude Code, Codex, and others do), install the **uproot skill** to give it deep knowledge of uproot's API:

:material-github: [mrpg/uproot-skill](https://github.com/mrpg/uproot-skill)

Follow the instructions in the repository to set it up. Once installed, the agent can work with uproot's page lifecycle, fields, SmoothOperators, data model, and multiplayer features out of the box.

!!! tip

    Even without the skill, agentic coding tools work well if you clone the [uproot-docs](https://github.com/mrpg/uproot-docs) repository alongside your project — this gives the agent direct access to all documentation source files.

## What's next?

Now that uproot is running, you can:

- **[Follow the tutorial](tutorial.md)** — Build a complete experiment step by step
- **[Explore the project structure](project-structure.md)** — Understand the generated files
- **[Browse example apps](https://github.com/mrpg/uproot-examples)** — See complete experiments you can learn from

## Troubleshooting

### uv command not found

If you get "command not found" after installing uv:

1. Close and reopen your terminal
2. Or run `source ~/.bashrc` (Linux) / `source ~/.zshrc` (macOS)
3. Or add `~/.local/bin` to your PATH manually

### Permission errors on Linux

If you encounter permission errors, make sure you're not running as root. uv is designed to work in user space.

### Port already in use

If port 8000 is already in use, you can specify a different port:

```console
uv run uproot run --port 8001
```

### Getting help

- **GitHub issues**: [github.com/mrpg/uproot/issues](https://github.com/mrpg/uproot/issues)
- **Mailing list**: Contact [max@uproot.science](mailto:max@uproot.science) to join
