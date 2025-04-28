#!/bin/bash
# Daily reconciliation script for trading system
# 交易系统日终对账脚本
#
# 使用方法 (Usage):
# 1. 设置为可执行 (Make executable): chmod +x daily_reconciliation.sh
# 2. 添加到crontab (Add to crontab): 0 0 * * * /path/to/daily_reconciliation.sh
#
# 也可以手动执行 (Can also be run manually): ./daily_reconciliation.sh

# 设置工作目录 (Set working directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit 1

# 设置环境变量 (Set environment variables)
# 生产环境应该从安全位置加载这些变量 (Production should load these from a secure location)
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment variables from .env"
    source "$PROJECT_ROOT/.env"
fi

# 必要的环境变量检查 (Check for necessary environment variables)
if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ] || [ -z "$TG_TOKEN" ]; then
    echo "ERROR: API_KEY, API_SECRET, or TG_TOKEN environment variables not set"
    exit 1
fi

# 获取昨天的日期 (Get yesterday's date)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# 交易对列表 (Trading pairs list)
# 可以根据需要修改 (Can be modified as needed)
SYMBOLS=("BTCUSDT" "ETHUSDT")

# 日志文件 (Log file)
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/reconciliation_$(date +%Y%m%d).log"

# 记录脚本开始 (Log script start)
echo "===== 开始日终对账 (Starting daily reconciliation) $(date) =====" | tee -a "$LOG_FILE"

# 为每个交易对执行对账 (Run reconciliation for each trading pair)
for SYMBOL in "${SYMBOLS[@]}"; do
    echo "对账交易对 (Reconciling trading pair): $SYMBOL" | tee -a "$LOG_FILE"
    
    # 执行对账脚本 (Run reconciliation script)
    python -m src.reconcile --symbol "$SYMBOL" --date "$YESTERDAY" 2>&1 | tee -a "$LOG_FILE"
    
    # 检查上一个命令的退出状态 (Check exit status of last command)
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo "错误: 对账$SYMBOL失败 (Error: Reconciliation failed for $SYMBOL)" | tee -a "$LOG_FILE"
    fi
    
    echo "完成对账: $SYMBOL (Completed reconciliation: $SYMBOL)" | tee -a "$LOG_FILE"
    echo "-----------------------------------------" | tee -a "$LOG_FILE"
done

# 记录脚本结束 (Log script end)
echo "===== 日终对账完成 (Daily reconciliation completed) $(date) =====" | tee -a "$LOG_FILE" 