#!/usr/bin/env python3
"""
Mark Six 竞争框架 - Web Dashboard 服务器
使用 Python 标准库 http.server，无须额外安装依赖

启动: python3 dashboard_server.py
访问: http://localhost:8080
"""

import json
import os
import time
import signal
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import html
import sys

# ============ 配置 ============
PORT = 9090
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录
SCORES_FILE = os.path.join(BASE_DIR, "competition", "competition_scores_v5.json")
METASTABLE_FILE = os.path.join(BASE_DIR, "competition", "metastable_candidates.json")
DATA_DIR = os.path.join(BASE_DIR, "data")

# ============ 工具函数 ============

def load_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def get_scores():
    return load_json(SCORES_FILE, {"alpha_total": 0, "beta_total": 0, "rounds": 0, "winner": None})

def get_metastable():
    return load_json(METASTABLE_FILE, {"metastable_candidates": []})

def get_latest_data():
    """读取最新的历史数据"""
    csv_path = os.path.join(DATA_DIR, "marksix", "hkjc_marksix.csv")
    draws = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines[1:]:  # 跳过表头
            parts = line.strip().split(',')
            if len(parts) >= 7:
                # 格式: Draw,Date,N1,N2,N3,N4,N5,N6,Extra
                # 日期格式: 2026-05/07
                draw_no = parts[0].strip()
                date = parts[1].strip().replace('/', '-')  # 2026-05/07 → 2026-05-07
                numbers = [p.strip() for p in parts[2:8]]
                draws.append({
                    "draw_no": draw_no,
                    "date": date,
                    "numbers": numbers
                })
        draws.reverse()  # 最新的在前
    except Exception as e:
        print(f"[ERROR] get_latest_data: {e}")
    return draws

def get_recent_rounds():
    """读取最近的回合记录"""
    checkpoints_dir = os.path.join(BASE_DIR, "checkpoints")
    rounds = []
    if os.path.exists(checkpoints_dir):
        for d in os.listdir(checkpoints_dir):
            if d.startswith("round_"):
                round_file = os.path.join(checkpoints_dir, d)
                data = load_json(round_file)
                if data:
                    rounds.append(data)
    rounds.sort(key=lambda x: x.get('round', 0), reverse=True)
    return rounds[:10]  # 最近10轮

# ============ HTML 模板 ============

DARK_THEME = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏆 Mark Six 预测冠军赛 - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a25;
            --border: #2a2a3a;
            --text-primary: #e8e8f0;
            --text-secondary: #8888a0;
            --alpha-color: #3b82f6;
            --alpha-glow: #3b82f680;
            --beta-color: #ef4444;
            --beta-glow: #ef444480;
            --accent: #f59e0b;
            --success: #22c55e;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* 粒子背景 */
        .bg-particles {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            overflow: hidden;
            z-index: 0;
        }
        .particle {
            position: absolute;
            width: 2px; height: 2px;
            background: var(--accent);
            border-radius: 50%;
            opacity: 0.3;
            animation: float 15s infinite;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); opacity: 0.3; }
            50% { transform: translateY(-100px) translateX(50px); opacity: 0.1; }
        }
        
        .container {
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* 顶部标题 */
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }
        header h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--alpha-color), var(--accent), var(--beta-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }
        header .subtitle {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        header .last-update {
            color: var(--accent);
            font-size: 0.8rem;
            margin-top: 4px;
        }
        
        /* 目标 Banner */
        .goal-banner {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
        }
        .goal-banner .target {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--accent);
            text-shadow: 0 0 30px var(--accent);
        }
        .goal-banner .label {
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-top: 4px;
        }
        
        /* Kanban 看板 */
        .kanban {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 20px;
            margin-bottom: 30px;
            align-items: start;
        }
        
        .agent-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            position: relative;
            overflow: hidden;
        }
        .agent-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
        }
        .alpha-card::before { background: var(--alpha-color); }
        .beta-card::before { background: var(--beta-color); }
        
        .agent-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }
        .agent-avatar {
            width: 48px; height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
        }
        .alpha-card .agent-avatar { background: var(--alpha-color); }
        .beta-card .agent-avatar { background: var(--beta-color); }
        
        .agent-info h2 {
            font-size: 1.3rem;
            font-weight: 700;
        }
        .agent-info .role {
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
        
        .score-display {
            text-align: center;
            padding: 20px 0;
        }
        .score-number {
            font-size: 4rem;
            font-weight: 900;
            line-height: 1;
        }
        .alpha-card .score-number { color: var(--alpha-color); }
        .beta-card .score-number { color: var(--beta-color); }
        .score-label {
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-top: 8px;
        }
        
        .progress-bar {
            background: var(--bg-primary);
            border-radius: 8px;
            height: 12px;
            margin-top: 20px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            border-radius: 8px;
            transition: width 0.5s ease;
        }
        .alpha-card .progress-fill { background: var(--alpha-color); }
        .beta-card .progress-fill { background: var(--beta-color); }
        
        .agent-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 20px;
        }
        .stat-box {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        .stat-value {
            font-size: 1.4rem;
            font-weight: 700;
        }
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.75rem;
            margin-top: 4px;
        }
        
        /* VS 中间区域 */
        .vs-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .vs-badge {
            width: 60px; height: 60px;
            background: linear-gradient(135deg, var(--alpha-color), var(--beta-color));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: 900;
            margin-bottom: 20px;
        }
        .round-info {
            text-align: center;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 20px;
        }
        .round-label {
            color: var(--text-secondary);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .round-number {
            font-size: 2rem;
            font-weight: 800;
            color: var(--accent);
        }
        
        /* 最近记录 */
        .recent-section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .rounds-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .round-item {
            display: grid;
            grid-template-columns: 60px 1fr 1fr 80px;
            gap: 16px;
            align-items: center;
            padding: 12px;
            background: var(--bg-primary);
            border-radius: 8px;
        }
        .round-item .round-num {
            font-weight: 700;
            color: var(--text-secondary);
        }
        .round-item .alpha-result {
            color: var(--alpha-color);
        }
        .round-item .beta-result {
            color: var(--beta-color);
        }
        .round-item .delta {
            text-align: right;
            font-weight: 600;
        }
        .delta.positive { color: var(--success); }
        .delta.negative { color: var(--beta-color); }
        
        /* Metastable 发现 */
        .metastable-section {
            background: var(--bg-card);
            border: 1px solid var(--accent);
            border-radius: 16px;
            padding: 24px;
        }
        .metastable-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }
        .metastable-item {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
        }
        .metastable-item .method {
            font-weight: 700;
            color: var(--accent);
            font-size: 0.9rem;
        }
        .metastable-item .evidence {
            color: var(--text-secondary);
            font-size: 0.75rem;
            margin-top: 6px;
        }
        .empty-state {
            text-align: center;
            color: var(--text-secondary);
            padding: 30px;
            font-style: italic;
        }
        
        /* 最新数据 */
        .latest-section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
        }
        .draw-item {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px;
            background: var(--bg-primary);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        .draw-item:last-child { margin-bottom: 0; }
        .draw-no {
            font-weight: 700;
            color: var(--accent);
            min-width: 60px;
        }
        .draw-date {
            color: var(--text-secondary);
            font-size: 0.85rem;
            min-width: 100px;
        }
        .draw-numbers {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        .draw-numbers span {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 4px 8px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        
        /* Footer */
        footer {
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.8rem;
            border-top: 1px solid var(--border);
            margin-top: 30px;
        }
        
        /* 响应式 */
        @media (max-width: 768px) {
            .kanban {
                grid-template-columns: 1fr;
            }
            .vs-section {
                order: -1;
                padding: 10px;
            }
            .round-item {
                grid-template-columns: 50px 1fr 1fr;
            }
            .round-item .delta {
                grid-column: 1 / -1;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="bg-particles" id="particles"></div>
    
    <div class="container">
        <header>
            <h1>🏆 Mark Six 预测冠军赛</h1>
            <div class="subtitle">Generative Adversarial Discovery Framework</div>
            <div class="last-update" id="lastUpdate">最后更新: --</div>
        </header>
        
        <div class="goal-banner">
            <div class="target" id="winScore">500</div>
            <div class="label">目标分数 · 先到者胜</div>
        </div>
        
        <!-- Kanban 看板 -->
        <div class="kanban">
            <!-- Alpha 卡片 -->
            <div class="agent-card alpha-card">
                <div class="agent-header">
                    <div class="agent-avatar">🔵</div>
                    <div class="agent-info">
                        <h2>Alpha</h2>
                        <div class="role">Explorer · 创新驱动</div>
                    </div>
                </div>
                <div class="score-display">
                    <div class="score-number" id="alphaScore">0</div>
                    <div class="score-label">当前总分</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="alphaProgress" style="width: 0%"></div>
                </div>
                <div class="agent-stats">
                    <div class="stat-box">
                        <div class="stat-value" id="alphaRounds">0</div>
                        <div class="stat-label">已完成轮次</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" id="alphaHits">0</div>
                        <div class="stat-label">预测命中</div>
                    </div>
                </div>
            </div>
            
            <!-- VS 中间 -->
            <div class="vs-section">
                <div class="vs-badge">VS</div>
                <div class="round-info">
                    <div class="round-label">当前轮次</div>
                    <div class="round-number" id="currentRound">0</div>
                </div>
            </div>
            
            <!-- Beta 卡片 -->
            <div class="agent-card beta-card">
                <div class="agent-header">
                    <div class="agent-avatar">🔴</div>
                    <div class="agent-info">
                        <h2>Beta</h2>
                        <div class="role">Critic · 证伪驱动</div>
                    </div>
                </div>
                <div class="score-display">
                    <div class="score-number" id="betaScore">0</div>
                    <div class="score-label">当前总分</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="betaProgress" style="width: 0%"></div>
                </div>
                <div class="agent-stats">
                    <div class="stat-box">
                        <div class="stat-value" id="betaRounds">0</div>
                        <div class="stat-label">已完成轮次</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" id="betaHits">0</div>
                        <div class="stat-label">预测命中</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 最近轮次记录 -->
        <div class="recent-section">
            <div class="section-title">📊 最近轮次</div>
            <div class="rounds-list" id="roundsList">
                <div class="empty-state">暂无记录，开始比赛后会自动显示</div>
            </div>
        </div>
        
        <!-- Metastable 发现 -->
        <div class="metastable-section">
            <div class="section-title">🔮 稳态候选方法 (Metastable Candidates)</div>
            <div class="metastable-grid" id="metastableList">
                <div class="empty-state">暂无敌我双方都无法证伪的方法</div>
            </div>
        </div>
        
        <!-- 最新开奖 -->
        <div class="latest-section" style="margin-top: 30px;">
            <div class="section-title">🎱 最新开奖 (Mark Six)</div>
            <div id="latestDraws">
                <div class="empty-state">加载中...</div>
            </div>
        </div>
        
        <footer>
            M615042026-B · Generative Adversarial Discovery Framework · Powered by Hermes Agent
        </footer>
    </div>
    
    <script>
        // 粒子效果
        function createParticles() {
            const container = document.getElementById('particles');
            for (let i = 0; i < 30; i++) {
                const p = document.createElement('div');
                p.className = 'particle';
                p.style.left = Math.random() * 100 + '%';
                p.style.top = Math.random() * 100 + '%';
                p.style.animationDelay = Math.random() * 15 + 's';
                p.style.animationDuration = (10 + Math.random() * 10) + 's';
                container.appendChild(p);
            }
        }
        createParticles();
        
        // 加载数据
        let WIN_SCORE = 500;
        
        async function loadData() {
            try {
                const [scoresRes, metastableRes, latestRes] = await Promise.all([
                    fetch('/api/scores'),
                    fetch('/api/metastable'),
                    fetch('/api/latest')
                ]);
                
                const scores = await scoresRes.json();
                const metastable = await metastableRes.json();
                const latest = await latestRes.json();
                
                // 更新分数
                document.getElementById('alphaScore').textContent = scores.alpha_total || 0;
                document.getElementById('betaScore').textContent = scores.beta_total || 0;
                document.getElementById('currentRound').textContent = scores.rounds || 0;
                
                // 更新进度条
                const alphaPct = Math.min(100, ((scores.alpha_total || 0) / WIN_SCORE) * 100);
                const betaPct = Math.min(100, ((scores.beta_total || 0) / WIN_SCORE) * 100);
                document.getElementById('alphaProgress').style.width = alphaPct + '%';
                document.getElementById('betaProgress').style.width = betaPct + '%';
                
                // 更新轮次
                document.getElementById('alphaRounds').textContent = scores.alpha_rounds || 0;
                document.getElementById('betaRounds').textContent = scores.beta_rounds || 0;
                document.getElementById('alphaHits').textContent = scores.alpha_hits || 0;
                document.getElementById('betaHits').textContent = scores.beta_hits || 0;
                
                // 更新时间
                document.getElementById('lastUpdate').textContent = '最后更新: ' + new Date().toLocaleTimeString('zh-CN');
                
                // 更新最近轮次
                const rounds = scores.recent_rounds || [];
                const roundsList = document.getElementById('roundsList');
                if (rounds.length === 0) {
                    roundsList.innerHTML = '<div class="empty-state">暂无记录，开始比赛后会自动显示</div>';
                } else {
                    roundsList.innerHTML = rounds.map(r => {
                        const delta = (r.alpha_delta || 0) - (r.beta_delta || 0);
                        const deltaClass = delta >= 0 ? 'positive' : 'negative';
                        return '<div class="round-item">' +
                            '<div class="round-num">#' + r.round + '</div>' +
                            '<div class="alpha-result">α: ' + (r.alpha_score > 0 ? '+' : '') + r.alpha_score + '</div>' +
                            '<div class="beta-result">β: ' + (r.beta_score > 0 ? '+' : '') + r.beta_score + '</div>' +
                            '<div class="delta ' + deltaClass + '">Δ ' + (delta > 0 ? '+' : '') + delta + '</div>' +
                        '</div>';
                    }).join('');
                }
                
                // 更新 Metastable
                const msList = document.getElementById('metastableList');
                const candidates = metastable.metastable_candidates || [];
                if (candidates.length === 0) {
                    msList.innerHTML = '<div class="empty-state">暂无敌我双方都无法证伪的方法</div>';
                } else {
                    msList.innerHTML = candidates.map(c => 
                        '<div class="metastable-item">' +
                            '<div class="method">⚡ ' + (c.method || 'Unknown') + '</div>' +
                            '<div class="evidence">' + (c.evidence || '') + '</div>' +
                        '</div>'
                    ).join('');
                }
                
                // 更新最新开奖
                const latestDiv = document.getElementById('latestDraws');
                if (latest.draws && latest.draws.length > 0) {
                    latestDiv.innerHTML = latest.draws.slice(0, 5).map(d => 
                        '<div class="draw-item">' +
                            '<div class="draw-no">' + d.draw_no + '</div>' +
                            '<div class="draw-date">' + d.date + '</div>' +
                            '<div class="draw-numbers">' +
                                d.numbers.map(n => '<span>' + n + '</span>').join('') +
                            '</div>' +
                        '</div>'
                    ).join('');
                }
                
                // 检查胜者
                if (scores.winner) {
                    document.querySelector('.goal-banner .target').textContent = 
                        '🏆 ' + scores.winner + ' WIN!';
                }
                
            } catch (e) {
                console.error('加载数据失败:', e);
            }
        }
        
        // 每 3 秒自动刷新
        loadData();
        setInterval(loadData, 3000);
    </script>
</body>
</html>
"""

# ============ HTTP 请求处理 ============

class DashboardHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(DARK_THEME.encode('utf-8'))
        
        elif path == '/api/scores':
            scores = get_scores()
            recent = get_recent_rounds()
            scores['recent_rounds'] = recent
            
            # 计算统计
            alpha_hits = sum(1 for r in recent if r.get('alpha_score', 0) >= 2)
            beta_hits = sum(1 for r in recent if r.get('beta_score', 0) >= 2)
            scores['alpha_hits'] = alpha_hits
            scores['beta_hits'] = beta_hits
            scores['alpha_rounds'] = len(recent)
            scores['beta_rounds'] = len(recent)
            
            response = json.dumps(scores, ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        
        elif path == '/api/metastable':
            ms = get_metastable()
            response = json.dumps(ms, ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        
        elif path == '/api/latest':
            draws = get_latest_data()
            response = json.dumps({'draws': draws[:10]}, ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        
        elif path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'time': time.time()}).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('404 Not Found'.encode('utf-8'))

# ============ 主程序 ============

class QuietHTTPHandler(DashboardHandler):
    """静默日志，不输出每次请求"""
    def log_message(self, format, *args):
        pass  # 静默

def main():
    # 信号处理：优雅退出
    def signal_handler(sig, frame):
        print("\n收到退出信号，关闭服务器...")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server = HTTPServer(('0.0.0.0', PORT), QuietHTTPHandler)
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     🏆 Mark Six 竞争框架 - Web Dashboard                  ║
╠══════════════════════════════════════════════════════════╣
║  状态:    ✅ 运行中                                       ║
║  端口:    {PORT}                                              ║
║  访问:    http://localhost:{PORT}                          ║
║  目标:    先到 500 分者获胜                               ║
╠══════════════════════════════════════════════════════════╣
║  📌 在手机浏览器打开:                                     ║
║     1. 打开 Chrome/Firefox                               ║
║     2. 输入 http://localhost:{PORT}                       ║
║                                                          ║
║  📌 或者用 Termux API:                                   ║
║     termux-open-url http://localhost:{PORT}             ║
╠══════════════════════════════════════════════════════════╣
║  按 Ctrl+C 停止服务器                                    ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()

if __name__ == '__main__':
    main()
