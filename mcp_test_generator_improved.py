#!/usr/bin/env python3
"""
MCP Plugin – Enhanced Test Generator for Trading Framework
==========================================================
Author  : ChatGPT‑Grace (merged with Cursor & L2 auto‑refresh)
Date    : 2025‑06‑05

Overview
--------
• **L2 智能刷新覆盖率**：若 .coverage 旧于源码最后修改，自动执行
  `pytest --cov` 生成最新 .coverage & .coverage.json，再分析
• Async 支持：检测 `ast.AsyncFunctionDef` 自动加 `@pytest.mark.asyncio`
• CLI 参数：`path` `focus` `threshold` `llm` `pr`
• 预留 `_generate_test_via_llm()` 钩子，可接入 Cursor / OpenAI
• 可选自动创建 PR（需 `GITHUB_TOKEN`）

Usage (in Cursor chat)
----------------------
/generate_tests path=src focus=low threshold=65 llm=true pr=false
"""

from __future__ import annotations

import ast
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Sequence


# ----------------- Configuration ----------------- #
PLUGIN_SETTINGS = {
    "default_path": "src",
    "coverage_threshold": 65,
    "focus_modes": {"low", "all"},
    "llm_enabled": True,  # toggle LLM generation
}

__mcp_plugin__ = {
    "name": "trading-test-generator",
    "version": "0.4.0",
    "description": "Generate pytest tests (sync & async) to improve coverage.",
    "entrypoint": "generate_tests_command",
}

logging.basicConfig(
    format="%(levelname)s | %(message)s",
    level=logging.INFO,
)

# ----------------- CLI entrypoint ----------------- #


def generate_tests_command(
    path: str = PLUGIN_SETTINGS["default_path"],
    focus: str = "low",
    threshold: int = PLUGIN_SETTINGS["coverage_threshold"],
    llm: bool = PLUGIN_SETTINGS["llm_enabled"],
    pr: bool = False,
) -> None:
    """Generate tests for uncovered code."""
    logging.info("🚀 启动测试生成器 (path=%s, focus=%s, threshold=%s)", path, focus, threshold)

    # --- L2 智能刷新覆盖率 --- #
    if not _ensure_fresh_coverage(path):
        logging.error("❌ 无法生成最新覆盖率数据，终止执行。")
        return

    coverage_data = _get_coverage_data()
    if not coverage_data:
        logging.error("❌ 仍未找到 coverage 数据，请检查 pytest 执行情况。")
        return

    targets = _find_targets(path, coverage_data, focus, threshold)
    logging.info("📊 找到 %d 个目标文件", len(targets))

    total_tests = 0
    for file_path, info in targets.items():
        functions = _find_uncovered_functions(file_path, info["missing_lines"])
        for func in functions:
            if _write_test(path, file_path, func, llm_enabled=llm):
                total_tests += 1

    logging.info("✅ 生成 %d 个测试", total_tests)

    if pr:
        _create_github_pr()


# ----------------- Coverage helpers ----------------- #


def _ensure_fresh_coverage(src_path: str) -> bool:
    """Return True if we have up‑to‑date coverage; else try to refresh."""
    cov_file = Path(".coverage")
    # 最新源码 mtime
    try:
        latest_src_mtime = max(p.stat().st_mtime for p in Path(src_path).rglob("*.py"))
    except ValueError:
        logging.error("No python files found under %s", src_path)
        return False

    need_refresh = (not cov_file.exists()) or (cov_file.stat().st_mtime < latest_src_mtime)

    if need_refresh:
        logging.info("🌀 .coverage 过期或不存在，正在运行 pytest 生成最新覆盖率…")
        try:
            subprocess.run(
                [
                    "pytest",
                    "-q",
                    f"--cov={src_path}",
                    "--cov-report=json",
                ],
                check=True,
            )
            logging.info("✅ 覆盖率刷新完成")
            return True
        except subprocess.CalledProcessError as exc:
            logging.error("pytest 执行失败: %s", exc)
            return False
    else:
        logging.info("📄 发现新鲜的 .coverage 文件，直接复用")
        return True


def _get_coverage_data() -> Optional[Dict]:
    """Load .coverage.json produced by coverage json report."""
    json_file = Path(".coverage.json")
    if not json_file.exists():
        logging.error(".coverage.json 不存在，无法解析数据")
        return None
    try:
        with json_file.open() as f:
            return json.load(f)
    except Exception as exc:
        logging.error("读取 .coverage.json 失败: %s", exc)
        return None


# ----------------- Target selection ----------------- #


def _find_targets(
    path: str,
    data: Dict,
    focus: str,
    threshold: int,
) -> Dict[Path, Dict[str, Sequence[int]]]:
    """Return mapping of files needing tests -> {'missing_lines': [...]}"""
    src_root = Path(path)
    results: Dict[Path, Dict[str, Sequence[int]]] = {}

    for f in src_root.rglob("*.py"):
        if f.name.startswith("test_"):
            continue
        file_cov = data.get("files", {}).get(str(f))
        if not file_cov:
            # 文件尚未被任何测试覆盖
            results[f] = {"missing_lines": []}
            continue
        executed = len(file_cov.get("executed_lines", []))
        missing = file_cov.get("missing_lines", [])
        total = executed + len(missing)
        coverage_percent = (executed / total) * 100 if total else 0.0
        if focus == "all" or coverage_percent < threshold:
            results[f] = {"missing_lines": missing}
    return results


# ----------------- AST helpers ----------------- #


def _find_uncovered_functions(
    file_path: Path,
    missing_lines: Sequence[int],
) -> List[ast.AST]:
    """Return list of uncovered FunctionDef / AsyncFunctionDef nodes."""
    try:
        tree = ast.parse(file_path.read_text())
    except (SyntaxError, UnicodeDecodeError) as exc:
        logging.warning("skip %s due to parse error: %s", file_path, exc)
        return []

    missing_set = set(missing_lines)
    funcs: List[ast.AST] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith(
            "_"
        ):
            # If any line of this function is missing, mark as uncovered
            if any(
                (hasattr(child, "lineno") and child.lineno in missing_set)
                for child in ast.walk(node)
            ):
                funcs.append(node)
    return funcs


# ----------------- Test writer ----------------- #


def _write_test(
    src_root: str,
    file_path: Path,
    func: ast.AST,
    llm_enabled: bool = True,
) -> bool:
    """Generate and write a single test for given function."""
    is_async = isinstance(func, ast.AsyncFunctionDef)
    module_path = str(file_path.relative_to(src_root)).replace(os.sep, ".").rstrip(".py")
    test_file = Path("tests") / f"test_{file_path.stem}_generated.py"
    test_file.parent.mkdir(exist_ok=True)

    if llm_enabled:
        content = _generate_test_via_llm(module_path, func.name, is_async)
    else:
        marker = "@pytest.mark.asyncio\n" if is_async else ""
        def_kw = "async def" if is_async else "def"
        content = (
            f"from {module_path} import {func.name}\n"
            "import pytest\n\n"
            f"{marker}{def_kw} test_{func.name}_basic():\n"
            '    """自动生成的占位测试."""\n'
            "    # TODO: 补充真实断言\n"
            f"    assert {func.name}  # type: ignore\n\n"
        )

    header = f"# Generated tests for {module_path}\n"
    write_mode = "a" if test_file.exists() else "w"
    with test_file.open(write_mode) as fp:
        if write_mode == "w":
            fp.write(header)
        fp.write(content)
    return True


# ----------------- LLM stub ----------------- #


def _generate_test_via_llm(
    module_path: str,
    func_name: str,
    is_async: bool,
) -> str:
    """Call LLM to draft a meaningful test. Placeholder implementation."""
    prompt = (
        "You are given the function {func} from module {mod}. "
        "Write a pytest test case that exercises the normal path. "
        "Use pytest.mark.asyncio if async.".format(func=func_name, mod=module_path)
    )
    logging.debug("LLM prompt:\n%s", prompt)
    marker = "@pytest.mark.asyncio\n" if is_async else ""
    def_kw = "async def" if is_async else "def"
    return (
        f"from {module_path} import {func_name}\n"
        "import pytest\n\n"
        f"{marker}{def_kw} test_{func_name}_basic():\n"
        "    # TODO: LLM generated body placeholder\n"
        "    assert True\n\n"
    )


# ----------------- GitHub PR helper ----------------- #


def _create_github_pr() -> None:
    """Create a PR with the changes. Placeholder implementation."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logging.info("No GITHUB_TOKEN provided; skipping PR creation.")
        return
    logging.info("🍀 Dummy PR creation triggered (not implemented).")


if __name__ == "__main__":
    generate_tests_command()
