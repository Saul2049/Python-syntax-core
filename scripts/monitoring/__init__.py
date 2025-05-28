#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scripts Monitoring Module (脚本监控模块)

Legacy monitoring module for backward compatibility
"""

try:
    from .monitoring import PrometheusExporter
except ImportError:
    PrometheusExporter = None

__all__ = ["PrometheusExporter"]
