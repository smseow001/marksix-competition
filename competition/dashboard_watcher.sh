#!/bin/bash
# Dashboard 守护脚本 - 每分钟检查一次，如果没在跑就重启
while true; do
    if ! pgrep -f "dashboard_server.py" > /dev/null 2>&1; then
        echo "[$(date)] Dashboard 重启中..."
        cd /data/data/com.termux/files/home/.hermes/projects/M615042026-B/competition
        python3 dashboard_server.py &
    fi
    sleep 60
done
