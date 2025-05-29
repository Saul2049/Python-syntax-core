# 🌅 明早查看指南 (2025-05-25)

## 📊 **快速状态检查**
```bash
# 1️⃣ 立即查看当前状态
python scripts/status_check.py

# 2️⃣ 查看过夜监控日志
cat overnight_log.txt | tail -50

# 3️⃣ 检查进程是否还在运行
ps aux | grep -E "(W3-Production|W4-24h-real|overnight_monitor)" | grep -v grep
```

## 📺 **连接监控会话**
```bash
# 连接到 W4 压力测试日志 (替代 tmux a -t stress)
screen -r stress

# 如果需要退出 screen，按: Ctrl+A, 然后按 D

# 直接查看最新日志
tail -f logs/w4_stress_W4-24h-real.log
```

## 🔍 **详细检查命令**
```bash
# W3 状态详情
cat output/w3_sentinel_status_W3-Production.json | jq '.'

# W4 状态详情  
cat output/w4_stress_status_W4-24h-real.json | jq '.'

# 检查防睡眠是否还在工作
ps aux | grep caffeinate | grep -v grep
```

## 🎯 **预期明早状态 (7AM-12PM)**
- **W3 泄漏哨兵**: ✅ 已完成 (6小时目标 @ ~5AM)
- **W4 压力测试**: 🔄 运行中 (~8-13小时，~1200-2000条信号)
- **过夜监控**: 📝 记录了整夜状态
- **防睡眠保护**: 🛡️ 持续至下午12点 (12小时保护)

## 🚨 **如果有问题**
```bash
# 重启崩溃的测试
make w3-start-tagged run_name=W3-Production-recovery hours=6 &
python scripts/memory/mem_stress_test.py --run-name W4-recovery --signals 20000 --duration 24h --max-rss 40 &

# 查看错误日志
ls logs/ | grep -E "(error|crash|exception)"
```

## 📈 **Grafana Dashboard**
如果想看图表，在浏览器中打开本地 Grafana (如果配置了的话)，或查看 `output/` 目录下的监控数据文件。

---
**💤 睡前状态**: 所有系统正常，防睡眠已启用12小时 (至中午12点)，过夜监控每小时记录状态 