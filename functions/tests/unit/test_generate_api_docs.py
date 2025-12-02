"""
Unit tests for generate_api_docs.py

Ensures the API documentation generator can run without errors.
"""

import subprocess
import sys
from pathlib import Path


def test_generate_api_docs_runs_without_error():
    """
    Test that generate_api_docs.py can be executed without import errors.

    This catches issues like:
    - Missing imports (e.g., removed enums like RelationshipType)
    - Circular imports
    - Invalid model references
    """
    script_path = Path(__file__).parent.parent.parent / "generate_api_docs.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent,
        timeout=60
    )

    assert result.returncode == 0, f"generate_api_docs.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "Done!" in result.stdout, f"Expected 'Done!' in output, got: {result.stdout}"


def test_generate_api_docs_produces_output():
    """Test that generate_api_docs.py produces the expected output file."""
    script_path = Path(__file__).parent.parent.parent / "generate_api_docs.py"
    output_path = Path(__file__).parent.parent.parent.parent / "docs" / "PUBLIC_API_GENERATED.md"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent,
        timeout=60
    )

    assert result.returncode == 0
    assert output_path.exists(), f"Expected output file at {output_path}"

    content = output_path.read_text()
    assert len(content) > 1000, "Output file seems too small"
    assert "# Arca Backend API Reference" in content, "Missing expected header"


def test_generate_api_docs_includes_relationship_enums():
    """Test that the generated docs include the new relationship enums."""
    script_path = Path(__file__).parent.parent.parent / "generate_api_docs.py"
    output_path = Path(__file__).parent.parent.parent.parent / "docs" / "PUBLIC_API_GENERATED.md"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent,
        timeout=60
    )

    assert result.returncode == 0

    content = output_path.read_text()

    # Check new enums are present
    assert "RelationshipCategory" in content, "Missing RelationshipCategory enum"
    assert "RelationshipLabel" in content, "Missing RelationshipLabel enum"

    # Check old enum is NOT present (was replaced)
    assert "RelationshipType" not in content, "Old RelationshipType enum should not be present"

    # Check new fields are documented
    assert "relationship_category" in content, "Missing relationship_category field"
    assert "relationship_label" in content, "Missing relationship_label field"
