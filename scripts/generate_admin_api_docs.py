"""Generate Markdown documentation from FastAPI’s OpenAPI schema."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI

DOCS_REPO = Path(__file__).resolve().parents[1]
UPROOT_SRC = DOCS_REPO.parent / "uproot" / "src"
sys.path.insert(0, str(UPROOT_SRC))

from uproot.server4 import router

APP = FastAPI(title="uproot Admin API", version="1.0.0")
APP.include_router(router)
SCHEMA = APP.openapi()
SCHEMAS = SCHEMA.get("components", {}).get("schemas", {})

SECTION_NAMES = (
    "Dashboard and configurations",
    "Sessions",
    "Players",
    "Admin chat",
    "Data export",
    "Digests and pipelines",
    "Rooms",
    "System",
)

METHOD_ORDER = {"get": 0, "post": 1, "patch": 2, "delete": 3, "put": 4}

PREFIX = "/admin/api/v1"
NOWRAP = "{ .text-nowrap }"

# FastAPI documents every route as returning JSON. These are the routes that
# actually return something else or have errors specific to them.
RESPONSE_OVERRIDES: dict[tuple[str, str], list[tuple[str, str, str]]] = {
    ("GET", "/sessions/{sname}/data/export/"): [
        ("200", "application/zip", "ZIP briefcase"),
    ],
    ("GET", "/sessions/{sname}/data/jsonl/"): [
        ("200", "application/jsonl", "JSONL stream"),
    ],
    ("GET", "/sessions/{sname}/digests/{appname}/html/"): [
        ("200", "text/html", "Rendered fragment"),
    ],
    ("GET", "/sessions/{sname}/pipelines/{appname}/html/"): [
        ("200", "text/html", "Rendered fragment"),
    ],
    ("GET", "/sessions/{sname}/pipelines/{appname}/runs/"): [
        ("200", "text/plain", "Pipeline result"),
        ("200", "text/csv", "Custom data export with `filetype=csv`"),
        ("200", "application/jsonl", "Custom data export with `filetype=jsonl`"),
    ],
    ("POST", "/sessions/{sname}/pipelines/{appname}/runs/"): [
        ("200", "text/plain", "Pipeline result"),
        ("200", "text/csv", "Custom data export with `filetype=csv`"),
        ("200", "application/jsonl", "Custom data export with `filetype=jsonl`"),
    ],
    ("GET", "/praise/"): [
        ("200", "text/plain", "Praise text"),
        ("502", "application/json", "Praise could not be fetched from upstream"),
    ],
    ("POST", "/auth/login/"): [
        ("201", "application/json", "Successful response"),
        ("401", "application/json", "Invalid admin credentials"),
        ("429", "application/json", "Too many failed login attempts"),
    ],
    ("GET", "/database/dump/"): [
        ("200", "application/gzip", "Gzip-compressed database dump"),
    ],
}


def typographic(text: str) -> str:
    parts = text.split("`")
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("'", "’")
    return "`".join(parts)


def clean_text(value: str) -> str:
    return typographic(" ".join(str(value).strip().split()))


def code_cell(value: str) -> str:
    return f"`{value}`{NOWRAP}"


def requires_bearer(endpoint: dict[str, Any]) -> bool:
    return any(
        param.get("in") == "header" and param.get("name", "").lower() == "authorization"
        for param in endpoint["parameters"]
    )


def table_text(value: str) -> str:
    return clean_text(value).replace("|", "\\|")


def schema_type(schema: dict[str, Any]) -> str:
    if not schema:
        return "any"

    if "$ref" in schema:
        return f"{schema['$ref'].split('/')[-1]}"

    if "anyOf" in schema:
        parts = [schema_type(part) for part in schema["anyOf"]]
        return " or ".join(dict.fromkeys(parts))

    if "allOf" in schema:
        parts = [schema_type(part) for part in schema["allOf"]]
        return " & ".join(dict.fromkeys(parts))

    if "enum" in schema:
        return " or ".join(f"`{item}`" for item in schema["enum"])

    stype = schema.get("type")
    if stype == "array":
        return f"array[{schema_type(schema.get('items', {}))}]"
    if stype == "object":
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            return f"object[string, {schema_type(additional)}]"
        return "object"
    if stype is None:
        return "any"
    return str(stype)


def schema_constraints(schema: dict[str, Any]) -> str:
    constraints = []

    for source, label in (
        ("minimum", "min"),
        ("maximum", "max"),
        ("exclusiveMinimum", "exclusive min"),
        ("exclusiveMaximum", "exclusive max"),
        ("minLength", "min length"),
        ("maxLength", "max length"),
        ("minItems", "min items"),
        ("maxItems", "max items"),
    ):
        if source in schema:
            constraints.append(f"{label}: `{schema[source]}`")

    return "; ".join(constraints)


def format_params(params: list[dict[str, Any]], where: str) -> str:
    chosen = [p for p in params if p.get("in") == where]
    if where == "header":
        chosen = [p for p in chosen if p.get("name", "").lower() != "authorization"]

    if not chosen:
        return ""

    lines = [
        "| Parameter | Type | Required | Description |",
        "|-----------|------|----------|-------------|",
    ]

    for param in chosen:
        pschema = param.get("schema", {})
        desc = table_text(param.get("description", ""))
        constraints = schema_constraints(pschema)
        if constraints:
            desc = f"{desc} ({constraints})" if desc else constraints
        lines.append(
            f"| {code_cell(param['name'])} | {schema_type(pschema)} | "
            f"{'Yes' if param.get('required') else 'No'} | {desc} |"
        )

    return "\n".join(lines)


def request_body_schema(request_body: dict[str, Any] | None) -> dict[str, Any] | None:
    if not request_body:
        return None

    content = request_body.get("content", {})
    for media_type in ("application/json", "application/x-www-form-urlencoded"):
        schema = content.get(media_type, {}).get("schema")
        if schema:
            return schema
    return None


def dereference(schema: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    if "$ref" in schema:
        model_name = schema["$ref"].split("/")[-1]
        return model_name, SCHEMAS.get(model_name, {})
    return None, schema


def format_request_body(request_body: dict[str, Any] | None) -> str:
    schema = request_body_schema(request_body)
    if not schema:
        return ""

    model_name, body = dereference(schema)
    props = body.get("properties", {})
    required = set(body.get("required", []))

    if not props:
        return ""

    title = "**Request body**"
    if model_name:
        title += f" (`{model_name}`)"
    title += ":"

    lines = [
        title,
        "",
        "| Field | Type | Required | Description |",
        "|-------|------|----------|-------------|",
    ]

    for name, prop in props.items():
        desc = table_text(prop.get("description", ""))
        constraints = schema_constraints(prop)
        if "default" in prop:
            constraints = "; ".join(
                part for part in (constraints, f"default: `{prop['default']}`") if part
            )
        if constraints:
            desc = f"{desc} ({constraints})" if desc else constraints
        lines.append(
            f"| {code_cell(name)} | {schema_type(prop)} | "
            f"{'Yes' if name in required else 'No'} | {desc} |"
        )

    return "\n".join(lines)


def response_rows(endpoint: dict[str, Any]) -> list[tuple[str, str, str]]:
    key = (endpoint["method"], endpoint["path"].removeprefix(PREFIX))
    if key in RESPONSE_OVERRIDES:
        return RESPONSE_OVERRIDES[key]

    rows = []
    for status, response in endpoint["responses"].items():
        if status == "422":
            continue
        content = response.get("content", {})
        media_types = ", ".join(content) or "-"
        desc = response.get("description", "")
        if desc == "Successful Response":
            desc = "Successful response"
        rows.append((status, media_types, desc))

    return rows


def format_responses(endpoint: dict[str, Any]) -> str:
    rows = response_rows(endpoint)
    if not rows:
        return ""

    lines = [
        "**Responses**:",
        "",
        "| Status | Content | Description |",
        "|--------|---------|-------------|",
    ]

    for status, media_type, desc in rows:
        content = code_cell(media_type) if media_type != "-" else "-"
        lines.append(f"| `{status}` | {content} | {table_text(desc)} |")

    return "\n".join(lines)


def section_for(path: str) -> str:
    if (
        "/auth/" in path
        or "/database/" in path
        or "/status/" in path
        or "/announcements/" in path
        or "/praise/" in path
    ):
        return "System"
    if "/admin-chat" in path:
        return "Admin chat"
    if "/data/" in path:
        return "Data export"
    if "/digests/" in path or "/pipelines/" in path:
        return "Digests and pipelines"
    if "/players/" in path or "/online-players/" in path or "/multiview/" in path:
        return "Players"
    if "/rooms/" in path:
        return "Rooms"
    if "/dashboard/" in path or "/configs" in path:
        return "Dashboard and configurations"
    if "/sessions" in path:
        return "Sessions"
    return "System"


def operation_sort_key(endpoint: dict[str, Any]) -> tuple[str, int]:
    return endpoint["path"], METHOD_ORDER.get(endpoint["method"].lower(), 99)


def collect_endpoints() -> dict[str, list[dict[str, Any]]]:
    sections: dict[str, list[dict[str, Any]]] = {name: [] for name in SECTION_NAMES}

    for path, methods in SCHEMA.get("paths", {}).items():
        for method, details in methods.items():
            if method not in METHOD_ORDER:
                continue

            endpoint = {
                "method": method.upper(),
                "path": path,
                "summary": details.get("summary", ""),
                "description": details.get("description", ""),
                "parameters": details.get("parameters", []),
                "requestBody": details.get("requestBody"),
                "responses": details.get("responses", {}),
            }
            sections[section_for(path)].append(endpoint)

    return sections


def endpoint_notes(endpoint: dict[str, Any]) -> list[str]:
    path = endpoint["path"]
    method = endpoint["method"]
    notes = []

    if not requires_bearer(endpoint):
        notes.append("This endpoint does not require a Bearer token.")
    if path.endswith("/pipelines/{appname}/runs/") and method == "GET":
        notes.append(
            "This endpoint never passes data to the pipeline, even if you send a request "
            "body. Use `POST` to pass data."
        )
    if path.endswith("/pipelines/{appname}/runs/") and method == "POST":
        notes.append(
            "This endpoint accepts an optional JSON request body. If the app’s `pipeline()` "
            "callable declares a `data` parameter, the decoded body is passed as `data`. "
            "A body that is not valid JSON fails with `400`."
        )
    if path.endswith("/pipelines/{appname}/runs/"):
        notes.append(
            "If the pipeline returns a custom data export, it is downloaded as CSV or JSONL, "
            "depending on `filetype`. Any other result is returned as plain text. `filetype` "
            "must be `csv` or `jsonl`; any other value fails with `400` before the pipeline "
            "runs."
        )
    if path.endswith("/database/dump/"):
        notes.append(
            "The response is a gzip-compressed MessagePack dump intended for "
            "`uproot restore`, not JSON."
        )
    if path.endswith("/auth/login/"):
        notes.append(
            "Login attempts are rate-limited per IP address. After 50 failed attempts "
            "within one hour, the IP is blocked for six hours. Requests from localhost "
            "are exempt."
        )
    if path.endswith("/announcements/dismiss/"):
        notes.append(
            "The nudge stays silent for ten years. The dashboard’s `nudge_announcements` "
            "reflects this."
        )
    if path.endswith("/dashboard/"):
        notes.append(
            "The response contains `uproot_version`, `nudge_announcements` (whether the "
            "admin UI currently nudges you to check announcements), `configs`, `rooms`, "
            "and `active_sessions`."
        )
    if path.endswith("/players/fields/"):
        notes.append(
            "Field names must be valid Python identifiers (letters, digits, and "
            "underscores, not starting with a digit). They are checked before anything "
            "is written: if any name is invalid, the request fails with `400` and no "
            "player is changed."
        )
    if path.endswith("/players/{uname}/") and endpoint["method"] == "GET":
        notes.append(
            "Pass `fields` repeatedly to choose fields, e.g. `?fields=id&fields=page_order`. "
            "Omitting it returns the same default fields as the all-players endpoint."
        )
    if path.endswith("/digests/html/"):
        notes.append(
            "`apps` lists every app with a digest. `html` only contains entries for apps "
            "that provide an `AdminDigest.html` template."
        )
    if path.endswith("/rooms/{roomname}/sessions/") and endpoint["method"] == "POST":
        notes.append(
            "If `config` is omitted, the room’s default configuration is used. If the room "
            "has none either, the request fails with `400`."
        )
    if path.endswith(("/auth/logout/", "/auth/logout-all/")):
        notes.append(
            "This revokes browser admin-login sessions. It does not revoke API keys."
        )
    if path.endswith("/auth/sessions/{user}/"):
        notes.append(
            "This revokes browser admin-login sessions for the named user. It does not revoke API keys."
        )

    return notes


def render() -> str:
    sections = collect_endpoints()
    output: list[str] = []

    output.extend(
        [
            "# Admin API reference",
            "",
            "The Admin REST API provides programmatic access to manage uproot experiments.",
            "All endpoints are located under `/admin/api/v1/` and require Bearer token authentication, except where noted.",
            "",
            '!!! note "Generated from FastAPI OpenAPI"',
            "    This page is generated by `scripts/generate_admin_api_docs.py` from FastAPI’s OpenAPI schema. A running uproot server also exposes FastAPI’s live schema at `/openapi.json` and interactive documentation at `/docs` and `/redoc`.",
            "",
            "## Authentication",
            "",
            "All requests must include an `Authorization` header with a valid API token:",
            "",
            "```http",
            "Authorization: Bearer YOUR_API_TOKEN",
            "```",
            "",
            "To enable API access, add one or more tokens in your project’s `main.py`:",
            "",
            "```python",
            'upd.API_KEYS.add("YOUR_API_TOKEN")',
            "```",
            "",
            "## Errors",
            "",
            "Errors are returned as JSON with a `detail` field:",
            "",
            "```json",
            '{"detail": "Session not found"}',
            "```",
            "",
            "These status codes are shared by many endpoints and are not repeated below:",
            "",
            "| Status | Meaning |",
            "|--------|---------|",
            "| `400` | The request is invalid, e.g. an unknown configuration or a duplicate name |",
            "| `401` | The Bearer token is missing or invalid |",
            "| `404` | A session, player, room, configuration, digest, or pipeline named in the request does not exist |",
            "| `422` | Parameters or request body do not match the expected types; `detail` is a list of problems |",
            "",
            "The **Responses** tables below list successful responses and errors specific to one endpoint.",
            "",
            "## CLI access",
            "",
            "The `uproot api` command calls these endpoints from the command line:",
            "",
            "```bash",
            'export UPROOT_API_KEY="YOUR_API_TOKEN"',
            "uproot api sessions",
            "uproot api sessions/mysession",
            "uproot api rooms",
            "uproot api rooms/waiting-room",
            "uproot api sessions/mysession/online-players",
            "uproot api sessions/mysession/players/ABC",
            'uproot api -X POST sessions -d \'{"config": "myconfig", "n_players": 4}\'',
            "uproot api -X PATCH sessions/mysession/active -d '{\"active\": false}'",
            'uproot api -X POST sessions/mysession/players/advance -d \'{"unames": ["ABC"]}\'',
            "```",
            "",
        ]
    )

    for section, endpoints in sections.items():
        if not endpoints:
            continue

        output.append(f"## {section}")
        output.append("")

        for endpoint in sorted(endpoints, key=operation_sort_key):
            output.append(f"### `{endpoint['method']} {endpoint['path']}`")
            output.append("")

            description = clean_text(
                endpoint.get("description") or endpoint.get("summary") or ""
            )
            if description:
                output.append(description)
                output.append("")

            for note in endpoint_notes(endpoint):
                output.append(f"!!! note\n    {note}")
                output.append("")

            path_params = format_params(endpoint["parameters"], "path")
            if path_params:
                output.append("**Path parameters**:")
                output.append("")
                output.append(path_params)
                output.append("")

            query_params = format_params(endpoint["parameters"], "query")
            if query_params:
                output.append("**Query parameters**:")
                output.append("")
                output.append(query_params)
                output.append("")

            request_body = format_request_body(endpoint.get("requestBody"))
            if request_body:
                output.append(request_body)
                output.append("")

            responses = format_responses(endpoint)
            if responses:
                output.append(responses)
                output.append("")

            output.append("---")
            output.append("")

    return "\n".join(output).rstrip() + "\n"


if __name__ == "__main__":
    print(render(), end="")
