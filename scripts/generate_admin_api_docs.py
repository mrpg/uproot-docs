#!/usr/bin/env python3
"""
Generate markdown documentation from the uproot admin API (server4.py).
Uses FastAPI's OpenAPI schema generation.

Usage:
    python scripts/generate_admin_api_docs.py > docs/reference/admin-api.md

Then manually review and edit the output as needed.
"""

import sys
sys.path.insert(0, "../uproot/src")

from fastapi import FastAPI
from uproot.server4 import router

# Create a minimal FastAPI app and include the router
app = FastAPI(title="uproot Admin API", version="1.0.0")
app.include_router(router)

# Get the OpenAPI schema
schema = app.openapi()


def format_params(params, include_required=True):
    """Format parameters as markdown table."""
    if not params:
        return ""

    if include_required:
        lines = ["| Parameter | Type | Required | Description |",
                 "|-----------|------|----------|-------------|"]
    else:
        lines = ["| Parameter | Type | Description |",
                 "|-----------|------|-------------|"]

    for p in params:
        required = "Yes" if p.get("required", False) else "No"
        ptype = p.get("schema", {}).get("type", "string")
        desc = p.get("description", "")
        if include_required:
            lines.append(f"| `{p['name']}` | {ptype} | {required} | {desc} |")
        else:
            lines.append(f"| `{p['name']}` | {ptype} | {desc} |")
    return "\n".join(lines)


def format_request_body(body_schema, schemas):
    """Format request body as markdown."""
    if not body_schema:
        return ""

    ref = body_schema.get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "")
    if ref:
        model_name = ref.split("/")[-1]
        model = schemas.get(model_name, {})
        props = model.get("properties", {})
        required = model.get("required", [])

        lines = [f"\n**Request body** (`{model_name}`):\n",
                 "| Field | Type | Required | Description |",
                 "|-------|------|----------|-------------|"]
        for name, prop in props.items():
            ptype = prop.get("type", prop.get("$ref", "").split("/")[-1] if "$ref" in prop else "any")
            if "items" in prop:
                item_type = prop["items"].get("type", "any")
                ptype = f"array[{item_type}]"
            req = "Yes" if name in required else "No"
            desc = prop.get("description", "")
            default = prop.get("default")
            if default is not None:
                desc += f" (default: `{default}`)"
            lines.append(f"| `{name}` | {ptype} | {req} | {desc} |")
        return "\n".join(lines)
    return ""


# Group endpoints by tag/section
sections = {
    "Sessions": [],
    "Players": [],
    "Data export": [],
    "Rooms": [],
    "Configurations": [],
    "System": [],
}

schemas = schema.get("components", {}).get("schemas", {})

for path, methods in schema.get("paths", {}).items():
    for method, details in methods.items():
        if method in ("get", "post", "patch", "delete", "put"):
            endpoint = {
                "method": method.upper(),
                "path": path,
                "summary": details.get("summary", ""),
                "description": details.get("description", ""),
                "parameters": details.get("parameters", []),
                "requestBody": details.get("requestBody"),
                "responses": details.get("responses", {}),
            }

            # Categorize based on path
            if "/sessions/" in path or ("/session/" in path and "/players" not in path and "/data" not in path and "/digest" not in path and "/page-times" not in path):
                sections["Sessions"].append(endpoint)
            elif "/players/" in path:
                sections["Players"].append(endpoint)
            elif "/data/" in path or "/page-times/" in path:
                sections["Data export"].append(endpoint)
            elif "/room" in path:
                sections["Rooms"].append(endpoint)
            elif "/config" in path:
                sections["Configurations"].append(endpoint)
            else:
                sections["System"].append(endpoint)

# Generate markdown
output = []
output.append("# Admin API reference")
output.append("")
output.append("The Admin REST API provides programmatic access to manage uproot experiments.")
output.append("All endpoints are located under `/admin/api/` and require Bearer token authentication.")
output.append("")
output.append("## Authentication")
output.append("")
output.append("All requests must include an `Authorization` header with a valid API token:")
output.append("")
output.append("```")
output.append("Authorization: Bearer YOUR_API_TOKEN")
output.append("```")
output.append("")
output.append("API tokens are configured in `deployment.API_KEYS`.")
output.append("")

for section_name, endpoints in sections.items():
    if not endpoints:
        continue

    output.append(f"## {section_name}")
    output.append("")

    for ep in endpoints:
        output.append(f"### `{ep['method']} {ep['path']}`")
        output.append("")
        if ep["summary"]:
            # Convert CamelCase to sentence
            summary = ep["summary"].replace("_", " ")
            output.append(summary)
            output.append("")

        # Path parameters
        path_params = [p for p in ep["parameters"] if p.get("in") == "path"]
        query_params = [p for p in ep["parameters"] if p.get("in") == "query"]

        if path_params:
            output.append("**Path parameters**:")
            output.append("")
            output.append(format_params(path_params, include_required=False))
            output.append("")

        if query_params:
            output.append("**Query parameters**:")
            output.append("")
            output.append(format_params(query_params))
            output.append("")

        body = format_request_body(ep["requestBody"], schemas)
        if body:
            output.append(body)
            output.append("")

        output.append("**Response**: Successful Response")
        output.append("")
        output.append("---")
        output.append("")

print("\n".join(output))
