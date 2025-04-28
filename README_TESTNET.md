# Binance Testnet 交易指南

本项目使用 Binance Testnet（币安测试网）实现实时交易，无需修改原有的回测系统代码。

## 快速开始

### 1. 获取 Testnet API Key 和 Secret

1. 访问 [Binance Testnet](https://testnet.binance.vision/)
2. 点击 "Get API Key" 按钮
3. 完成验证后，会获得API Key和Secret（请妥善保存）

### 2. 配置API密钥

编辑 `config.ini` 文件，填入你的 API Key 和 Secret：

```ini
[BINANCE]
API_KEY = RJ36X1UYesKrUwf6rnIQkkd5Cfyk2f0Epe719Xb9q2PR28QcrKdPZ5jBL2qGMehr
API_SECRET = uimocTQN5g8RF1P9UZN9zQ0rLuqIXrot4xuABgJZjbWRgoU0NOxoUvlG8lyfey1S

[TRADING]
SYMBOL = BTCUSDT
RISK_FRACTION = 0.02
FAST_WINDOW = 7
SLOW_WINDOW = 20
ATR_WINDOW = 14
```

### 3. 运行交易脚本

```bash
# 测试模式（不执行实际交易）
python live_trade.py --test

# 实盘模式（使用日线K线，默认设置）
python live_trade.py

# 使用不同K线周期
python live_trade.py --interval 1h  # 1小时线
python live_trade.py --interval 15m  # 15分钟线

# 使用自定义配置文件
python live_trade.py --config my_config.ini
```

## 项目结构

```
├── config.ini                # 配置文件
├── src/
│   ├── broker.py             # 原有的回测逻辑（未修改）
│   ├── signals.py            # 信号生成（未修改）
│   └── binance_client.py     # 新增：Binance API客户端
├── live_trade.py             # 新增：实时交易脚本
└── trades.csv                # 新增：交易日志
```

## 特点

1. **最小化修改**：直接复用回测系统的核心逻辑
2. **透明的交易日志**：所有交易记录在 `trades.csv` 中
3. **风险管理**：使用与回测系统相同的ATR止损和风险比例仓位管理
4. **移动止损**：支持通过API更新止损价格
5. **测试模式**：可以在不执行实际交易的情况下测试策略

## 注意事项

1. 仅支持 BTCUSDT 交易对
2. 交易数量会自动舍入到小数点后3位（0.001 BTC）
3. 确保您的Testnet账户中有足够的测试USDT

## 故障排除

- 如果API连接失败，确认您的API密钥已经正确配置
- 查看交易日志文件 `trades.csv` 以跟踪所有交易记录
- 检查 Binance Testnet 网站上的订单历史，确认交易执行情况

# 重新获取新的API密钥并更新config.ini后再次运行
python live_trade.py --test 