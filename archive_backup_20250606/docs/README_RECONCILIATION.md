# 交易系统对账指南 (Trading System Reconciliation Guide)

本文档提供如何设置和使用交易系统的对账功能的说明。
This document provides instructions on how to set up and use the reconciliation feature of the trading system.

## 功能概述 (Features Overview)

1. **交易记录 (Trade Records)**
   - 所有交易自动记录到CSV文件
   - 按交易对分别存储
   - 生产环境保存到 `~/trades/YYYY/` 目录
   - 开发环境保存到 `./trades/` 目录

2. **日终对账 (Daily Reconciliation)**
   - 比较交易所数据与本地记录
   - 验证账户余额
   - 生成详细对账报告
   - 异常时发送Telegram通知

## 设置指南 (Setup Guide)

### 1. 环境变量 (Environment Variables)

创建 `.env` 文件并设置以下环境变量:
Create a `.env` file and set the following environment variables:

```bash
# API密钥 (API Keys)
API_KEY=your_api_key
API_SECRET=your_api_secret

# Telegram 通知 (Telegram Notifications)
TG_TOKEN=your_telegram_bot_token
TG_CHAT_ID=your_telegram_chat_id

# 交易数据目录 (Trades Data Directory)
# 开发环境 (Development): ./trades
# 生产环境 (Production): ~/trades
TRADES_DIR=./trades
```

### 2. 设置 Cron 任务 (Setup Cron Job)

编辑 crontab:
Edit crontab:

```bash
crontab -e
```

添加以下行来设置每天午夜运行对账:
Add the following line to run reconciliation at midnight every day:

```
0 0 * * * /完整路径/scripts/daily_reconciliation.sh
```

对于特定时区的调整，可以修改上面的时间:
For timezone-specific adjustments, modify the time above:

```
# 北京时间早上8点 (8:00 AM Beijing Time)
0 8 * * * /完整路径/scripts/daily_reconciliation.sh
```

## 手动对账 (Manual Reconciliation)

可以通过以下命令手动运行对账:
You can manually run reconciliation with the following command:

```bash
# 使用昨天日期 (Using yesterday's date)
python -m src.reconcile --symbol BTCUSDT

# 指定日期 (Specific date)
python -m src.reconcile --symbol BTCUSDT --date 2023-10-15

# 多个参数 (Multiple parameters)
python -m src.reconcile --symbol BTCUSDT --date 2023-10-15 --trades-dir ~/trades --no-notify
```

## 对账报告 (Reconciliation Reports)

对账报告保存在以下目录:
Reconciliation reports are saved in the following directory:

```
/trades/reconciliation/
```

报告包含以下文件:
Reports include the following files:

- `reconciliation_SYMBOL_DATE_TIMESTAMP_matched.csv` - 匹配的交易 (Matched trades)
- `reconciliation_SYMBOL_DATE_TIMESTAMP_exchange_only.csv` - 仅交易所有的交易 (Exchange-only trades)
- `reconciliation_SYMBOL_DATE_TIMESTAMP_local_only.csv` - 仅本地有的交易 (Local-only trades)
- `reconciliation_SYMBOL_DATE_TIMESTAMP_balance.json` - 余额信息 (Balance information)
- `reconciliation_SYMBOL_DATE_TIMESTAMP_summary.json` - 摘要报告 (Summary report)

## 异常通知 (Error Notifications)

当对账发现异常时 (例如交易记录不匹配)，系统将通过 Telegram 发送通知。
When reconciliation finds discrepancies (e.g., mismatched trade records), the system will send a notification via Telegram.

异常示例:
Example notification:

```
⚠️ 对账异常 (Reconciliation Issue)
日期 (Date): 2023-10-15
品种 (Symbol): BTCUSDT
匹配交易 (Matched): 5条
仅交易所 (Exchange only): 1条
仅本地 (Local only): 0条
请检查对账报告 (Please check reconciliation report)
```

## 故障排除 (Troubleshooting)

1. **cron 不执行 (Cron not executing)**
   - 检查脚本权限: `chmod +x scripts/daily_reconciliation.sh`
   - 检查 cron 日志: `grep CRON /var/log/syslog`

2. **对账失败 (Reconciliation failing)**
   - 检查环境变量是否正确设置
   - 查看日志文件: `logs/reconciliation_YYYYMMDD.log`

3. **未收到通知 (Not receiving notifications)**
   - 确认 TG_TOKEN 和 TG_CHAT_ID 设置正确
   - 检查机器人权限 