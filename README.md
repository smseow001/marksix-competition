# 🏆 Mark Six 预测冠军赛

> M615042026-B 项目核心框架 — 双 Agent 对抗式学习系统

## 项目概述

两个 AI Agent（Alpha vs Beta）在真实 Mark Six 数据上进行预测比赛，先累积 **500 分**者获胜。

- **Alpha（Explorer）**：创新驱动，不断探索新预测方法
- **Beta（Critic）**：证伪驱动，验证并否定 Alpha 的方法

## 快速启动

```bash
# 启动 Web Dashboard
cd competition
python3 dashboard_server.py
# 浏览器打开 http://localhost:9090
```

## 核心文件

| 文件 | 说明 |
|------|------|
| `dashboard_server.py` | 轻量 Web Dashboard（Python 标准库，零依赖） |
| `AGENTS_V5.md` | 双 Agent 框架设计文档 |
| `collect_data.py` | Mark Six 数据抓取脚本 |

## 架构

```
┌─────────────────────────────────────┐
│     Mark Six 预测冠军赛             │
├─────────────┬──────────────────────┤
│  🔵 Alpha   │    🔴 Beta           │
│  Explorer   │    Critic           │
│  创新驱动   │    证伪驱动          │
├─────────────┴──────────────────────┤
│     ⚖️ 仲裁（Arbitrator）          │
│  无法证伪 = 稳态候选方法           │
├────────────────────────────────────┤
│     📊 Web Dashboard (端口 8080)   │
└────────────────────────────────────┘
```

## 计分规则

| 命中 | 得分 |
|------|------|
| 6/6 | +200 |
| 5/6 | +50 |
| 4/6 | +20 |
| 3/6 | +5 |
| 2/6 | +2 |
| 1/6 | -2 |
| 0/6 | -10 |

## 技术栈

- **Hermes Agent** — AI Agent 框架
- **Python 3** — 标准库（无外部依赖）
- **Mark Six 数据** — nfd.com.tw

## 项目背景

M615042026-B — 随机预测方法论研究

**核心理念**： Never say 不存在可供预测随机

---

*Powered by Hermes Agent · M615042026-B*
