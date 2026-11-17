from __future__ import annotations

import os
from pathlib import Path

import pytest

from local_mcp_toolbox.calculator import evaluate_expression
from local_mcp_toolbox.notes import get_notes_directory, search_notes
from local_mcp_toolbox.system_info import get_system_info


def test_calculator_evaluates_arithmetic_with_precedence() -> None:
    result = evaluate_expression("2 + 3 * (4 - 1)")

    assert result == {
        "ok": True,
        "expression": "2 + 3 * (4 - 1)",
        "result": 11,
    }


def test_calculator_handles_division_by_zero() -> None:
    result = evaluate_expression("10 / 0")

    assert result["ok"] is False
    assert result["error"] == "Division by zero is not allowed."


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo unsafe')",
        "open('secret.txt').read()",
        "math.sqrt(16)",
        "value + 1",
    ],
)
def test_calculator_rejects_python_code_names_and_function_calls(
    expression: str,
) -> None:
    result = evaluate_expression(expression)

    assert result["ok"] is False
    assert "error" in result


def test_calculator_limits_exponent_magnitude() -> None:
    result = evaluate_expression("2 ** 100")

    assert result["ok"] is False
    assert "Exponent magnitude" in str(result["error"])


def test_calculator_rejects_empty_and_oversized_expressions() -> None:
    empty_result = evaluate_expression("   ")
    long_result = evaluate_expression("1" * 129)

    assert empty_result["ok"] is False
    assert "cannot be empty" in str(empty_result["error"])
    assert long_result["ok"] is False
    assert "too long" in str(long_result["error"])


def test_notes_search_finds_matching_markdown_and_text_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "agentic.md").write_text(
        "Agentic AI tools help an agent complete tasks. Tool calling connects agents to tools.",
        encoding="utf-8",
    )
    (tmp_path / "python.txt").write_text(
        "Python is a general-purpose programming language.",
        encoding="utf-8",
    )
    (tmp_path / "ignored.csv").write_text(
        "agentic,tools,should,not,be,indexed",
        encoding="utf-8",
    )
    monkeypatch.setenv("MCP_TOOLBOX_NOTES_DIR", str(tmp_path))

    result = search_notes("agentic tools", limit=5)

    assert result["ok"] is True
    assert result["results_count"] == 1
    assert result["results"][0]["source"] == "agentic.md"
    assert result["results"][0]["score"] > 0
    assert "Agentic AI tools" in result["results"][0]["snippet"]


def test_notes_search_returns_relative_paths_and_not_absolute_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "notes.md").write_text("MCP server tool discovery", encoding="utf-8")
    monkeypatch.setenv("MCP_TOOLBOX_NOTES_DIR", str(tmp_path))

    result = search_notes("MCP server")

    assert result["ok"] is True
    assert result["results"][0]["source"] == "nested/notes.md"
    assert str(tmp_path) not in str(result)


def test_notes_search_handles_missing_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "not-created"
    monkeypatch.setenv("MCP_TOOLBOX_NOTES_DIR", str(missing))

    result = search_notes("anything")

    assert result["ok"] is True
    assert result["results_count"] == 0
    assert result["results"] == []
    assert "not found" in str(result["message"]).lower()


@pytest.mark.parametrize(
    ("query", "limit"),
    [
        ("   ", 5),
        ("valid query", 0),
        ("valid query", 21),
    ],
)
def test_notes_search_validates_query_and_limit(
    query: str,
    limit: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_TOOLBOX_NOTES_DIR", str(tmp_path))

    result = search_notes(query, limit=limit)

    assert result["ok"] is False
    assert "error" in result


def test_get_notes_directory_uses_configured_location(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_TOOLBOX_NOTES_DIR", str(tmp_path))

    assert get_notes_directory() == tmp_path.resolve()


def test_system_info_contains_expected_non_sensitive_fields() -> None:
    info = get_system_info()

    assert isinstance(info["os"], str)
    assert isinstance(info["os_release"], str)
    assert isinstance(info["architecture"], str)
    assert isinstance(info["python_version"], str)
    assert info["logical_cpu_count"] is None or isinstance(
        info["logical_cpu_count"], int
    )

    sensitive_or_unnecessary_keys = {
        "username",
        "hostname",
        "host",
        "environment",
        "environment_variables",
        "ip_address",
        "processes",
    }
    assert sensitive_or_unnecessary_keys.isdisjoint(info.keys())
