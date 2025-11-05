#!/bin/bash

# AI-Alpha-Trader Docker Startup Script
# 这个脚本帮助你快速启动整个AI交易系统

set -e

echo "🚀 AI-Alpha-Trader Docker 启动脚本"
echo "=================================="

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在"
    echo "📋 正在从 .env.example 创建 .env 文件..."
    cp .env.example .env
    echo "✅ .env 文件已创建"
    echo ""
    echo "⚠️  重要：请编辑 .env 文件并填入你的API密钥！"
    echo "   需要配置的密钥："
    echo "   - OPENAI_API_KEY (必需)"
    echo "   - JINA_API_KEY (可选，用于市场信息搜索)"
    echo "   - ALPHAADVANTAGE_API_KEY (可选，已有本地数据)"
    echo ""
    read -p "是否现在编辑.env文件？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    else
        echo "⚠️  请稍后手动编辑 .env 文件"
        echo "   运行: nano .env 或 vim .env"
        exit 1
    fi
fi

# 检查runtime_env.json是否存在
if [ ! -f runtime_env.json ]; then
    echo "📝 创建 runtime_env.json..."
    cat > runtime_env.json << EOF
{
  "SIGNATURE": "",
  "TODAY_DATE": "",
  "IF_TRADE": false
}
EOF
    echo "✅ runtime_env.json 已创建"
fi

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装！请先安装 Docker"
    echo "   访问: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装！请先安装 Docker Compose"
    exit 1
fi

# 选择Docker Compose命令
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ Docker Compose 未找到！"
    exit 1
fi

echo ""
echo "🔨 构建 Docker 镜像..."
$DOCKER_COMPOSE build

echo ""
echo "🚀 启动服务..."
echo "   - MCP Math Service (端口 8000)"
echo "   - MCP Search Service (端口 8001)"
echo "   - MCP Trade Service (端口 8002)"
echo "   - MCP Price Service (端口 8003)"
echo "   - AI Trader 主程序"
echo ""

$DOCKER_COMPOSE up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

echo ""
echo "🔍 检查服务状态..."
$DOCKER_COMPOSE ps

echo ""
echo "✅ 服务已启动！"
echo ""
echo "📊 查看日志："
echo "   所有服务: docker-compose logs -f"
echo "   主程序: docker-compose logs -f ai-trader"
echo "   MCP服务: docker-compose logs -f mcp-math mcp-search mcp-trade mcp-price"
echo ""
echo "🛑 停止服务："
echo "   docker-compose down"
echo ""
echo "📁 数据位置："
echo "   交易记录: ./data/agent_data/"
echo "   日志文件: ./logs/"
echo ""
