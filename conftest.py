"""Root-level pytest configuration helpers.

Automatically tag tests under legacy backup directories as ``archive`` and
performance benchmark scripts as ``slow`` so they are excluded from the default
fast test run but *can* be executed explicitly when required.
"""

from __future__ import annotations

import os

import pytest

# ---------------------------------------------------------------------------
# Path patterns to classify tests
# ---------------------------------------------------------------------------

_ARCHIVE_DIR_KEYWORDS: tuple[str, ...] = (
    "archive_backup_",
    "tests_backup_before_cleanup",
)
_PERF_DIR_KEYWORDS: tuple[str, ...] = (
    os.path.join("scripts", "performance"),
    os.path.join("tests", "performance"),  # future-proof
)


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------


def _path_contains_keyword(path: str, keywords: tuple[str, ...]) -> bool:
    """Return True if *any* keyword fragment appears in *path*."""
    return any(k in path for k in keywords)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:  # noqa: D401
    """Attach *archive* / *slow* markers based on file location."""

    archive_marker = pytest.mark.archive
    slow_marker = pytest.mark.slow

    for item in items:
        path_str = str(item.fspath)

        # Tag archive / legacy tests
        if _path_contains_keyword(path_str, _ARCHIVE_DIR_KEYWORDS):
            item.add_marker(archive_marker)

        # Tag performance / slow tests
        if _path_contains_keyword(path_str, _PERF_DIR_KEYWORDS):
            item.add_marker(slow_marker)
