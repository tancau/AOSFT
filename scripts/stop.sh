#!/bin/bash
set -e

echo "=== AOSFT-MVP 停止脚本 ==="

if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
    if docker-compose ps -q 2>/dev/null | grep -q .; then
        echo "停止Docker服务..."
        docker-compose down
        echo "服务已停止"
    else
        echo "Docker服务未运行"
    fi
else
    PID=$(pgrep -f "python3 main.py" 2>/dev/null || true)
    if [ -n "$PID" ]; then
        echo "停止进程: $PID"
        kill $PID
        echo "服务已停止"
    else
        echo "服务未运行"
    fi
fi
