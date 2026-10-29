# uproot-docs

Please go to [uproot.science](https://uproot.science/) or [github.com/mrpg/uproot](https://github.com/mrpg/uproot) unless you wish to contribute to the uproot website and documentation.

## For AI agents

If you are an agent helping someone build an uproot experiment, this repository is the documentation source. To find your way around:

- [`llms.txt`](https://uproot.science/llms.txt) on the website lists every page with a one-line summary. Each page is available as plain Markdown: append `.md` to its path (e.g., <https://uproot.science/building/forms.md>). [`llms-full.txt`](https://uproot.science/llms-full.txt) contains all pages in one file.
- In this repository, the pages are in [`docs/`](docs/), and the `nav` section of [`mkdocs.yml`](mkdocs.yml) gives their reading order. Every page starts with a `description:` line, so `grep -r '^description:' docs` prints a summary of all pages.
- Start with [`docs/getting-started/tutorial.md`](docs/getting-started/tutorial.md) for the big picture. Use [`docs/reference/`](docs/reference/) for exact signatures: fields, page methods, the Python API, the Admin REST API, and the CLI.
- Complete working experiments are in [mrpg/uproot-examples](https://github.com/mrpg/uproot-examples). The framework source is in [mrpg/uproot](https://github.com/mrpg/uproot).

## Deployment

Handled automatically.

## License

This documentation and the examples therein are licensed under the **0BSD License** (Zero-Clause BSD).

### For users and developers

You are completely free to do anything with this material. No requirements, no attribution needed, no obligations of any kind. There is no warranty.

### For contributors

By contributing to this repository, your contributions are licensed under 0BSD, granting the same unlimited freedom to everyone.

### Full license

See [LICENSE](LICENSE) for the complete 0BSD license text.
