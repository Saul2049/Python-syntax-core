#!/bin/bash
# 自动生成的测试清理脚本
set -e

# 创建归档目录
mkdir -p tests/archive/deprecated
mkdir -p tests/archive/old_versions

# 删除明确无用的测试
echo '删除无用测试: test_brokers_binance_client.py::test_rate_limit_retry_success_first_attempt'
echo '删除无用测试: test_core_gc_optimizer.py::test_temporary_gc_settings_context_manager'
echo '删除无用测试: test_core_gc_optimizer.py::test_temporary_gc_settings_with_exception'
echo '删除无用测试: test_core_network_retry_manager.py::test_execute_success_first_attempt'
echo '删除无用测试: test_core_network_retry_manager.py::test_log_retry_attempt'
echo '删除无用测试: test_core_network_decorators.py::test_save_attempt_state'
echo '删除无用测试: test_core_network_decorators.py::test_should_continue_retry_false_max_attempts'
echo '删除无用测试: test_core_network_decorators.py::test_log_retry_attempt'
echo '删除无用测试: test_core_network_decorators.py::test_execute_with_retry_success_first_attempt'

echo '清理完成！'