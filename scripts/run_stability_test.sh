#!/bin/bash
# 运行稳定性测试的脚本
# Script to run a stability test

set -e

# 确保在项目根目录运行
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# 创建日志目录
LOG_DIR="$ROOT_DIR/logs/stability_test_$(date +%Y%m%d)"
mkdir -p "$LOG_DIR"

# 安装必要的依赖
echo "正在检查并安装必要的依赖..."
pip install --quiet psutil
pip install --quiet -r requirements.txt

# 生成唯一的测试ID
TEST_ID=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/stability_test_$TEST_ID.log"

# 设置测试参数
SYMBOLS="BTC/USDT,ETH/USDT"
DAYS=3
INTERVAL=60  # 每分钟检查一次
RISK=0.5     # 降低风险系数进行测试

echo "==============================================" | tee -a "$LOG_FILE"
echo "开始稳定性测试 (ID: $TEST_ID)" | tee -a "$LOG_FILE"
echo "测试时间: $(date)" | tee -a "$LOG_FILE" 
echo "测试交易对: $SYMBOLS" | tee -a "$LOG_FILE"
echo "持续时间: $DAYS 天" | tee -a "$LOG_FILE"
echo "检查间隔: $INTERVAL 秒" | tee -a "$LOG_FILE"
echo "风险系数: $RISK" | tee -a "$LOG_FILE"
echo "日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
echo "==============================================" | tee -a "$LOG_FILE"

# 启动守护进程监控
monitor_pid=""

# 检测操作系统类型
OS_TYPE=$(uname)

# 函数：监控测试进程
function monitor_test() {
    local pid=$1
    local log_file=$2
    local check_interval=300  # 每5分钟检查一次

    echo "启动监控进程..." | tee -a "$log_file"
    
    while true; do
        if ! ps -p $pid > /dev/null; then
            echo "警告: 测试进程 $pid 不再运行，退出监控." | tee -a "$log_file"
            return 1
        fi
        
        # 记录系统状态 - 根据操作系统调整命令
        echo "--- $(date) ---" >> "$LOG_DIR/system_status_$TEST_ID.log"
        
        # CPU使用率
        echo "CPU使用率:" >> "$LOG_DIR/system_status_$TEST_ID.log"
        if [ "$OS_TYPE" = "Darwin" ]; then
            # macOS
            top -l 1 | head -n 12 >> "$LOG_DIR/system_status_$TEST_ID.log"
        else
            # Linux
            top -bn1 | head -n 12 >> "$LOG_DIR/system_status_$TEST_ID.log"
        fi
        echo "" >> "$LOG_DIR/system_status_$TEST_ID.log"
        
        # 内存使用率
        echo "内存使用率:" >> "$LOG_DIR/system_status_$TEST_ID.log"
        if [ "$OS_TYPE" = "Darwin" ]; then
            # macOS
            vm_stat >> "$LOG_DIR/system_status_$TEST_ID.log"
        else
            # Linux
            free -m >> "$LOG_DIR/system_status_$TEST_ID.log"
        fi
        echo "" >> "$LOG_DIR/system_status_$TEST_ID.log"
        
        # 磁盘使用率
        echo "磁盘使用率:" >> "$LOG_DIR/system_status_$TEST_ID.log"
        df -h >> "$LOG_DIR/system_status_$TEST_ID.log"
        echo "" >> "$LOG_DIR/system_status_$TEST_ID.log"
        
        sleep $check_interval
    done
}

# 启动测试
echo "启动稳定性测试..." | tee -a "$LOG_FILE"
python scripts/stability_test.py \
    --symbols "$SYMBOLS" \
    --days "$DAYS" \
    --interval "$INTERVAL" \
    --risk "$RISK" \
    --log-dir "$LOG_DIR" >> "$LOG_FILE" 2>&1 &

TEST_PID=$!
echo "测试进程ID: $TEST_PID" | tee -a "$LOG_FILE"

# 启动监控
monitor_test $TEST_PID "$LOG_FILE" &
MONITOR_PID=$!
echo "监控进程ID: $MONITOR_PID" | tee -a "$LOG_FILE"

# 显示如何检查测试状态
echo "" | tee -a "$LOG_FILE"
echo "测试正在后台运行。您可以使用以下命令检查状态:" | tee -a "$LOG_FILE"
echo "  tail -f $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "要终止测试，请运行:" | tee -a "$LOG_FILE"
echo "  kill $TEST_PID $MONITOR_PID" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 保存进程ID以便后续控制
echo "$TEST_PID $MONITOR_PID" > "$LOG_DIR/pids.txt"

# 计算结束日期 - 兼容不同操作系统
if [ "$OS_TYPE" = "Darwin" ]; then
    # macOS 使用date -v
    END_DATE=$(date -v+${DAYS}d)
else
    # Linux 使用date -d
    END_DATE=$(date -d "$DAYS days")
fi

echo "测试预计将在 $END_DATE 完成" | tee -a "$LOG_FILE"
echo "完成后将在 $LOG_DIR 生成测试报告" | tee -a "$LOG_FILE" 