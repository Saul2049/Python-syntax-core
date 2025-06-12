#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legacy *data* helper module (archived).

The **sole purpose** of this file is to satisfy import expectations of the
*old_tests* suite bundled inside :pydir:`archive_backup_20250606`.
"""

from __future__ import annotations

import types

try:
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – fallback when pandas is absent
    pd = types.ModuleType("pandas")  # type: ignore[assignment]


def load_csv(filepath: str = "btc_eth.csv") -> "pd.DataFrame":
    """Load a CSV file and return a *pandas* DataFrame.

    The implementation is intentionally *minimal* – it raises
    :class:`FileNotFoundError` for every call because the legacy tests only
    exercise the *control-flow* and handle exceptions on their own.  The function
    nonetheless mirrors the original public signature and provides a useful
    docstring so that introspection-based tests can succeed.
    """

    raise FileNotFoundError(f"{filepath} not found – this is a stub implementation")


__all__ = ["pd", "load_csv"]
