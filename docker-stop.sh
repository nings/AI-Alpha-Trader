#!/bin/bash

# AI-Alpha-Trader Docker 停止脚本

set -e

echo "🛑 停止 AI-Alpha-Trader 服务..."

# 选择Docker Compose命令
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ Docker Compose 未找到！"
    exit 1
fi

# 停止并移除容器
$DOCKER_COMPOSE down

echo "✅ 所有服务已停止"
echo ""
echo "📊 如需查看交易结果："
echo "   ls -la ./data/agent_data/"
echo ""
echo "🔄 重新启动："
echo "   ./docker-start.sh"
echo ""
