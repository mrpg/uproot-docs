"""Make the documentation easy to find and read for AI agents.

At build time, this hook writes:

- a Markdown copy of every page next to its HTML (``/building/forms.md`` for
  ``/building/forms/``), with MkDocs-only syntax removed and links made absolute,
- ``/llms.txt``, an index of all pages following https://llmstxt.org/,
- ``/llms-full.txt``, all pages concatenated in navigation order,

and adds ``<link rel="alternate" type="text/markdown">`` to every page’s HTML.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path

from mkdocs.structure.nav import Section

PAGES: dict[str, dict[str, str]] = {}
NAV = []

LLMS_INTRO = """\
uproot is a modern, open-source Python framework for developing and conducting \
browser-based behavioral experiments (surveys, games, real-time multiplayer \
interactions). Experiments are Python packages: pages are classes, templates \
are Jinja2, and all data goes into an append-only log.

Notes for agents:

- Every page below is available as clean Markdown: append `.md` to the page \
path (e.g., https://uproot.science/building/forms.md). \
`llms-full.txt` contains all pages in one file.
- uproot app modules get everything via `from uproot.smithereens import *`; \
no manual imports are needed in examples.
- Complete working experiments: https://github.com/mrpg/uproot-examples \
(branch `main`). Framework source: https://github.com/mrpg/uproot. \
Documentation source: https://github.com/mrpg/uproot-docs.
- An agent skill with condensed API knowledge: https://github.com/mrpg/uproot-skill
- To try an experiment locally, run `uproot start --simulate` inside a project.
"""

FENCE = re.compile(r"^\s*(```|~~~)")
LINK = re.compile(r"(\]\()([^)\s]+)(\))")
EMOJI = re.compile(
    r":(?:material|fontawesome|octicons|simple)-[a-z0-9-]+:(\{[^}]*\})?\s*"
)
ATTR_TRAILING = re.compile(r"\s*\{\s*[:.#][^}]*\}\s*$")
ATTR_LINE = re.compile(r"^\s*\{:[^}]*\}\s*$")
ENTITY = re.compile(r"&#x202F;|&shy;")


def _clean(markdown: str, src_uri: str, site_url: str) -> str:
    """Strip MkDocs-only syntax and turn relative links into absolute .md URLs."""
    base = posixpath.dirname(src_uri)
    out, in_fence = [], False

    def fix_link(m: re.Match[str]) -> str:
        target = m.group(2)
        if re.match(r"^[a-z][a-z0-9+.-]*:|^#|^/", target, re.IGNORECASE):
            return m.group(0)
        path, _, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(base, path))
        url = site_url + resolved + (f"#{anchor}" if anchor else "")
        return f"{m.group(1)}{url}{m.group(3)}"

    for line in markdown.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        if in_fence or FENCE.match(line):
            out.append(line)
            continue
        if ATTR_LINE.match(line):
            continue
        line = ENTITY.sub("", line)
        line = EMOJI.sub("", line)
        line = ATTR_TRAILING.sub("", line)
        line = LINK.sub(fix_link, line)
        out.append(line)

    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def on_nav(nav, config, files):
    NAV[:] = nav.items
    return nav


def on_page_markdown(markdown, page, config, files):
    site_url = config["site_url"]
    PAGES[page.file.src_uri] = {
        "title": page.title or "",
        "description": page.meta.get("description", ""),
        "markdown": _clean(markdown, page.file.src_uri, site_url),
    }
    return markdown


def on_post_page(output, page, config):
    href = config["site_url"] + page.file.src_uri
    tag = f'<link rel="alternate" type="text/markdown" href="{href}">'
    return output.replace("</head>", f"  {tag}\n  </head>", 1)


def _walk(items):
    """Yield (section title or None, page) in navigation order."""
    for item in items:
        if isinstance(item, Section):
            for _, page in _walk(item.children):
                yield item.title, page
        elif getattr(item, "is_page", False):
            yield None, item


def on_post_build(config):
    site_dir = Path(config["site_dir"])
    site_url = config["site_url"]

    for src_uri, info in PAGES.items():
        target = site_dir / src_uri
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(info["markdown"], encoding="utf-8")

    sections: dict[str, list[str]] = {}
    ordered: list[str] = []
    for section, page in _walk(NAV):
        src_uri = page.file.src_uri
        if src_uri not in PAGES:
            continue
        ordered.append(src_uri)
        sections.setdefault(section or "Overview", []).append(src_uri)

    lines = [f"# {config['site_name']}", "", f"> {config['site_description']}", ""]
    lines.append(LLMS_INTRO)
    for section, uris in sections.items():
        lines += [f"## {section}", ""]
        for uri in uris:
            info = PAGES[uri]
            entry = f"- [{info['title']}]({site_url}{uri})"
            if info["description"]:
                entry += f": {info['description']}"
            lines.append(entry)
        lines.append("")
    lines += [
        "## Optional",
        "",
        (
            f"- [Full documentation in one file]({site_url}llms-full.txt): "
            "every page above, concatenated in navigation order"
        ),
        "",
    ]
    (site_dir / "llms.txt").write_text("\n".join(lines), encoding="utf-8")

    full = [
        f"# {config['site_name']} documentation\n\n> {config['site_description']}\n"
    ]
    for uri in ordered:
        info = PAGES[uri]
        full.append(f"\n---\n\nSource: {site_url}{uri}\n\n{info['markdown']}")
    (site_dir / "llms-full.txt").write_text("".join(full), encoding="utf-8")
