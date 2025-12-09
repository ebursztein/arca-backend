#!/usr/bin/env python3
"""
API Documentation Generator for Arca Backend

Programmatically extracts Cloud Function signatures and Pydantic model definitions
to generate accurate, complete API documentation for iOS integration.

Usage:
    uv run python generate_api_docs.py

Output:
    docs/PUBLIC_API_GENERATED.md
"""

import ast
import inspect
import re
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo


# =============================================================================
# Configuration
# =============================================================================

OUTPUT_FILE = Path(__file__).parent.parent / "docs" / "PUBLIC_API_GENERATED.md"
MAIN_PY = Path(__file__).parent / "main.py"
CONVERSATION_HELPERS_PY = Path(__file__).parent / "conversation_helpers.py"
ASK_THE_STARS_PY = Path(__file__).parent / "ask_the_stars.py"


# =============================================================================
# Type Formatting
# =============================================================================

def format_type(annotation: Any, simplify: bool = True) -> str:
    """Format a type annotation to a readable string for iOS developers."""
    if annotation is None or annotation is type(None):
        return "null"

    # Handle string annotations
    if isinstance(annotation, str):
        return annotation

    # Handle forward references
    if hasattr(annotation, "__forward_arg__"):
        return annotation.__forward_arg__

    # Get origin for generic types
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Optional[X] -> X | null
    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return f"{format_type(non_none[0])} | null"
        return " | ".join(format_type(a) for a in args)

    # Literal["a", "b"] -> "a" | "b"
    if origin is Literal:
        return " | ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in args)

    # list[X] -> X[]
    if origin is list:
        if args:
            return f"{format_type(args[0])}[]"
        return "array"

    # dict[K, V] -> object
    if origin is dict:
        if args and len(args) == 2:
            return f"object<{format_type(args[0])}, {format_type(args[1])}>"
        return "object"

    # Handle Enum
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        values = [f'"{m.value}"' for m in annotation]
        if len(values) <= 4:
            return " | ".join(values)
        return f"string (enum: {annotation.__name__})"

    # Handle Pydantic models
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.__name__

    # Basic types
    type_map = {
        str: "string",
        int: "int",
        float: "float",
        bool: "boolean",
        dict: "object",
        list: "array",
        Any: "any",
    }

    if annotation in type_map:
        return type_map[annotation]

    # Fallback
    if hasattr(annotation, "__name__"):
        return annotation.__name__

    return str(annotation)


def extract_constraints(field_info: FieldInfo) -> str:
    """Extract constraints from a Pydantic FieldInfo."""
    constraints = []

    metadata = getattr(field_info, "metadata", [])
    for m in metadata:
        if hasattr(m, "ge"):
            constraints.append(f">= {m.ge}")
        if hasattr(m, "le"):
            constraints.append(f"<= {m.le}")
        if hasattr(m, "gt"):
            constraints.append(f"> {m.gt}")
        if hasattr(m, "lt"):
            constraints.append(f"< {m.lt}")
        if hasattr(m, "min_length"):
            constraints.append(f"min_length: {m.min_length}")
        if hasattr(m, "max_length"):
            constraints.append(f"max_length: {m.max_length}")
        if hasattr(m, "pattern"):
            constraints.append(f"pattern: {m.pattern}")

    # Also check direct attributes on field_info
    if hasattr(field_info, "ge") and field_info.ge is not None:
        constraints.append(f">= {field_info.ge}")
    if hasattr(field_info, "le") and field_info.le is not None:
        constraints.append(f"<= {field_info.le}")

    return ", ".join(constraints) if constraints else "-"


# =============================================================================
# Model Extraction
# =============================================================================

def extract_pydantic_model(model_class: type) -> dict:
    """Extract complete field info from a Pydantic model."""
    fields = {}

    for name, field_info in model_class.model_fields.items():
        annotation = field_info.annotation

        # Check if required
        is_required = field_info.is_required()

        # Get default
        default = field_info.default
        if default is None and not is_required:
            default_str = "null"
        elif default is not None and not callable(default):
            default_str = repr(default)
        else:
            default_str = "-"

        fields[name] = {
            "type": format_type(annotation),
            "required": is_required,
            "default": default_str,
            "constraints": extract_constraints(field_info),
            "description": field_info.description or "-",
        }

    return fields


def extract_enum(enum_class: type) -> list[dict]:
    """Extract enum values."""
    return [{"name": m.name, "value": m.value} for m in enum_class]


# =============================================================================
# Function Extraction from main.py
# =============================================================================

def parse_python_file(filepath: Path, decorator_pattern: str = "https_fn.on_call") -> list[dict]:
    """Parse a Python file to extract Cloud Function definitions."""
    if not filepath.exists():
        return []

    with open(filepath, "r") as f:
        source = f.read()

    tree = ast.parse(source)
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for decorator
            is_callable = False
            is_http = False
            memory = None
            secrets = []

            for decorator in node.decorator_list:
                dec_str = ast.unparse(decorator)
                if decorator_pattern in dec_str:
                    is_callable = True
                    # Check if HTTP endpoint
                    if "on_request" in dec_str:
                        is_http = True
                    # Extract memory parameter
                    if "memory=" in dec_str:
                        match = re.search(r"memory=(\d+)", dec_str)
                        if match:
                            memory = int(match.group(1))
                    # Extract secrets
                    if "secrets=" in dec_str:
                        secrets = re.findall(r"([A-Z_]+_KEY)", dec_str)

            if is_callable:
                # Extract docstring
                docstring = ast.get_docstring(node) or ""

                # Parse request parameters from docstring
                params = parse_docstring_params(docstring)

                # Parse return type from docstring
                returns = parse_docstring_returns(docstring)

                # Parse SSE events if HTTP endpoint
                sse_events = parse_sse_events(docstring) if is_http else []

                functions.append({
                    "name": node.name,
                    "docstring": docstring,
                    "params": params,
                    "returns": returns,
                    "memory": memory,
                    "secrets": secrets,
                    "line": node.lineno,
                    "is_http": is_http,
                    "sse_events": sse_events,
                    "source_file": filepath.name,
                })

    return functions


def parse_main_py() -> list[dict]:
    """Parse all Python files to extract Cloud Function definitions."""
    functions = []

    # Parse main.py
    functions.extend(parse_python_file(MAIN_PY))

    # Parse conversation_helpers.py
    functions.extend(parse_python_file(CONVERSATION_HELPERS_PY))

    # Parse ask_the_stars.py (HTTP endpoints use on_request)
    functions.extend(parse_python_file(ASK_THE_STARS_PY, "https_fn.on_request"))

    return functions


def parse_docstring_params(docstring: str) -> list[dict]:
    """Parse request parameters from docstring Args section or Expected request data."""
    params = []

    # Try Args: format first (Google-style docstrings)
    args_match = re.search(r"Args:\s*\n((?:\s+\w+.*\n?)+)", docstring)
    if args_match:
        args_block = args_match.group(1)
        for line in args_block.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Match: param_name (type, optional): description
            param_match = re.match(r"(\w+)\s*\(([^)]+)\):\s*(.*)", line)
            if param_match:
                name = param_match.group(1)
                type_info = param_match.group(2)
                desc = param_match.group(3)
                is_optional = "optional" in type_info.lower()
                # Extract base type
                type_str = type_info.split(",")[0].strip()
                params.append({
                    "name": name,
                    "type": type_str,
                    "required": not is_optional,
                    "description": desc or "-"
                })
        if params:
            return params

    # Fall back to Expected request data format
    # Find the start of the JSON block
    start_match = re.search(r"Expected request data:\s*\{", docstring)
    if not start_match:
        return params

    # Find matching closing brace using balanced bracket matching
    start_idx = start_match.end() - 1  # Include the opening brace
    brace_count = 0
    end_idx = start_idx
    for i, char in enumerate(docstring[start_idx:], start_idx):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break

    json_block = docstring[start_idx:end_idx]

    # Parse only top-level fields (depth 1)
    # Track brace depth to skip nested objects
    depth = 0

    for line in json_block.split("\n"):
        stripped = line.strip()

        # Check depth at start of line (before processing this line's braces)
        # Only parse fields at depth 1 (inside the root object)
        if depth == 1 and stripped and not stripped.startswith("//") and stripped != "{":
            # Match "field_name": type_hint // comment
            param_match = re.match(r'"(\w+)":\s*([^,/\n]+)(?:,)?\s*(?://\s*(.*))?', stripped)
            if param_match:
                name = param_match.group(1)
                value_hint = param_match.group(2).strip()
                comment = param_match.group(3) or ""

                # Determine type from value hint
                if value_hint == '{':
                    type_str = "object"
                elif value_hint == '[':
                    type_str = "array"
                elif value_hint.startswith('"'):
                    type_str = "string"
                elif value_hint in ("true", "false"):
                    type_str = "boolean"
                elif "." in value_hint and value_hint.replace(".", "").replace("-", "").isdigit():
                    type_str = "float"
                elif value_hint.replace("-", "").isdigit():
                    type_str = "int"
                else:
                    type_str = "string"

                # Check if optional
                is_optional = "optional" in comment.lower() or "Optional" in comment

                # Build description - combine value with comment for choice fields
                description = comment.strip() if comment else "-"
                if description.startswith("or ") and value_hint.startswith('"'):
                    # Comment like "or 'public'" - prepend the example value
                    description = f"{value_hint} {description}"

                params.append({
                    "name": name,
                    "type": type_str,
                    "required": not is_optional,
                    "description": description,
                })

        # Count braces AFTER parsing to track depth for next line
        for char in line:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1

    return params


def parse_docstring_returns(docstring: str) -> str:
    """Parse return type from docstring Returns section."""
    # Look for Returns: section
    match = re.search(r"Returns:\s*\n\s*(.+?)(?:\n\s*\n|\Z)", docstring, re.DOTALL)
    if match:
        returns_text = match.group(1).strip()
        # Extract model name if present (preferred - links to model docs)
        model_match = re.search(r"(\w+(?:Data|Horoscope|Profile|Response|Result|ForIOS|SSEResponse))", returns_text)
        if model_match:
            return model_match.group(1)

        # If it's a JSON example, extract all keys to show response shape
        if returns_text.startswith("{"):
            # Extract all keys (including nested) so iOS knows full structure
            keys = re.findall(r'"(\w+)":', returns_text)
            if keys:
                # Deduplicate while preserving order
                seen = []
                for k in keys:
                    if k not in seen:
                        seen.append(k)
                # Show more keys (up to 10) for better iOS visibility
                return "{ " + ", ".join(f'"{k}": ...' for k in seen[:10]) + " }"

        return returns_text.split("\n")[0]
    return "object"


def parse_sse_events(docstring: str) -> list[dict]:
    """Parse SSE event schemas from docstring."""
    events = []

    # Look for SSE Response Events section
    sse_match = re.search(r"SSE Response Events:\s*\n(.+?)(?:\n\s*Returns:|\Z)", docstring, re.DOTALL)
    if not sse_match:
        return events

    sse_block = sse_match.group(1)

    # Extract event types with their JSON schemas
    # Pattern: data: {"type": "...", ...}
    event_matches = re.findall(r'data:\s*(\{[^}]+\})', sse_block)
    for event_json in event_matches:
        # Extract type field
        type_match = re.search(r'"type":\s*"(\w+)"', event_json)
        if type_match:
            event_type = type_match.group(1)
            # Extract other fields
            fields = re.findall(r'"(\w+)":\s*("[^"]+"|[\w.]+)', event_json)
            events.append({
                "type": event_type,
                "schema": event_json,
                "fields": {k: v for k, v in fields if k != "type"}
            })

    return events


# =============================================================================
# Markdown Generation
# =============================================================================

def generate_markdown(functions: list[dict], models: dict, enums: dict, astrometer_labels: dict) -> str:
    """Generate complete API documentation markdown."""
    lines = [
        "# Arca Backend API Reference",
        "",
        f"> Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "> ",
        "> DO NOT EDIT MANUALLY. Run `uv run python functions/generate_api_docs.py` to regenerate.",
        "",
        "## Table of Contents",
        "",
        "- [Authentication](#authentication)",
        "- [Callable Functions](#callable-functions)",
        "- [Model Definitions](#model-definitions)",
        "- [Enum Definitions](#enum-definitions)",
        "- [Astrometer State Labels](#astrometer-state-labels)",
        "",
        "---",
        "",
        "## Authentication",
        "",
        "All callable functions require Firebase Authentication. The backend verifies the auth token",
        "and uses `req.auth.uid` as the user ID - clients do NOT need to pass `user_id`.",
        "",
        "### How It Works",
        "",
        "1. iOS client signs in via Firebase Auth",
        "2. `httpsCallable()` automatically attaches the auth token",
        "3. Backend extracts user ID from the verified token",
        "",
        "### Dev Account Override",
        "",
        "For testing connection sharing flows, dev accounts can pass `user_id` in the request",
        "to impersonate other users. This is restricted to the following Firebase Auth UIDs:",
        "",
        "| Dev Account | Firebase UID |",
        "|-------------|--------------|",
        "| Dev A | `test_user_a` |",
        "| Dev B | `test_user_b` |",
        "| Dev C | `test_user_c` |",
        "| Dev D | `test_user_d` |",
        "| Dev E | `test_user_e` |",
        "",
        "**Usage (dev accounts only):**",
        "```swift",
        "// Normal user - no user_id needed",
        "let result = try await callable.call([\"date\": \"2025-01-15\"])",
        "",
        "// Dev account impersonating another user",
        "let result = try await callable.call([\"user_id\": \"target_user_uid\", \"date\": \"2025-01-15\"])",
        "```",
        "",
        "---",
        "",
        "## Callable Functions",
        "",
    ]

    # Group functions by category
    categories = {
        "Charts": ["natal_chart", "daily_transit", "user_transit", "get_synastry_chart", "get_natal_chart_for_connection"],
        "User Management": ["create_user_profile", "get_user_profile", "update_user_profile", "get_memory", "get_sun_sign_from_date", "register_device_token"],
        "Horoscope": ["get_daily_horoscope", "get_astrometers"],
        "Conversations": ["ask_the_stars", "get_conversation_history", "get_user_entities", "update_entity", "delete_entity"],
        "Connections": ["create_connection", "update_connection", "delete_connection", "list_connections"],
        "Sharing": ["get_share_link", "get_public_profile", "import_connection", "update_share_mode", "list_connection_requests", "respond_to_request"],
        "Compatibility": ["get_compatibility"],
    }

    categorized = set()
    for cat_name, func_names in categories.items():
        cat_functions = [f for f in functions if f["name"] in func_names]
        if not cat_functions:
            continue

        lines.append(f"### {cat_name}")
        lines.append("")

        for func in cat_functions:
            categorized.add(func["name"])
            lines.extend(generate_function_docs(func))

    # Any uncategorized functions
    uncategorized = [f for f in functions if f["name"] not in categorized]
    if uncategorized:
        lines.append("### Other")
        lines.append("")
        for func in uncategorized:
            lines.extend(generate_function_docs(func))

    # Model definitions
    lines.append("---")
    lines.append("")
    lines.append("## Model Definitions")
    lines.append("")

    # Group models by category
    model_categories = {
        "User & Profile": ["UserProfile", "MemoryCollection", "CategoryEngagement", "ConnectionMention", "RelationshipMention"],
        "Horoscope": ["DailyHoroscope", "ActionableAdvice", "RelationshipWeather", "ConnectionVibe"],
        "Astrometers": ["AstrometersForIOS", "MeterGroupForIOS", "MeterForIOS", "MeterAspect", "AstrologicalFoundation", "MeterReading"],
        "Charts": ["NatalChartData", "ChartAngles", "AnglePosition", "PlanetPosition", "HouseCusp", "AspectData", "ChartDistributions", "ElementDistribution", "ModalityDistribution", "QuadrantDistribution", "HemisphereDistribution"],
        "Connections": ["Connection", "StoredVibe", "ShareLink", "ConnectionRequest", "ShareLinkResponse", "PublicProfileResponse", "ImportConnectionResponse", "ConnectionListResponse"],
        "Compatibility": ["CompatibilityResult", "CompatibilityInterpretation", "ModeCompatibility", "CompatibilityCategory", "DrivingAspect", "SynastryAspect", "CompositeSummary", "KarmicSummary", "KarmicAspect"],
        "Entities": ["Entity", "UserEntities", "ExtractedEntity", "ExtractedEntities", "EntityMergeAction", "MergedEntities", "AttributeKV"],
        "Conversations": ["Conversation", "Message"],
        "Compressed Storage": ["CompressedHoroscope", "CompressedMeterGroup", "CompressedMeter", "CompressedAstrometers", "CompressedTransitSummary", "CompressedTransit", "UserHoroscopes"],
        "Sun Sign Profiles": ["SunSignProfile", "PlanetaryDignities", "Correspondences", "HealthTendencies", "CompatibilityEntry"],
    }

    documented_models = set()
    for cat_name, model_names in model_categories.items():
        cat_models = [(name, models[name]) for name in model_names if name in models]
        if not cat_models:
            continue

        lines.append(f"### {cat_name}")
        lines.append("")

        for model_name, model_fields in cat_models:
            documented_models.add(model_name)
            lines.extend(generate_model_docs(model_name, model_fields))

    # Any uncategorized models
    uncategorized_models = [(name, fields) for name, fields in models.items() if name not in documented_models]
    if uncategorized_models:
        lines.append("### Other Models")
        lines.append("")
        for model_name, model_fields in sorted(uncategorized_models):
            lines.extend(generate_model_docs(model_name, model_fields))

    # Enum definitions
    lines.append("---")
    lines.append("")
    lines.append("## Enum Definitions")
    lines.append("")

    for enum_name, enum_values in sorted(enums.items()):
        lines.extend(generate_enum_docs(enum_name, enum_values))

    # Astrometer state labels
    if astrometer_labels:
        lines.extend(generate_astrometer_labels_docs(astrometer_labels))

    return "\n".join(lines)


def generate_function_docs(func: dict) -> list[str]:
    """Generate documentation for a single function."""
    lines = [
        f"#### `{func['name']}`",
        "",
    ]

    # Add type indicator for HTTP endpoints
    if func.get("is_http"):
        lines.append("**Type:** HTTP Endpoint (SSE streaming)")
        lines.append("")

    # Add memory/secrets if present
    notes = []
    if func.get("memory"):
        notes.append(f"Memory: {func['memory']}MB")
    if func.get("secrets"):
        notes.append(f"Requires: {', '.join(func['secrets'])}")
    if notes:
        lines.append(f"*{' | '.join(notes)}*")
        lines.append("")

    # Description from first paragraph of docstring
    if func["docstring"]:
        desc = func["docstring"].split("\n\n")[0].replace("\n", " ").strip()
        lines.append(desc)
        lines.append("")

    # Authentication note for HTTP endpoints
    if func.get("is_http"):
        lines.append("**Authentication:**")
        lines.append("- Production: `Authorization: Bearer <firebase_id_token>`")
        # Check for dev mode in docstring
        if "dev_arca_2025" in func.get("docstring", ""):
            lines.append("- Dev mode: `Authorization: Bearer dev_arca_2025` (requires `user_id` in body)")
        lines.append("")

    # Request parameters
    if func["params"]:
        lines.append("**Request Body:**")
        lines.append("")
        lines.append("| Field | Type | Required | Description |")
        lines.append("|-------|------|----------|-------------|")
        for param in func["params"]:
            req = "Yes" if param["required"] else "No"
            lines.append(f"| `{param['name']}` | {param['type']} | {req} | {param['description']} |")
        lines.append("")

    # SSE events for HTTP endpoints
    if func.get("sse_events"):
        lines.append("**SSE Response Events:**")
        lines.append("")
        lines.append("Content-Type: `text/event-stream`")
        lines.append("")
        for event in func["sse_events"]:
            lines.append(f"**`type=\"{event['type']}\"`**")
            lines.append("```json")
            lines.append(event["schema"])
            lines.append("```")
            if event["fields"]:
                lines.append("")
                lines.append("| Field | Type | Description |")
                lines.append("|-------|------|-------------|")
                for field_name, field_val in event["fields"].items():
                    # Infer type from value
                    if field_val.startswith('"'):
                        field_type = "string"
                    else:
                        field_type = "string"
                    lines.append(f"| `{field_name}` | {field_type} | - |")
            lines.append("")
    else:
        # Regular response for non-SSE functions
        lines.append(f"**Response:** `{func['returns']}`")
        lines.append("")

    lines.append("---")
    lines.append("")

    return lines


def generate_model_docs(model_name: str, fields: dict) -> list[str]:
    """Generate documentation for a single model."""
    lines = [
        f"#### `{model_name}`",
        "",
        "| Field | Type | Required | Default | Constraints | Description |",
        "|-------|------|----------|---------|-------------|-------------|",
    ]

    for field_name, field_info in fields.items():
        req = "Yes" if field_info["required"] else "No"
        default = field_info["default"] if field_info["default"] != "-" else "-"
        if len(default) > 20:
            default = default[:17] + "..."
        desc = field_info["description"]
        if len(desc) > 60:
            desc = desc[:57] + "..."

        lines.append(
            f"| `{field_name}` | {field_info['type']} | {req} | {default} | {field_info['constraints']} | {desc} |"
        )

    lines.append("")
    return lines


def generate_enum_docs(enum_name: str, values: list[dict]) -> list[str]:
    """Generate documentation for an enum."""
    lines = [
        f"#### `{enum_name}`",
        "",
        "| Name | Value |",
        "|------|-------|",
    ]

    for v in values:
        lines.append(f"| `{v['name']}` | `\"{v['value']}\"` |")

    lines.append("")
    return lines


# =============================================================================
# Astrometer Labels Extraction
# =============================================================================

def extract_astrometer_labels() -> dict:
    """Extract bucket labels from group JSON files."""
    import json
    from pathlib import Path

    labels_dir = Path(__file__).parent / "astrometers" / "labels" / "groups"
    groups = ["overall", "mind", "heart", "body", "instincts", "growth"]

    result = {}
    for group_name in groups:
        json_file = labels_dir / f"{group_name}.json"
        if json_file.exists():
            with open(json_file, "r") as f:
                data = json.load(f)
            bucket_labels = data.get("bucket_labels", {})
            if isinstance(bucket_labels, dict):
                result[group_name] = {
                    "display_name": data.get("metadata", {}).get("display_name", group_name.title()),
                    "buckets": {
                        "0-25": bucket_labels.get("0-25", {}).get("label", ""),
                        "25-50": bucket_labels.get("25-50", {}).get("label", ""),
                        "50-75": bucket_labels.get("50-75", {}).get("label", ""),
                        "75-100": bucket_labels.get("75-100", {}).get("label", ""),
                    }
                }
    return result


def generate_astrometer_labels_docs(labels: dict) -> list[str]:
    """Generate markdown documentation for astrometer bucket labels."""
    lines = [
        "---",
        "",
        "## Astrometer State Labels",
        "",
        "Each meter group has 4 state labels based on the unified score quartile.",
        "",
        "**Quartile Thresholds:**",
        "- `score < 25` -> bucket 0 (challenging)",
        "- `score >= 25 && < 50` -> bucket 1 (turbulent)",
        "- `score >= 50 && < 75` -> bucket 2 (peaceful)",
        "- `score >= 75` -> bucket 3 (flowing)",
        "",
        "### Labels by Group",
        "",
        "| Group | 0-25 | 25-50 | 50-75 | 75-100 |",
        "|-------|------|-------|-------|--------|",
    ]

    for group_name, group_data in labels.items():
        buckets = group_data["buckets"]
        lines.append(
            f"| **{group_data['display_name']}** | {buckets['0-25']} | {buckets['25-50']} | {buckets['50-75']} | {buckets['75-100']} |"
        )

    lines.append("")
    lines.append("### iOS Implementation")
    lines.append("")
    lines.append("```swift")
    lines.append("// Map unified_score to bucket index")
    lines.append("func bucketIndex(score: Double) -> Int {")
    lines.append("    if score < 25 { return 0 }")
    lines.append("    else if score < 50 { return 1 }")
    lines.append("    else if score < 75 { return 2 }")
    lines.append("    else { return 3 }")
    lines.append("}")
    lines.append("```")
    lines.append("")

    return lines


# =============================================================================
# Main
# =============================================================================

def main():
    print("Generating API documentation...")

    # Import all models
    print("  Importing models...")

    # models.py
    from models import (
        UserProfile, MemoryCollection, CategoryEngagement, RelationshipMention, ConnectionMention,
        Entity, UserEntities, Message, Conversation,
        ExtractedEntity, ExtractedEntities, EntityMergeAction, MergedEntities, AttributeKV,
        ActionableAdvice, RelationshipWeather, ConnectionVibe,
        MeterGroupScores, MeterGroupState, TrendMetric, MeterGroupTrend, MeterGroupData,
        DailyHoroscope,
        CompressedMeter, CompressedMeterGroup, CompressedTransit, CompressedTransitSummary,
        CompressedAstrometers, CompressedHoroscope, UserHoroscopes,
        MeterAspect, AstrologicalFoundation, MeterForIOS, MeterGroupForIOS, AstrometersForIOS,
        EntityStatus, EntityCategory, MessageRole, ActionType, QualityType, DirectionType, ChangeRateType,
    )

    # relationships.py
    from relationships import RelationshipCategory, RelationshipLabel

    # astro.py
    from astro import (
        NatalChartData, ChartAngles, AnglePosition, PlanetPosition, HouseCusp, AspectData,
        ChartDistributions, ElementDistribution, ModalityDistribution, QuadrantDistribution, HemisphereDistribution,
        SunSignProfile, PlanetaryDignities, Correspondences, HealthTendencies, CompatibilityEntry,
        ZodiacSign, Planet, CelestialBody, Element, Modality, AspectType, ChartType, House,
    )

    # connections.py
    from connections import (
        Connection, StoredVibe, ShareLink, ConnectionRequest,
        ShareLinkResponse, PublicProfileResponse, ImportConnectionResponse, ConnectionListResponse,
    )

    # compatibility.py
    from compatibility import (
        SynastryAspect, DrivingAspect, CompatibilityCategory, Composite, ModeCompatibility, CompatibilityResult,
        Karmic,
    )

    # astrometers
    from astrometers.meters import MeterReading
    from astrometers.hierarchy import Meter, MeterGroupV2

    # Collect all models
    pydantic_models = [
        # User & Profile
        UserProfile, MemoryCollection, CategoryEngagement, RelationshipMention, ConnectionMention,
        # Entities
        Entity, UserEntities, Message, Conversation,
        ExtractedEntity, ExtractedEntities, EntityMergeAction, MergedEntities, AttributeKV,
        # Horoscope
        ActionableAdvice, RelationshipWeather, ConnectionVibe,
        MeterGroupScores, MeterGroupState, TrendMetric, MeterGroupTrend, MeterGroupData,
        DailyHoroscope,
        # Compressed
        CompressedMeter, CompressedMeterGroup, CompressedTransit, CompressedTransitSummary,
        CompressedAstrometers, CompressedHoroscope, UserHoroscopes,
        # Astrometers iOS
        MeterAspect, AstrologicalFoundation, MeterForIOS, MeterGroupForIOS, AstrometersForIOS,
        MeterReading,
        # Charts
        NatalChartData, ChartAngles, AnglePosition, PlanetPosition, HouseCusp, AspectData,
        ChartDistributions, ElementDistribution, ModalityDistribution, QuadrantDistribution, HemisphereDistribution,
        SunSignProfile, PlanetaryDignities, Correspondences, HealthTendencies, CompatibilityEntry,
        # Connections
        Connection, StoredVibe, ShareLink, ConnectionRequest,
        ShareLinkResponse, PublicProfileResponse, ImportConnectionResponse, ConnectionListResponse,
        # Compatibility
        SynastryAspect, DrivingAspect, CompatibilityCategory, Composite, ModeCompatibility, CompatibilityResult,
        Karmic,
    ]

    enum_classes = [
        EntityStatus, EntityCategory, MessageRole, ActionType, QualityType, DirectionType, ChangeRateType,
        RelationshipCategory, RelationshipLabel,
        ZodiacSign, Planet, CelestialBody, Element, Modality, AspectType, ChartType, House,
        # Astrometers
        Meter, MeterGroupV2,
    ]

    # Extract model fields
    print("  Extracting model fields...")
    models = {}
    for model in pydantic_models:
        try:
            models[model.__name__] = extract_pydantic_model(model)
        except Exception as e:
            print(f"    Warning: Could not extract {model.__name__}: {e}")

    # Extract enums
    print("  Extracting enums...")
    enums = {}
    for enum_class in enum_classes:
        try:
            enums[enum_class.__name__] = extract_enum(enum_class)
        except Exception as e:
            print(f"    Warning: Could not extract {enum_class.__name__}: {e}")

    # Parse main.py for functions
    print("  Parsing main.py...")
    functions = parse_main_py()
    print(f"    Found {len(functions)} callable functions")

    # Extract astrometer labels
    print("  Extracting astrometer labels...")
    astrometer_labels = extract_astrometer_labels()
    print(f"    Found {len(astrometer_labels)} meter groups")

    # Generate markdown
    print("  Generating markdown...")
    markdown = generate_markdown(functions, models, enums, astrometer_labels)

    # Write output
    print(f"  Writing to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(markdown)

    print(f"\nDone! Generated {len(functions)} functions, {len(models)} models, {len(enums)} enums")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
