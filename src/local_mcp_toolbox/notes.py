"""Safe, read-only keyword search over a configured local notes directory."""

from __future__ import annotations

import os
import re
from pathlib import Path

_TOKEN_PATTERN = re.compile(r"[\w'-]+", flags=re.UNICODE)
_ALLOWED_EXTENSIONS = {".md", ".txt"}
_MAX_FILE_BYTES = 1_000_000
_MAX_RESULTS = 20
_MAX_SNIPPET_CHARS = 500


def get_notes_directory() -> Path:
    """Return the configured notes directory (default: ./data/notes)."""

    configured = os.environ.get("MCP_TOOLBOX_NOTES_DIR", "data/notes")
    return Path(configured).expanduser().resolve()


def search_notes(query: str, limit: int = 5) -> dict[str, object]:
    """Search configured Markdown/text notes and return ranked snippets.

    Only .md and .txt files under MCP_TOOLBOX_NOTES_DIR are considered.
    The caller supplies search terms, not a filesystem path. Results expose
    relative source names rather than the machine's absolute notes path.
    """

    terms = [term.casefold() for term in _TOKEN_PATTERN.findall(query)]
    if not terms:
        return {"ok": False, "error": "Query must contain at least one searchable word."}
    if not 1 <= limit <= _MAX_RESULTS:
        return {"ok": False, "error": f"limit must be between 1 and {_MAX_RESULTS}."}

    root = get_notes_directory()
    if not root.exists() or not root.is_dir():
        return {
            "ok": True,
            "results_count": 0,
            "results": [],
            "message": "Notes directory not found. Create it or set MCP_TOOLBOX_NOTES_DIR.",
        }

    results: list[dict[str, object]] = []
    for file_path in sorted(root.rglob("*")):
        if file_path.suffix.lower() not in _ALLOWED_EXTENSIONS or not file_path.is_file():
            continue
        try:
            resolved = file_path.resolve(strict=True)
            relative_source = resolved.relative_to(root)
            if resolved.stat().st_size > _MAX_FILE_BYTES:
                continue
            content = resolved.read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            continue

        normalized = content.casefold()
        unique_terms = set(terms)
        score = sum(normalized.count(term) for term in unique_terms)
        if score == 0:
            continue

        first_match = min(
            normalized.find(term) for term in unique_terms if term in normalized
        )
        start = max(0, first_match - 100)
        snippet = content[start : start + _MAX_SNIPPET_CHARS].strip()
        if start > 0:
            snippet = "…" + snippet
        if start + _MAX_SNIPPET_CHARS < len(content):
            snippet += "…"

        results.append(
            {
                "source": relative_source.as_posix(),
                "score": score,
                "snippet": snippet,
            }
        )

    results.sort(key=lambda item: (-int(item["score"]), str(item["source"])))
    selected = results[:limit]
    return {
        "ok": True,
        "results_count": len(selected),
        "results": selected,
    }


__all__ = ["get_notes_directory", "search_notes"]
