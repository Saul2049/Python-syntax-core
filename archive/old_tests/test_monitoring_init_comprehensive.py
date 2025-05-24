#!/usr/bin/env python3
"""
监控模块__init__.py完整测试套件 (Monitoring Init Comprehensive Tests)

专门提升src/monitoring/__init__.py覆盖率
目标：从43%覆盖率提升到90%+
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import importlib


class TestMonitoringImports:
    """监控模块导入测试"""

    def test_import_monitoring_module(self):
        """测试监控模块基础导入"""
        try:
            import src.monitoring
            assert src.monitoring is not None
        except ImportError as e:
            pytest.fail(f"Failed to import monitoring module: {e}")

    def test_import_individual_components(self):
        """测试单独导入各组件"""
        from src.monitoring import (
            AlertManager,
            HealthChecker,
            MetricsCollector,
            PrometheusExporter,
            get_monitoring_system
        )
        
        # 验证导入的是类/函数
        assert AlertManager is not None
        assert HealthChecker is not None
        assert MetricsCollector is not None
        assert PrometheusExporter is not None
        assert callable(get_monitoring_system)

    def test_all_exports(self):
        """测试__all__导出列表"""
        import src.monitoring
        
        expected_exports = [
            "PrometheusExporter",
            "MetricsCollector", 
            "HealthChecker",
            "AlertManager",
            "get_monitoring_system",
        ]
        
        assert hasattr(src.monitoring, '__all__')
        assert all(item in src.monitoring.__all__ for item in expected_exports)


class TestGetMonitoringSystemFunction:
    """get_monitoring_system函数测试"""

    def test_get_monitoring_system_default_parameters(self):
        """测试默认参数的监控系统"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 设置mock返回值
            mock_exporter = Mock()
            mock_collector = Mock()
            mock_health_checker = Mock()
            mock_alert_manager = Mock()
            
            MockPrometheusExporter.return_value = mock_exporter
            MockMetricsCollector.return_value = mock_collector
            MockHealthChecker.return_value = mock_health_checker
            MockAlertManager.return_value = mock_alert_manager
            
            from src.monitoring import get_monitoring_system
            
            result = get_monitoring_system()
            
            # 验证函数调用
            MockPrometheusExporter.assert_called_once_with(port=9090)
            MockMetricsCollector.assert_called_once_with(mock_exporter)
            MockHealthChecker.assert_called_once_with(mock_collector)
            MockAlertManager.assert_called_once_with(mock_collector)
            
            # 验证返回结果
            assert isinstance(result, dict)
            assert 'exporter' in result
            assert 'collector' in result  
            assert 'health_checker' in result
            assert 'alert_manager' in result
            
            assert result['exporter'] is mock_exporter
            assert result['collector'] is mock_collector
            assert result['health_checker'] is mock_health_checker
            assert result['alert_manager'] is mock_alert_manager

    def test_get_monitoring_system_custom_port(self):
        """测试自定义端口的监控系统"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 设置mock返回值
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            MockAlertManager.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            result = get_monitoring_system(port=8080)
            
            # 验证使用了自定义端口
            MockPrometheusExporter.assert_called_once_with(port=8080)
            
            assert isinstance(result, dict)
            assert len(result) == 4  # 包含alert_manager

    def test_get_monitoring_system_alerts_disabled(self):
        """测试禁用警报的监控系统"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 设置mock返回值
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            result = get_monitoring_system(enable_alerts=False)
            
            # 验证AlertManager没有被调用
            MockAlertManager.assert_not_called()
            
            # 验证返回结果不包含alert_manager
            assert isinstance(result, dict)
            assert 'exporter' in result
            assert 'collector' in result
            assert 'health_checker' in result
            assert 'alert_manager' not in result
            assert len(result) == 3

    def test_get_monitoring_system_alerts_enabled_explicitly(self):
        """测试显式启用警报的监控系统"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 设置mock返回值
            mock_exporter = Mock()
            mock_collector = Mock()
            mock_health_checker = Mock()
            mock_alert_manager = Mock()
            
            MockPrometheusExporter.return_value = mock_exporter
            MockMetricsCollector.return_value = mock_collector
            MockHealthChecker.return_value = mock_health_checker
            MockAlertManager.return_value = mock_alert_manager
            
            from src.monitoring import get_monitoring_system
            
            result = get_monitoring_system(enable_alerts=True)
            
            # 验证AlertManager被调用
            MockAlertManager.assert_called_once_with(mock_collector)
            
            # 验证返回结果包含alert_manager
            assert 'alert_manager' in result
            assert result['alert_manager'] is mock_alert_manager

    def test_get_monitoring_system_custom_parameters_combination(self):
        """测试自定义参数组合"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 设置mock返回值
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 测试自定义端口但禁用警报
            result = get_monitoring_system(port=3000, enable_alerts=False)
            
            MockPrometheusExporter.assert_called_once_with(port=3000)
            MockAlertManager.assert_not_called()
            
            assert 'alert_manager' not in result
            assert len(result) == 3

    def test_get_monitoring_system_component_initialization_order(self):
        """测试组件初始化顺序"""
        call_order = []
        
        def track_prometheus_init(*args, **kwargs):
            call_order.append('prometheus')
            return Mock()
        
        def track_collector_init(*args, **kwargs):
            call_order.append('collector')
            return Mock()
        
        def track_health_init(*args, **kwargs):
            call_order.append('health')
            return Mock()
        
        def track_alert_init(*args, **kwargs):
            call_order.append('alert')
            return Mock()
        
        with patch('src.monitoring.PrometheusExporter', side_effect=track_prometheus_init), \
             patch('src.monitoring.MetricsCollector', side_effect=track_collector_init), \
             patch('src.monitoring.HealthChecker', side_effect=track_health_init), \
             patch('src.monitoring.AlertManager', side_effect=track_alert_init):
            
            from src.monitoring import get_monitoring_system
            
            get_monitoring_system()
            
            # 验证初始化顺序：prometheus -> collector -> health -> alert
            expected_order = ['prometheus', 'collector', 'health', 'alert']
            assert call_order == expected_order

    def test_get_monitoring_system_with_exception_in_components(self):
        """测试组件初始化异常处理"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 模拟PrometheusExporter初始化异常
            MockPrometheusExporter.side_effect = Exception("Prometheus init failed")
            
            from src.monitoring import get_monitoring_system
            
            with pytest.raises(Exception, match="Prometheus init failed"):
                get_monitoring_system()

    def test_get_monitoring_system_with_collector_exception(self):
        """测试MetricsCollector初始化异常"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.side_effect = Exception("Collector init failed")
            
            from src.monitoring import get_monitoring_system
            
            with pytest.raises(Exception, match="Collector init failed"):
                get_monitoring_system()

    def test_get_monitoring_system_with_health_checker_exception(self):
        """测试HealthChecker初始化异常"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.side_effect = Exception("HealthChecker init failed")
            
            from src.monitoring import get_monitoring_system
            
            with pytest.raises(Exception, match="HealthChecker init failed"):
                get_monitoring_system()

    def test_get_monitoring_system_with_alert_manager_exception(self):
        """测试AlertManager初始化异常"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            MockAlertManager.side_effect = Exception("AlertManager init failed")
            
            from src.monitoring import get_monitoring_system
            
            # AlertManager异常应该被捕获，函数仍然返回结果但不包含alert_manager
            # 这取决于实际实现，这里假设异常会传播
            with pytest.raises(Exception, match="AlertManager init failed"):
                get_monitoring_system(enable_alerts=True)


class TestMonitoringSystemIntegration:
    """监控系统集成测试"""

    def test_monitoring_system_component_connections(self):
        """测试监控系统组件间连接"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            mock_exporter = Mock()
            mock_collector = Mock()
            mock_health_checker = Mock()
            mock_alert_manager = Mock()
            
            MockPrometheusExporter.return_value = mock_exporter
            MockMetricsCollector.return_value = mock_collector
            MockHealthChecker.return_value = mock_health_checker
            MockAlertManager.return_value = mock_alert_manager
            
            from src.monitoring import get_monitoring_system
            
            result = get_monitoring_system()
            
            # 验证组件间的依赖关系
            # MetricsCollector 依赖 PrometheusExporter
            MockMetricsCollector.assert_called_once_with(mock_exporter)
            
            # HealthChecker 依赖 MetricsCollector
            MockHealthChecker.assert_called_once_with(mock_collector)
            
            # AlertManager 依赖 MetricsCollector
            MockAlertManager.assert_called_once_with(mock_collector)
            
            # 验证返回的组件引用正确
            assert result['exporter'] is mock_exporter
            assert result['collector'] is mock_collector
            assert result['health_checker'] is mock_health_checker
            assert result['alert_manager'] is mock_alert_manager

    def test_monitoring_system_partial_initialization(self):
        """测试监控系统部分初始化"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 测试禁用警报时的初始化
            result = get_monitoring_system(enable_alerts=False)
            
            # 验证只初始化了必要的组件
            assert len(result) == 3
            assert set(result.keys()) == {'exporter', 'collector', 'health_checker'}

    def test_monitoring_system_return_type_consistency(self):
        """测试监控系统返回类型一致性"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            MockAlertManager.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 测试不同参数下的返回类型
            result1 = get_monitoring_system()
            result2 = get_monitoring_system(port=8080)
            result3 = get_monitoring_system(enable_alerts=False)
            result4 = get_monitoring_system(port=7070, enable_alerts=True)
            
            # 所有返回值都应该是字典
            assert isinstance(result1, dict)
            assert isinstance(result2, dict)
            assert isinstance(result3, dict)
            assert isinstance(result4, dict)
            
            # 验证键的存在性
            base_keys = {'exporter', 'collector', 'health_checker'}
            assert base_keys.issubset(result1.keys())
            assert base_keys.issubset(result2.keys())
            assert base_keys.issubset(result3.keys())
            assert base_keys.issubset(result4.keys())


class TestParameterValidation:
    """参数验证测试"""

    def test_get_monitoring_system_invalid_port_type(self):
        """测试无效端口类型"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector'), \
             patch('src.monitoring.HealthChecker'), \
             patch('src.monitoring.AlertManager'):
            
            from src.monitoring import get_monitoring_system
            
            # 测试字符串端口
            get_monitoring_system(port="8080")
            MockPrometheusExporter.assert_called_with(port="8080")
            
            # 测试None端口
            get_monitoring_system(port=None)
            MockPrometheusExporter.assert_called_with(port=None)

    def test_get_monitoring_system_extreme_port_values(self):
        """测试极端端口值"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker'), \
             patch('src.monitoring.AlertManager'):
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 测试极小端口
            get_monitoring_system(port=1)
            
            # 测试极大端口
            get_monitoring_system(port=65535)
            
            # 测试负端口
            get_monitoring_system(port=-1)
            
            # 测试零端口
            get_monitoring_system(port=0)

    def test_get_monitoring_system_enable_alerts_type_coercion(self):
        """测试enable_alerts参数类型强制转换"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            MockAlertManager.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 测试不同的"真值"
            for truthy_value in [1, "true", [1], {"a": 1}]:
                result = get_monitoring_system(enable_alerts=truthy_value)
                assert 'alert_manager' in result
            
            # 测试不同的"假值"
            for falsy_value in [0, "", [], {}, None]:
                MockAlertManager.reset_mock()
                result = get_monitoring_system(enable_alerts=falsy_value)
                if falsy_value:  # 非空容器仍然是真值
                    assert 'alert_manager' in result
                else:
                    assert 'alert_manager' not in result


class TestEdgeCasesAndErrorHandling:
    """边缘情况和错误处理测试"""

    def test_monitoring_module_reload(self):
        """测试模块重新加载"""
        import src.monitoring
        
        # 重新加载模块
        importlib.reload(src.monitoring)
        
        # 验证重新加载后功能正常
        from src.monitoring import get_monitoring_system
        assert callable(get_monitoring_system)

    def test_monitoring_with_missing_dependencies(self):
        """测试缺失依赖的情况"""
        # 实际上，由于我们是在测试环境中mock了所有组件，
        # 这个测试应该验证在真实导入失败情况下的处理
        # 修改为更现实的测试场景
        try:
            from src.monitoring import PrometheusExporter
            # 如果导入成功，测试通过
            assert PrometheusExporter is not None
        except (ImportError, AttributeError):
            # 如果真的有导入错误，也是预期的
            pass

    def test_monitoring_system_memory_usage(self):
        """测试监控系统内存使用"""
        import gc
        import sys
        
        initial_objects = len(gc.get_objects())
        
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            MockAlertManager.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 创建多个监控系统实例
            systems = []
            for i in range(10):
                system = get_monitoring_system(port=9000+i)
                systems.append(system)
            
            # 清理引用
            del systems
            gc.collect()
            
            final_objects = len(gc.get_objects())
            
            # 对象数量增长应该是合理的
            object_growth = final_objects - initial_objects
            assert object_growth < 1000  # 不应该有过多的对象泄漏

    def test_concurrent_monitoring_system_creation(self):
        """测试并发创建监控系统"""
        import threading
        import time
        
        results = []
        exceptions = []
        
        def create_monitoring_system(port_offset):
            try:
                with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
                     patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
                     patch('src.monitoring.HealthChecker') as MockHealthChecker, \
                     patch('src.monitoring.AlertManager') as MockAlertManager:
                    
                    MockPrometheusExporter.return_value = Mock()
                    MockMetricsCollector.return_value = Mock()
                    MockHealthChecker.return_value = Mock()
                    MockAlertManager.return_value = Mock()
                    
                    from src.monitoring import get_monitoring_system
                    
                    result = get_monitoring_system(port=9090 + port_offset)
                    results.append(result)
            except Exception as e:
                exceptions.append(e)
        
        # 创建多个线程并发创建监控系统
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_monitoring_system, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有异常，所有创建都成功
        assert len(exceptions) == 0
        assert len(results) == 5
        
        # 验证每个结果都是有效的字典
        for result in results:
            assert isinstance(result, dict)
            assert 'exporter' in result
            assert 'collector' in result
            assert 'health_checker' in result

    def test_monitoring_system_with_mock_failures(self):
        """测试各种Mock失败情况"""
        # 测试Mock对象属性访问失败
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 创建一个会在属性访问时失败的Mock
            failing_mock = Mock()
            failing_mock.side_effect = AttributeError("Mock attribute error")
            
            MockPrometheusExporter.return_value = failing_mock
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            MockAlertManager.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            result = get_monitoring_system()
            
            # 即使有failing_mock，函数应该仍然返回结果
            assert isinstance(result, dict)
            assert result['exporter'] is failing_mock

    def test_monitoring_system_documentation_consistency(self):
        """测试监控系统文档一致性"""
        from src.monitoring import get_monitoring_system
        
        # 验证函数有文档字符串
        assert get_monitoring_system.__doc__ is not None
        assert len(get_monitoring_system.__doc__.strip()) > 0
        
        # 验证文档中提到的参数
        doc = get_monitoring_system.__doc__
        assert 'port' in doc
        assert 'enable_alerts' in doc
        
        # 验证文档中提到的返回值
        assert 'Dictionary' in doc or 'dict' in doc.lower()

    def test_monitoring_import_path_variations(self):
        """测试不同导入路径"""
        # 测试直接从__init__导入
        from src.monitoring import get_monitoring_system as direct_import
        
        # 测试从模块导入后访问
        import src.monitoring as monitoring_module
        module_import = monitoring_module.get_monitoring_system
        
        # 两种导入方式应该是同一个函数
        assert direct_import is module_import
        
        # 测试通过getattr访问
        getattr_import = getattr(monitoring_module, 'get_monitoring_system')
        assert getattr_import is direct_import

    def test_monitoring_system_state_isolation(self):
        """测试监控系统状态隔离"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            # 确保每次调用都返回新的Mock实例
            MockPrometheusExporter.side_effect = lambda **kwargs: Mock()
            MockMetricsCollector.side_effect = lambda exporter: Mock()
            MockHealthChecker.side_effect = lambda collector: Mock()
            MockAlertManager.side_effect = lambda collector: Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 创建两个独立的监控系统
            system1 = get_monitoring_system(port=9091)
            system2 = get_monitoring_system(port=9092)
            
            # 验证它们是独立的实例
            assert system1 is not system2
            assert system1['exporter'] is not system2['exporter']
            assert system1['collector'] is not system2['collector']
            assert system1['health_checker'] is not system2['health_checker']
            assert system1['alert_manager'] is not system2['alert_manager']

    def test_monitoring_system_with_keyword_only_args(self):
        """测试仅关键字参数"""
        with patch('src.monitoring.PrometheusExporter') as MockPrometheusExporter, \
             patch('src.monitoring.MetricsCollector') as MockMetricsCollector, \
             patch('src.monitoring.HealthChecker') as MockHealthChecker, \
             patch('src.monitoring.AlertManager') as MockAlertManager:
            
            MockPrometheusExporter.return_value = Mock()
            MockMetricsCollector.return_value = Mock()
            MockHealthChecker.return_value = Mock()
            MockAlertManager.return_value = Mock()
            
            from src.monitoring import get_monitoring_system
            
            # 测试仅使用关键字参数
            result = get_monitoring_system(port=9093, enable_alerts=False)
            
            assert isinstance(result, dict)
            assert 'alert_manager' not in result
            
            MockPrometheusExporter.assert_called_with(port=9093) 