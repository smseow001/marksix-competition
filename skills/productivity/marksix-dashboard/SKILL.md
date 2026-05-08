---
description: 轻量 Web Dashboard 用于 Mark Six 双 Agent 竞争框架 — 实时计分板、KANBAN 看板、稳态方法展示。使用 Python 标准库，无须安装任何依赖。
triggers:
  - 启动 Mark Six 竞争框架的可视化面板
  - 查看 Alpha/Beta 双团队的实时比赛状态
  - 启动本地 Web 服务器展示竞争结果
  - 在 Termux/Android 环境中运行可视化面板
---

# 🏆 Mark Six 竞争框架 - Web Dashboard

## 快速启动

```bash
cd ~/.hermes/projects/M615042026-B/competition
python3 dashboard_server.py
```

然后在浏览器打开：**http://localhost:8080**

---

## 功能一览

| 区域 | 说明 |
|------|------|
| 🏆 目标 Banner | 目标 500 分，先到者胜 |
| 🔵 Alpha vs 🔴 Beta | 两侧卡片显示双方实时分数 + 进度条 |
| ⚔️ VS 中间区域 | 当前轮次 |
| 📊 最近轮次 | 最近 10 轮的比赛结果（需要 checkpoint 支持） |
| 🔮 稳态候选 | 双方都无法证伪的方法（潜在突破口） |
| 🎱 最新开奖 | 最近 5 期 Mark Six 结果 |
| 🔄 自动刷新 | 每 3 秒自动更新数据 |

---

## API 端点

```
GET /                     → Web 界面（深色主题 KANBAN 风格）
GET /api/health           → 健康检查
GET /api/scores           → 实时分数 + 最近轮次
GET /api/metastable       → 稳态候选方法
GET /api/latest           → 最近 10 期开奖
```

---

## 依赖

**零外部依赖** — 使用 Python 3 标准库：
- `http.server` — HTTP 服务器
- `json` — 数据读写
- `datetime` — 时间戳
- `html` — HTML 转义

---

## 文件结构

```
competition/
├── dashboard_server.py      # 主服务器（单文件，约 800 行）
├── checkpoints/             # 每轮存档（自动创建）
├── competition_scores_v5.json   # 分数数据
└── metastable_candidates.json   # 稳态候选方法
```

---

## 开机自启（Termux）

```bash
# 方法 1: 用 cron 定时检查
*/5 * * * * pgrep -f dashboard_server.py || cd ~/.hermes/projects/M615042026-B/competition && python3 dashboard_server.py &

# 方法 2: Termux Boot（需要 termux-boot 包）
# 在 ~/.termux/boot/ 创建脚本启动 Dashboard
```

---

## 端口说明

- 默认端口：**8080**
- 绑定地址：**0.0.0.0**（局域网可访问）
- 如果端口被占用，修改 `dashboard_server.py` 第 18 行：
  ```python
  PORT = 8080  # 改成其他端口如 9090
  ```

---

## 在局域网其他设备访问

手机 IP 假设是 `192.168.1.100`，在同局域网电脑浏览器输入：

```
http://192.168.1.100:8080
```

查手机 IP：
```bash
ip addr show wlan0 | grep inet
```

---

## 数据来源

- **分数**：`competition_scores_v5.json`
- **Metastable**：`metastable_candidates.json`
- **开奖数据**：`data/marksix/hkjc_marksix.csv`

---

## 已知限制

1. **无 SSE 实时推送** — 使用轮询（3 秒），非真正 WebSocket
2. **手机休眠会断连** — 需要守护脚本维持运行
3. **无认证** — 局域网内任何人可访问（勿放公网）

---

## 扩展建议

1. **加入 /api/run_round** — 从 Dashboard 触发新的一轮比赛
2. **加入 /api/agent_status** — 显示 Agent 心跳是否存活
3. **加入图表** — 用 matplotlib 生成历史分数折线图
4. **加入通知** — 有人连进来时用 termux-notification 提醒
5. **HTTPS 支持** — 用 self-signed 证书从公网访问
