#!/usr/bin/env python3
"""Generate Markdown documentation from FastAPI's OpenAPI schema."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI

DOCS_REPO = Path(__file__).resolve().parents[1]
UPROOT_SRC = DOCS_REPO.parent / "uproot" / "src"
sys.path.insert(0, str(UPROOT_SRC))

from uproot.server4 import router  # noqa: E402

APP = FastAPI(title="uproot Admin API", version="1.0.0")
APP.include_router(router)
SCHEMA = APP.openapi()
SCHEMAS = SCHEMA.get("components", {}).get("schemas", {})

SECTION_NAMES = (
    "Dashboard and Configurations",
    "Sessions",
    "Players",
    "Admin Chat",
    "Data Export",
    "Digests and Pipelines",
    "Rooms",
    "System",
)

METHOD_ORDER = {"get": 0, "post": 1, "patch": 2, "delete": 3, "put": 4}


def clean_text(value: str) -> str:
    return " ".join(str(value).strip().split())


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
            f"| `{param['name']}` | {schema_type(pschema)} | "
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
            f"| `{name}` | {schema_type(prop)} | "
            f"{'Yes' if name in required else 'No'} | {desc} |"
        )

    return "\n".join(lines)


def format_responses(responses: dict[str, Any]) -> str:
    if not responses:
        return ""

    lines = [
        "**Responses**:",
        "",
        "| Status | Content | Description |",
        "|--------|---------|-------------|",
    ]

    for status, response in responses.items():
        if status == "422":
            continue
        content = response.get("content", {})
        media_types = ", ".join(f"`{name}`" for name in content) or "-"
        desc = table_text(response.get("description", ""))
        lines.append(f"| `{status}` | {media_types} | {desc} |")

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
        return "Admin Chat"
    if "/data/" in path or "/page-times/" in path:
        return "Data Export"
    if "/digests/" in path or "/pipelines/" in path:
        return "Digests and Pipelines"
    if "/players/" in path or "/multiview/" in path:
        return "Players"
    if "/rooms/" in path:
        return "Rooms"
    if "/dashboard/" in path or "/configs" in path:
        return "Dashboard and Configurations"
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
    notes = []

    if path.endswith("/pipelines/{appname}/runs/"):
        notes.append(
            "This endpoint accepts an optional JSON request body. If the app's `pipeline()` "
            "callable declares a `data` parameter, the decoded body is passed as `data`."
        )
    if path.endswith("/database/dump/"):
        notes.append(
            "The response is a binary MessagePack dump intended for `uproot restore`, not JSON."
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
            "All endpoints are located under `/admin/api/v1/` and require Bearer token authentication.",
            "",
            '!!! note "Generated from FastAPI OpenAPI"',
            "    This page is generated by `scripts/generate_admin_api_docs.py` from FastAPI's OpenAPI schema. A running uproot server also exposes FastAPI's live schema at `/openapi.json` and interactive documentation at `/docs` and `/redoc`.",
            "",
            "## Authentication",
            "",
            "All requests must include an `Authorization` header with a valid API token:",
            "",
            "```http",
            "Authorization: Bearer YOUR_API_TOKEN",
            "```",
            "",
            "To enable API access, add one or more tokens in your project's `main.py`:",
            "",
            "```python",
            'upd.API_KEYS.add("YOUR_API_TOKEN")',
            "```",
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
            "uproot api sessions/mysession/players/online",
            'uproot api -X POST sessions -d \'{"config": "myconfig", "n_players": 4}\'',
            "uproot api -X PATCH sessions/mysession/active",
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

            responses = format_responses(endpoint.get("responses", {}))
            if responses:
                output.append(responses)
                output.append("")

            output.append("---")
            output.append("")

    return "\n".join(output).rstrip() + "\n"


if __name__ == "__main__":
    print(render(), end="")
