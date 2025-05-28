#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场数据提供者 - 接口和实现
Market Data Provider - Interface and implementations
"""

import abc
import datetime
import json
import logging
import os
import random
import time
from typing import Dict, List, Optional, Tuple, Union

import requests
from requests.exceptions import RequestException

logger = logging.getLogger("market_data")

# 导入配置管理器
try:
    # 尝试导入增强配置管理器
    from scripts.enhanced_config import get_config

    logger.info("使用增强配置管理器")
except ImportError:
    logger.info("无法导入增强配置管理器，尝试导入旧版配置管理器")
    try:
        # 如果无法导入增强版，则尝试导入旧版
        from scripts.config_manager import get_config

        logger.info("使用旧版配置管理器")
    except ImportError:
        # 如果都无法导入，使用默认值
        logger.warning("无法导入配置管理器，将使用默认值")
        get_config = None


class MarketDataProvider(abc.ABC):
    """市场数据提供者抽象基类"""

    @abc.abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[List]:
        """获取K线数据"""
        pass

    @abc.abstractmethod
    def get_ticker(self, symbol: str) -> Dict:
        """获取最新行情"""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        pass

    @abc.abstractmethod
    def get_name(self) -> str:
        """获取数据源名称"""
        pass


class MockMarketDataProvider(MarketDataProvider):
    """模拟市场数据提供者"""

    def __init__(self):
        self.last_prices = {}
        logger.info("初始化模拟市场数据提供者")

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[List]:
        """获取模拟K线数据"""
        now = time.time() * 1000  # 毫秒时间戳

        # 如果没有该交易对的上次价格，生成一个初始价格
        if symbol not in self.last_prices:
            self.last_prices[symbol] = 30000 + random.random() * 1000

        klines = []

        # 生成模拟K线数据
        for i in range(limit):
            # 每根K线向前推一个时间间隔
            timestamp = now - (limit - i) * self._get_interval_ms(interval)

            # 基于上一个价格生成新价格
            price = self.last_prices[symbol] * (1 + (random.random() - 0.5) * 0.01)
            self.last_prices[symbol] = price

            # 生成开高低收
            open_price = price * (1 + (random.random() - 0.5) * 0.005)
            high_price = max(open_price, price) * (1 + random.random() * 0.005)
            low_price = min(open_price, price) * (1 - random.random() * 0.005)
            close_price = price

            # 生成成交量
            volume = random.random() * 100

            # 按照Binance K线格式构建
            kline = [
                int(timestamp),  # 开盘时间
                str(open_price),  # 开盘价
                str(high_price),  # 最高价
                str(low_price),  # 最低价
                str(close_price),  # 收盘价
                str(volume),  # 成交量
                int(timestamp) + self._get_interval_ms(interval) - 1,  # 收盘时间
                str(volume * price),  # 成交额
                100,  # 成交笔数
                str(volume * 0.6),  # 主动买入成交量
                str(volume * price * 0.6),  # 主动买入成交额
                "0",  # 忽略
            ]
            klines.append(kline)

        return klines

    def get_ticker(self, symbol: str) -> Dict:
        """获取最新模拟行情"""
        if symbol not in self.last_prices:
            self.last_prices[symbol] = 30000 + random.random() * 1000

        price = self.last_prices[symbol] * (1 + (random.random() - 0.5) * 0.001)
        self.last_prices[symbol] = price

        return {"symbol": symbol, "price": str(price), "time": int(time.time() * 1000)}

    def is_available(self) -> bool:
        """模拟数据源始终可用"""
        return True

    def get_name(self) -> str:
        """获取数据源名称"""
        return "MockMarket"

    def _get_interval_ms(self, interval: str) -> int:
        """转换时间间隔为毫秒数"""
        unit = interval[-1]
        value = int(interval[:-1])

        if unit == "m":
            return value * 60 * 1000
        elif unit == "h":
            return value * 60 * 60 * 1000
        elif unit == "d":
            return value * 24 * 60 * 60 * 1000
        elif unit == "w":
            return value * 7 * 24 * 60 * 60 * 1000
        else:
            return 60000  # 默认1分钟


class BinanceTestnetDataProvider(MarketDataProvider):
    """币安测试网数据提供者"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.base_url = "https://testnet.binance.vision/api/v3"
        self.api_key = api_key
        self.api_secret = api_secret
        self.last_check = 0
        self.available = True
        self.headers = {"X-MBX-APIKEY": api_key} if api_key else {}
        logger.info("初始化币安测试网数据提供者")

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[List]:
        """获取K线数据"""
        try:
            # 构建请求参数
            params = {"symbol": symbol.replace("/", ""), "interval": interval, "limit": limit}

            # 发送请求
            url = f"{self.base_url}/klines"
            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            # 检查响应
            if response.status_code != 200:
                logger.error(f"获取K线失败: {response.text}")
                self.available = False
                return []

            self.available = True
            return response.json()

        except RequestException as e:
            logger.error(f"获取K线请求异常: {e}")
            self.available = False
            return []
        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            self.available = False
            return []

    def get_ticker(self, symbol: str) -> Dict:
        """获取最新行情"""
        try:
            # 构建请求参数
            params = {"symbol": symbol.replace("/", "")}

            # 发送请求
            url = f"{self.base_url}/ticker/price"
            response = requests.get(url, params=params, headers=self.headers, timeout=5)

            # 检查响应
            if response.status_code != 200:
                logger.error(f"获取行情失败: {response.text}")
                self.available = False
                return {}

            self.available = True
            return response.json()

        except RequestException as e:
            logger.error(f"获取行情请求异常: {e}")
            self.available = False
            return {}
        except Exception as e:
            logger.error(f"获取行情数据异常: {e}")
            self.available = False
            return {}

    def is_available(self) -> bool:
        """检查数据源是否可用"""
        # 每60秒检查一次可用性
        now = time.time()
        if now - self.last_check < 60 and self.available:
            return self.available

        try:
            self.last_check = now
            response = requests.get(f"{self.base_url}/ping", timeout=5)
            self.available = response.status_code == 200
            return self.available
        except Exception:
            self.available = False
            return False

    def get_name(self) -> str:
        """获取数据源名称"""
        return "BinanceTestnet"


class MarketDataManager:
    """市场数据管理器 - 管理多个数据源，支持热切换"""

    def __init__(
        self,
        primary_provider: MarketDataProvider,
        backup_provider: MarketDataProvider,
        min_switch_interval: int = 300,
    ):
        self.primary = primary_provider
        self.backup = backup_provider
        self.using_primary = True
        self.last_switch_time = 0
        self.min_switch_interval = min_switch_interval  # 最小切换间隔(秒)
        logger.info(
            f"初始化市场数据管理器: 主源={primary_provider.get_name()}, 备源={backup_provider.get_name()}"
        )

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[List]:
        """获取K线数据，自动选择可用数据源"""
        provider = self._get_available_provider()
        result = provider.get_klines(symbol, interval, limit)

        # 如果数据为空且当前使用主源，尝试切换到备源
        if not result and self.using_primary:
            logger.warning(
                f"主数据源({self.primary.get_name()})返回空数据，尝试切换到备源({self.backup.get_name()})"
            )
            self._switch_to_backup()
            provider = self.backup
            result = provider.get_klines(symbol, interval, limit)

        return result

    def get_ticker(self, symbol: str) -> Dict:
        """获取最新行情，自动选择可用数据源"""
        provider = self._get_available_provider()
        result = provider.get_ticker(symbol)

        # 如果数据为空且当前使用主源，尝试切换到备源
        if not result and self.using_primary:
            logger.warning(
                f"主数据源({self.primary.get_name()})返回空数据，尝试切换到备源({self.backup.get_name()})"
            )
            self._switch_to_backup()
            provider = self.backup
            result = provider.get_ticker(symbol)

        return result

    def _get_available_provider(self) -> MarketDataProvider:
        """获取当前可用的数据提供者"""
        now = time.time()

        # 如果当前使用主源，检查是否可用
        if self.using_primary:
            if self.primary.is_available():
                return self.primary
            else:
                # 如果主源不可用且满足切换条件，切换到备源
                if now - self.last_switch_time > self.min_switch_interval:
                    logger.warning(
                        f"主数据源({self.primary.get_name()})不可用，切换到备源({self.backup.get_name()})"
                    )
                    self._switch_to_backup()
                    return self.backup
                else:
                    # 未达到切换间隔，继续使用主源
                    logger.warning(
                        f"主数据源({self.primary.get_name()})不可用，但未达到切换间隔，继续尝试"
                    )
                    return self.primary
        else:
            # 当前使用备源，检查主源是否恢复
            if (
                self.primary.is_available()
                and now - self.last_switch_time > self.min_switch_interval
            ):
                logger.info(f"主数据源({self.primary.get_name()})已恢复，切换回主源")
                self._switch_to_primary()
                return self.primary
            else:
                return self.backup

    def _switch_to_backup(self):
        """切换到备用数据源"""
        self.using_primary = False
        self.last_switch_time = time.time()
        logger.info(f"数据源切换: {self.primary.get_name()} -> {self.backup.get_name()}")

    def _switch_to_primary(self):
        """切换回主数据源"""
        self.using_primary = True
        self.last_switch_time = time.time()
        logger.info(f"数据源切换: {self.backup.get_name()} -> {self.primary.get_name()}")

    def get_current_provider_name(self) -> str:
        """获取当前使用的数据源名称"""
        return self.primary.get_name() if self.using_primary else self.backup.get_name()


# 创建数据提供者和管理器的工厂函数
def create_market_data_manager(use_binance_testnet: bool = True) -> MarketDataManager:
    """创建市场数据管理器"""
    # 创建模拟数据提供者作为备用
    mock_provider = MockMarketDataProvider()

    # 获取配置
    config = get_config() if get_config else None
    min_switch_interval = 300  # 默认切换间隔

    if config:
        # 如果有配置管理器，从配置中获取设置
        use_binance_testnet = config.use_binance_testnet() if use_binance_testnet else False
        min_switch_interval = config.get_min_switch_interval()

    if use_binance_testnet:
        # 获取API密钥
        api_key = None
        api_secret = None

        if config:
            # 从配置管理器获取API密钥
            api_key = config.get_binance_testnet_api_key()
            api_secret = config.get_binance_testnet_api_secret()
        else:
            # 直接从环境变量获取
            api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
            api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")

        # 创建币安测试网数据提供者作为主要源
        binance_provider = BinanceTestnetDataProvider(api_key, api_secret)

        # 如果币安测试网可用，将其作为主要数据源
        if binance_provider.is_available():
            manager = MarketDataManager(binance_provider, mock_provider, min_switch_interval)
        else:
            logger.warning("币安测试网不可用，使用模拟数据源作为主要数据源")
            manager = MarketDataManager(mock_provider, binance_provider, min_switch_interval)
    else:
        # 只使用模拟数据源
        manager = MarketDataManager(mock_provider, mock_provider, min_switch_interval)

    return manager
