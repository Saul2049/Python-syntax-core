# 🔖 项目阶段详细需求文档

> **版本**: v1.0 | 2025‑05‑25 | 维护人: o3
>
> 本文档汇总了从 0‑→1 到 v5.0.0 的五大阶段（①‑⑤）及 Memory‑M 系列（W1‑W5）的全部可执行需求、里程碑与验收标准，作为后续迭代的唯一权威基线。

---

## ① 监控与分析（原阶段 5）

### 🎯 目的

* 在任何重构/性能优化之前，先建立 **可观测性闭环**：实时指标 → 告警 → Runbook → 回滚。

### 📦 关键交付物

| 序号   | 交付物                    | 描述                            |
| ---- | ---------------------- | ----------------------------- |
| M1‑1 | `metrics_collector.py` | 统一指标汇总 SDK（Prometheus format） |
| M1‑2 | Grafana Dashboard      | Memory/CPU/Latency/GC/FD 五板块  |
| M1‑3 | Alertmanager Rules     | P95 延迟、RSS、FD、异常数、多级告警        |
| M1‑4 | Runbook v1             | P0/P1/P2 故障流程；自动 rollback 脚本  |
| M1‑5 | `health_check.py`      | 一键本地/CI 健康扫描                  |

### ✅ 验收标准

* 覆盖 ≥ 90 % 关键路径指标（见 **KPI 列表**）。
* Grafana 图在 5 s 内刷新；Pushgateway 延迟 < 1 s。
* Alertmanager 能通过 Telegram 通道在 10 s 内送达。
* Runbook 演练通过 3 个 P0 场景（WS 中断、内存泄漏、订单异常）。

### 🚦 退出准则

> 指标可见、告警闭环、Runbook 完整。通过后方可进入阶段 ②。

---

## ② 用户 / 开发体验

### 🎯 目的

* 让任何新同学 "clone → `make dev` → `pytest -q`" < 2 min 跑通。

### 📦 交付物

| Sprint | 交付物                                | 说明                                    |
| ------ | ---------------------------------- | ------------------------------------- |
| S‑0    | `Makefile` ➝ `make dev`            | 创建 venv + 安装 `[dev]` + pre‑commit     |
| S‑1    | `.env.example` + `setup_config.py` | 交互式生成本地配置；30 s 内完成                    |
| S‑2    | `pre‑commit` 链                     | ruff, black, isort, commit‑lint       |
| S‑3    | README Quick‑Start（GIF）            | 30 分钟跑通示例 /zh + /en                   |
| S‑4    | CLI Wrapper (`trade.cli`)          | `backtest`, `optimize`, `run-live` 命令 |
| S‑5    | MkDocs Docs site                   | GH Pages 自动部署，搜索、版本切换                 |

### ✅ 验收标准

* `pre‑commit` 钩子 100 % 通过且 < 5 s。
* Quick‑Start 新人测试（3 人）成功率 100 %。
* CLI 命令帮助 `--help` 覆盖率 100 %。

---

## ③ 代码现代化 & 技术债

### 🎯 目的

* 清理所有 FutureWarning，补充类型注解，确保 pandas ≥ 2.x 完整支持。

### 📦 交付物

| 巡检项           | 目标             | 实现                             |
| ------------- | -------------- | ------------------------------ |
| Type Hints    | 核心模块 100 %     | `src/broker.py`, `signals.py`… |
| FutureWarning | = 0            | full‑ffill, concat 替换 append   |
| pre‑commit 强检 | ruff E/F/W 全通过 | ——                             |

### ✅ 验收

* `pytest -q` 0 warning。
* `mypy --strict src/` error = 0。
* CI `codespell`、`bandit` 全绿。

---

## ④ 性能优化

### 🎯 目标

* 单线程 CPU‑bound 算法全部向量化；异步 IO 并发吞吐 ≥ 100 signals/s；P95 信号延迟 ≤ 6 ms。

### 📦 子阶段

| 子阶段 | 关键成果                                   |
| --- | -------------------------------------- |
| M3  | 算法向量化（ewm, numba optional）             |
| M4  | I/O 并发优化（aiohttp + WebSocket + uvloop） |
| M5  | 内存\&GC 优化（W1‑W5，见下）                    |

### ✅ 验收

* `signal_latency_seconds_p95` ≤ 6 ms（真实频率）。
* `cpu_utilization` ≤ 70 %（R‑pi 4 4G 限制）。

---

## ⑤ 工具链升级

### 🎯 目的

* CI/CD、依赖安全、自动发布一次到位。

### 📦 交付

| 模块         | 需求                                         |
| ---------- | ------------------------------------------ |
| CI Matrix  | Py 3.9 / 3.10 / 3.11 全部 pytest 通过          |
| Dependabot | `weekly` PR + CI perf guard                |
| SCA        | `pip‑audit`, `safety` 在 CI enforced        |
| Release    | `gh release create`+Docker build+GHCR push |

---

## Memory‑M 子阶段（W1‑W5）

| 周          | 目标          | 指标                                           | 状态基线             |
| ---------- | ----------- | -------------------------------------------- | ---------------- |
| **W1**     | 零分配缓存 & 滑窗  | 分配率 ↓ ≥ 20 %<br>RSS 增长 < 5 MB                | ✔ snapshot v1    |
| **W2**     | GC 阈值 & 冻结  | Gen0 ≤ 200/min<br>P95 GC 暂停 ≤ 5 ms           | ✔ (900,20,10)    |
| **W3**     | 泄漏哨兵 6 h    | rss / fd 增长率 < 0.1/min                       | ✔ leak\_report 0 |
| **W4**     | 24 h 真负载    | RSS ≤ 40 MB                                  | 🔄 运行中           |
| P95 ≤ 6 ms | ✅ 3.10ms 达标 |                                              |                  |
| **W5**     | 72 h Canary | latency\_ratio < 1.2<br>panic\_sell\_total=0 | 待启动              |

---

### 📌 版本里程碑

| Tag           | 组成                | 条件                |
| ------------- | ----------------- | ----------------- |
| **v4.0.0**    | M4‑异步架构 + M1 监控   | P95 ≤ 6 ms（实验）    |
| **v5.0.0‑rc** | W1‑W4 全绿          | CI + perf‑guard 绿 |
| **v5.0.0**    | W5 Canary 72 h 通过 | 主网灰度就绪            |

---

> **后续维护**：
>
> * 本文档放置于 `docs/PROJECT_PHASES.md`，任何阶段需求或指标变更请通过 PR 修改并更新版本号。 