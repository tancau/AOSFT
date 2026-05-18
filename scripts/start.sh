#!/bin/bash
set -e

echo "=== AOSFT-MVP 启动脚本 ==="

if [ ! -f .env ]; then
    echo "警告: .env文件不存在，从模板创建"
    cp .env.example .env
    echo "请编辑.env文件配置API密钥后重新运行"
    exit 1
fi

if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "使用Docker启动..."
    docker-compose up -d --build
    echo "服务已启动，查看日志: docker-compose logs -f"
else
    echo "Docker未安装，使用直接方式启动..."
    
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    if [ ! -f "data/aosft.db" ]; then
        echo "初始化数据库..."
        python3 scripts/init_db.py
    fi
    
    echo "启动AOSFT-MVP..."
    python3 main.py
fi
