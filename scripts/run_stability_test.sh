#!/bin/bash
# 稳定性测试运行脚本

# 设置路径和环境变量
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
LOG_DIR="$PROJECT_ROOT/logs/stability_test_$(date +%Y%m%d)"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 默认参数
DAYS=3
INTERVAL=60
MOCK_ONLY=0
CONFIG_FILE=""
CONFIG_YAML=""
ENV_FILE=""
SYMBOLS=""
MONITORING_PORT=9090
PRESERVE_LOGS=1  # 默认保留完整日志

# 处理命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --days)
      DAYS="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --mock-only)
      MOCK_ONLY=1
      shift
      ;;
    --config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    --config-yaml)
      CONFIG_YAML="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --symbols)
      SYMBOLS="$2"
      shift 2
      ;;
    --monitoring-port)
      MONITORING_PORT="$2"
      shift 2
      ;;
    --no-preserve-logs)
      PRESERVE_LOGS=0
      shift
      ;;
    --help)
      echo "稳定性测试运行脚本"
      echo ""
      echo "用法: $0 [选项]"
      echo ""
      echo "选项:"
      echo "  --days N               测试持续天数 (默认: 3)"
      echo "  --interval N           检查间隔(秒) (默认: 60)"
      echo "  --mock-only            仅使用模拟数据，不连接Binance"
      echo "  --config FILE          使用指定的INI配置文件"
      echo "  --config-yaml FILE     使用指定的YAML配置文件"
      echo "  --env-file FILE        使用指定的.env环境变量文件"
      echo "  --symbols \"S1,S2\"      要测试的交易对，逗号分隔"
      echo "  --monitoring-port N    监控端口 (默认: 9090)"
      echo "  --no-preserve-logs     不保留完整历史日志"
      echo "  --help                 显示此帮助信息"
      exit 0
      ;;
    *)
      echo "未知选项: $1"
      exit 1
      ;;
  esac
done

# 构建命令行参数
ARGS=("--days" "$DAYS" "--interval" "$INTERVAL" "--monitoring-port" "$MONITORING_PORT")

# 添加可选参数
if [[ $MOCK_ONLY -eq 1 ]]; then
  ARGS+=("--mock-only")
fi

if [[ -n "$CONFIG_FILE" ]]; then
  ARGS+=("--config" "$CONFIG_FILE")
fi

if [[ -n "$CONFIG_YAML" ]]; then
  ARGS+=("--config-yaml" "$CONFIG_YAML")
fi

if [[ -n "$ENV_FILE" ]]; then
  ARGS+=("--env-file" "$ENV_FILE")
fi

if [[ -n "$SYMBOLS" ]]; then
  ARGS+=("--symbols" "$SYMBOLS")
fi

if [[ $PRESERVE_LOGS -eq 0 ]]; then
  ARGS+=("--no-preserve-logs")
fi

# 设置Python路径
PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export PYTHONPATH

# 输出当前设置
echo "启动稳定性测试:"
echo "- 持续时间: $DAYS 天"
echo "- 检查间隔: $INTERVAL 秒"
echo "- 日志目录: $LOG_DIR"
echo "- 保留完整日志: $([ "$PRESERVE_LOGS" -eq 1 ] && echo "是" || echo "否")"
echo "- 监控端口: $MONITORING_PORT"
if [[ -n "$SYMBOLS" ]]; then
  echo "- 交易对: $SYMBOLS"
fi
if [[ $MOCK_ONLY -eq 1 ]]; then
  echo "- 仅使用模拟数据"
fi

# 运行测试
echo "运行命令: python $SCRIPT_DIR/stability_test.py ${ARGS[@]} --log-dir $LOG_DIR"
python "$SCRIPT_DIR/stability_test.py" "${ARGS[@]}" --log-dir "$LOG_DIR"

# 检查运行结果
EXIT_CODE=$?
if [[ $EXIT_CODE -eq 0 ]]; then
  echo "稳定性测试成功完成"
else
  echo "稳定性测试失败或被中断，退出代码: $EXIT_CODE"
fi

# 创建日志归档
if [[ $EXIT_CODE -eq 0 && $PRESERVE_LOGS -eq 1 ]]; then
  ARCHIVE_NAME="stability_logs_$(date +%Y%m%d_%H%M%S).tar.gz"
  echo "创建日志归档: $ARCHIVE_NAME"
  tar -czf "$PROJECT_ROOT/logs/$ARCHIVE_NAME" -C "$PROJECT_ROOT/logs" "$(basename $LOG_DIR)"
  echo "日志归档已创建: $PROJECT_ROOT/logs/$ARCHIVE_NAME"
fi

exit $EXIT_CODE 