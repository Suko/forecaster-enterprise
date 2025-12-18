#!/usr/bin/env python3
"""
Generate `docs/backend/API_REFERENCE.md` from FastAPI OpenAPI.

Usage:
  cd backend
  uv run python scripts/generate_api_reference.py --output ../docs/backend/API_REFERENCE.md
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


HTTP_METHOD_ORDER = ["get", "post", "put", "patch", "delete", "options", "head"]


def _ref_name(schema: dict[str, Any] | None) -> str | None:
    if not schema:
        return None
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        return ref.removeprefix("#/components/schemas/")
    return None


def _iter_operations(openapi: dict[str, Any]) -> Iterable[dict[str, Any]]:
    paths = openapi.get("paths") or {}
    for path, methods in sorted(paths.items(), key=lambda x: x[0]):
        if not isinstance(methods, dict):
            continue
        for method in HTTP_METHOD_ORDER:
            op = methods.get(method)
            if not isinstance(op, dict):
                continue
            yield {
                "path": path,
                "method": method.upper(),
                "operation": op,
            }


def _render_operation(op_info: dict[str, Any]) -> str:
    path: str = op_info["path"]
    method: str = op_info["method"]
    op: dict[str, Any] = op_info["operation"]

    summary = op.get("summary") or op.get("operationId") or ""
    description = op.get("description") or ""
    deprecated = bool(op.get("deprecated", False))

    lines: list[str] = []
    lines.append(f"### `{method} {path}`")
    if deprecated:
        lines.append("")
        lines.append("**Deprecated:** yes")

    if summary:
        lines.append("")
        lines.append(f"**Summary:** {summary.strip()}")

    if description:
        desc = description.strip()
        if desc:
            lines.append("")
            lines.append(desc)

    # Request body
    request_body = op.get("requestBody") or {}
    content = request_body.get("content") if isinstance(request_body, dict) else None
    if isinstance(content, dict) and content:
        lines.append("")
        lines.append("**Request Body**")
        for content_type, content_spec in sorted(content.items(), key=lambda x: x[0]):
            schema = (content_spec or {}).get("schema") if isinstance(content_spec, dict) else None
            schema_name = _ref_name(schema) or (schema.get("type") if isinstance(schema, dict) else None)
            schema_display = schema_name or "unknown"
            lines.append(f"- `{content_type}` → `{schema_display}`")

    # Responses (schemas only; details live in OpenAPI)
    responses = op.get("responses") or {}
    if isinstance(responses, dict) and responses:
        lines.append("")
        lines.append("**Responses**")
        for status_code, resp in sorted(responses.items(), key=lambda x: str(x[0])):
            if not isinstance(resp, dict):
                lines.append(f"- `{status_code}`")
                continue
            resp_desc = (resp.get("description") or "").strip()
            resp_content = resp.get("content") or {}
            schema_display: str | None = None
            if isinstance(resp_content, dict):
                json_ct = resp_content.get("application/json") or next(iter(resp_content.values()), None)
                if isinstance(json_ct, dict):
                    schema = json_ct.get("schema")
                    schema_name = _ref_name(schema) or (schema.get("type") if isinstance(schema, dict) else None)
                    schema_display = schema_name
            if schema_display:
                if resp_desc:
                    lines.append(f"- `{status_code}` `{schema_display}` — {resp_desc}")
                else:
                    lines.append(f"- `{status_code}` `{schema_display}`")
            else:
                if resp_desc:
                    lines.append(f"- `{status_code}` — {resp_desc}")
                else:
                    lines.append(f"- `{status_code}`")

    return "\n".join(lines)


def generate_markdown(openapi: dict[str, Any], base_url: str) -> str:
    today = date.today().isoformat()

    ops = list(_iter_operations(openapi))
    canonical = [o for o in ops if not bool(o["operation"].get("deprecated", False))]
    legacy = [o for o in ops if bool(o["operation"].get("deprecated", False))]

    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in canonical:
        tags = entry["operation"].get("tags") or ["other"]
        tag = tags[0] if isinstance(tags, list) and tags else "other"
        by_tag[str(tag)].append(entry)

    by_tag_legacy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in legacy:
        tags = entry["operation"].get("tags") or ["other"]
        tag = tags[0] if isinstance(tags, list) and tags else "other"
        by_tag_legacy[str(tag)].append(entry)

    lines: list[str] = []
    lines.append("# API Reference")
    lines.append("")
    lines.append("**Source of Truth:** FastAPI OpenAPI (`/openapi.json`)")
    lines.append(f"**Base URL:** `{base_url}`  ")
    lines.append(f"**Last Generated:** {today}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Quick Start (Frontend)")
    lines.append("")
    lines.append("```typescript")
    lines.append("// 1. Login")
    lines.append("const form = new URLSearchParams();")
    lines.append("form.append('username', 'user@example.com');")
    lines.append("form.append('password', 'password');")
    lines.append("")
    lines.append(f"const res = await fetch('{base_url}/api/v1/auth/login', {{")
    lines.append("  method: 'POST',")
    lines.append("  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },")
    lines.append("  body: form.toString()")
    lines.append("});")
    lines.append("const { access_token } = await res.json();")
    lines.append("")
    lines.append("// 2. Use token in requests")
    lines.append("const headers = { 'Authorization': `Bearer ${access_token}` };")
    lines.append("")
    lines.append("// 3. Example: dashboard")
    lines.append(f"const dashboard = await fetch('{base_url}/api/v1/dashboard', {{ headers }}).then(r => r.json());")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Endpoints (Canonical)")
    lines.append("")
    for tag in sorted(by_tag.keys()):
        lines.append(f"## {tag.title()}")
        lines.append("")
        for entry in sorted(by_tag[tag], key=lambda e: (e["path"], HTTP_METHOD_ORDER.index(e["method"].lower()))):
            lines.append(_render_operation(entry))
            lines.append("")

    if by_tag_legacy:
        lines.append("---")
        lines.append("")
        lines.append("## Endpoints (Legacy / Deprecated)")
        lines.append("")
        for tag in sorted(by_tag_legacy.keys()):
            lines.append(f"## {tag.title()}")
            lines.append("")
            for entry in sorted(
                by_tag_legacy[tag],
                key=lambda e: (e["path"], HTTP_METHOD_ORDER.index(e["method"].lower())),
            ):
                lines.append(_render_operation(entry))
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Path to write Markdown output to.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL shown in examples.")
    args = parser.parse_args()

    from main import app  # Import after args parsing to keep CLI responsive on import errors.

    openapi = app.openapi()
    md = generate_markdown(openapi, base_url=args.base_url.rstrip("/"))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

