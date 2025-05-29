# 数据源配置指南

本文档介绍如何配置和使用交易系统中的市场数据源。系统支持多个数据源，并且能够在主要数据源不可用时自动切换到备用数据源。

## 支持的数据源

目前系统支持以下数据源：

1. **币安测试网（Binance Testnet）** - 使用币安测试网API获取实时行情数据
2. **模拟数据（Mock Data）** - 生成模拟的市场数据用于测试

## 配置方式

系统支持多种配置方式，按优先级排序：

1. 命令行参数（最高优先级）
2. 环境变量（`.env`文件）
3. YAML配置文件（`config.yaml`）
4. INI配置文件（`config.ini`，向后兼容旧版）
5. 默认值（最低优先级）

### YAML配置文件（推荐）

YAML配置文件提供了更结构化和可读性更强的配置方式：

```yaml
# 交易配置
trading:
  # 交易对列表
  symbols:
    - BTC/USDT
    - ETH/USDT
    - LTC/USDT
  # 风险百分比
  risk_percent: 0.5
  # 检查间隔(秒)
  check_interval: 60
  # 测试模式
  test_mode: true
  # 技术指标参数
  indicators:
    fast_ma: 7
    slow_ma: 25
    atr_period: 14

# 数据源配置
data_sources:
  # 是否使用币安测试网
  use_binance_testnet: true
  # 自动切换数据源
  auto_fallback: true
  # 切换间隔(秒)
  min_switch_interval: 300

# 日志配置
logging:
  # 日志级别
  level: INFO
  # 日志目录
  log_dir: logs/stability_test
  # 是否记录到控制台
  console: true
  # 日志文件最大大小(MB)
  max_file_size_mb: 10
  # 保留日志文件数
  backup_count: 5
```

### 环境变量（`.env`文件）

环境变量适合存储敏感信息，如API密钥：

```
# 币安测试网API密钥
BINANCE_TESTNET_API_KEY=your_api_key_here
BINANCE_TESTNET_API_SECRET=your_api_secret_here

# 日志级别
LOG_LEVEL=INFO

# 生产环境标志
PRODUCTION=false
```

环境变量可以通过系统环境变量设置，也可以通过`.env`文件设置。

### INI配置文件（向后兼容）

旧版的INI配置文件格式依然支持：

```ini
[general]
# 一般设置
symbols = BTC/USDT,ETH/USDT
risk_percent = 0.5
check_interval = 60
test_mode = true

[data_sources]
# 数据源设置
use_binance_testnet = true
# 是否在Binance测试网不可用时自动切换到模拟数据
auto_fallback = true
# 数据源切换后的最小重试间隔(秒)
min_switch_interval = 300

[binance_testnet]
# 币安测试网API密钥
api_key = YOUR_BINANCE_TESTNET_API_KEY
api_secret = YOUR_BINANCE_TESTNET_API_SECRET

[logging]
# 日志设置
level = INFO
log_dir = logs/stability_test
```

## 命令行参数

运行稳定性测试时，可以使用命令行参数控制数据源和配置：

```bash
# 使用YAML配置文件
python scripts/stability_test.py --config-yaml path/to/config.yaml

# 使用环境变量文件
python scripts/stability_test.py --env-file path/to/.env

# 使用INI配置文件(向后兼容)
python scripts/stability_test.py --config path/to/config.ini

# 组合使用多种配置方式
python scripts/stability_test.py --config-yaml path/to/config.yaml --env-file path/to/.env
```

## 获取币安测试网API密钥

要使用币安测试网数据源，需要获取API密钥：

1. 访问 [币安测试网](https://testnet.binance.vision/)
2. 使用GitHub或Google账号登录
3. 在页面上生成新的API密钥
4. 将生成的密钥添加到环境变量或`.env`文件中

## 数据源热切换机制

系统支持数据源的热切换，当主数据源不可用时会自动切换到备用数据源：

1. 系统默认配置使用币安测试网作为主数据源，模拟数据作为备用
2. 当检测到币安测试网不可用或返回错误时，自动切换到模拟数据
3. 系统会定期检查主数据源是否恢复，并在恢复后自动切换回主数据源
4. 为防止频繁切换，系统设置了最小切换间隔（默认300秒）

## 日志与监控

数据源切换事件会被记录在日志中：

```
2025-05-01 09:37:35,442 - stability_test - INFO - 模拟网络中断...
2025-05-01 09:37:40,443 - stability_test - INFO - 恢复连接...
2025-05-01 09:37:41,443 - market_data - INFO - 数据源切换: BinanceTestnet -> MockMarket
```

稳定性测试报告中会包含数据源切换次数：

```
====== 最终稳定性测试报告 ======
开始时间: 2025-05-01 12:00:00.123456
运行时长: 3.00 天
交易对: BTC/USDT, ETH/USDT
当前数据源: MockMarket

性能指标:
- 总信号数: 124
- 错误次数: 0
- 每小时错误率: 0.0000
- 数据中断次数: 2
- 重连次数: 2
- 数据源切换次数: 3
- 平均内存使用: 5.59 MB
- 最大内存使用: 11.71 MB

系统状态: 稳定
```

## 使用脚本运行测试

项目提供了便捷的脚本运行稳定性测试：

```bash
# 使用默认设置运行3天的测试
./scripts/run_stability_test.sh

# 指定测试时长和间隔
./scripts/run_stability_test.sh --days 1 --interval 30

# 仅使用模拟数据
./scripts/run_stability_test.sh --mock-only

# 使用INI配置文件
./scripts/run_stability_test.sh --config path/to/config.ini

# 使用YAML配置文件
./scripts/run_stability_test.sh --config-yaml path/to/config.yaml

# 使用环境变量文件
./scripts/run_stability_test.sh --env-file path/to/.env

# 指定交易对
./scripts/run_stability_test.sh --symbols "BTC/USDT,ETH/USDT,LTC/USDT"

# 生产模式(执行实际交易)
./scripts/run_stability_test.sh --production
```

## 配置优先级说明

当多种配置方式同时存在时，系统按照以下优先级处理：

1. 命令行参数覆盖所有其他配置
2. 环境变量覆盖配置文件中的相同配置
3. YAML配置文件覆盖INI配置文件
4. INI配置文件覆盖默认值

例如，如果在命令行中指定了`--mock-only`，即使配置文件中设置了`use_binance_testnet=true`，系统也会仅使用模拟数据。

## 故障排除

如果遇到数据源连接问题：

1. 检查API密钥是否正确
2. 确认网络连接正常
3. 验证测试网是否可用：`curl https://testnet.binance.vision/api/v3/ping`
4. 检查日志文件中的错误信息

如需其他帮助，请参考系统完整文档或联系开发团队。 