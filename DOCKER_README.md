# 🐳 AI-Alpha-Trader Docker 部署指南

本指南将帮助你使用 Docker 快速部署和运行 AI-Alpha-Trader 系统。

---

## 📋 目录

1. [前置要求](#前置要求)
2. [快速开始](#快速开始)
3. [详细说明](#详细说明)
4. [服务架构](#服务架构)
5. [配置说明](#配置说明)
6. [常用命令](#常用命令)
7. [故障排查](#故障排查)

---

## 前置要求

### 必需软件

- **Docker** (版本 20.10+)
  - Mac: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
  - Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
  - Linux: [Docker Engine](https://docs.docker.com/engine/install/)

- **Docker Compose** (通常包含在 Docker Desktop 中)
  - 验证安装: `docker-compose --version` 或 `docker compose version`

### API 密钥

- **OPENAI_API_KEY** (必需) - 用于 AI 模型
- **JINA_API_KEY** (可选) - 用于市场信息搜索
- **ALPHAADVANTAGE_API_KEY** (可选) - 项目已包含本地数据

---

## 快速开始

### 方式一：使用启动脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/HKUDS/AI-Trader.git
cd AI-Trader

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
nano .env  # 或使用其他编辑器

# 3. 一键启动
./docker-start.sh
```

### 方式二：手动启动

```bash
# 1. 创建环境配置
cp .env.example .env
nano .env  # 填入API密钥

# 2. 创建运行时配置文件
cat > runtime_env.json << EOF
{
  "SIGNATURE": "",
  "TODAY_DATE": "",
  "IF_TRADE": false
}
EOF

# 3. 构建镜像
docker-compose build

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f
```

---

## 详细说明

### 第一步：环境配置

创建 `.env` 文件并配置 API 密钥：

```bash
# AI Model API Configuration
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-openai-key-here

# Data Source Configuration (可选)
JINA_API_KEY=your-jina-key-here
ALPHAADVANTAGE_API_KEY=your-alpha-vantage-key-here

# MCP Service Ports (默认值，通常不需要修改)
MATH_HTTP_PORT=8000
SEARCH_HTTP_PORT=8001
TRADE_HTTP_PORT=8002
GETPRICE_HTTP_PORT=8003

# Agent Configuration
AGENT_MAX_STEP=30
```

### 第二步：构建和启动

```bash
# 构建 Docker 镜像
docker-compose build

# 后台启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f
```

---

## 服务架构

Docker Compose 会启动以下服务：

```
┌─────────────────────────────────────────┐
│          AI-Trader 系统架构              │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   ai-trader (主程序)              │  │
│  │   - 运行 main.py                  │  │
│  │   - 协调所有 AI 模型               │  │
│  └──────────────────────────────────┘  │
│                 ↓                       │
│  ┌──────────────────────────────────┐  │
│  │   MCP 工具服务层                  │  │
│  ├──────────────────────────────────┤  │
│  │  mcp-math     (端口 8000)        │  │
│  │  - 数学计算                       │  │
│  ├──────────────────────────────────┤  │
│  │  mcp-search   (端口 8001)        │  │
│  │  - 市场信息搜索                   │  │
│  ├──────────────────────────────────┤  │
│  │  mcp-trade    (端口 8002)        │  │
│  │  - 买卖股票交易                   │  │
│  ├──────────────────────────────────┤  │
│  │  mcp-price    (端口 8003)        │  │
│  │  - 股票价格查询                   │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   数据卷                          │  │
│  │   - ./data (交易数据)             │  │
│  │   - ./logs (日志文件)             │  │
│  │   - ./configs (配置文件)          │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 服务说明

| 服务名称 | 容器名称 | 端口 | 功能 |
|---------|---------|------|------|
| **ai-trader** | ai-trader-main | - | 主程序，运行AI交易逻辑 |
| **mcp-math** | ai-trader-mcp-math | 8000 | 数学计算服务 |
| **mcp-search** | ai-trader-mcp-search | 8001 | 市场信息搜索服务 |
| **mcp-trade** | ai-trader-mcp-trade | 8002 | 股票交易服务 |
| **mcp-price** | ai-trader-mcp-price | 8003 | 价格查询服务 |

---

## 配置说明

### 修改配置文件

编辑 `configs/default_config.json` 来配置：

```json
{
  "agent_type": "BaseAgent",
  "date_range": {
    "init_date": "2025-10-01",    // 开始日期
    "end_date": "2025-10-21"       // 结束日期
  },
  "models": [
    {
      "name": "gpt-5",
      "basemodel": "openai/gpt-5",
      "signature": "gpt-5",
      "enabled": true                // 启用此模型
    }
  ],
  "agent_config": {
    "max_steps": 30,                 // 最大推理步数
    "initial_cash": 10000.0          // 初始资金
  }
}
```

### 自定义配置运行

```bash
# 使用自定义配置文件
docker-compose run --rm ai-trader python main.py configs/my_config.json
```

---

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f ai-trader
docker-compose logs -f mcp-trade

# 查看最近100行日志
docker-compose logs --tail=100 ai-trader

# 查看带时间戳的日志
docker-compose logs -f -t ai-trader
```

### 进入容器

```bash
# 进入主程序容器
docker-compose exec ai-trader bash

# 进入 MCP 服务容器
docker-compose exec mcp-trade bash

# 在容器中运行命令
docker-compose exec ai-trader python -c "import sys; print(sys.version)"
```

### 数据管理

```bash
# 查看交易记录
ls -la ./data/agent_data/

# 查看特定AI的交易记录
cat ./data/agent_data/gpt-5/position/position.jsonl

# 备份数据
tar -czf backup_$(date +%Y%m%d).tar.gz ./data ./logs

# 清理旧日志
docker-compose down
rm -rf ./logs/*
```

### 重建和清理

```bash
# 重新构建镜像（代码更新后）
docker-compose build --no-cache

# 停止并删除所有容器、网络
docker-compose down

# 停止并删除所有容器、网络、卷
docker-compose down -v

# 清理未使用的 Docker 资源
docker system prune -a
```

---

## 故障排查

### 问题 1: 服务启动失败

**症状：** `docker-compose up` 后服务无法启动

**解决方案：**

```bash
# 1. 查看详细日志
docker-compose logs ai-trader

# 2. 检查端口是否被占用
lsof -i :8000
lsof -i :8001
lsof -i :8002
lsof -i :8003

# 3. 停止占用端口的进程或修改端口配置
# 编辑 .env 文件修改端口号
```

### 问题 2: API 连接失败

**症状：** 日志中显示 API 密钥错误或连接失败

**解决方案：**

```bash
# 1. 验证 .env 文件配置
cat .env

# 2. 重新启动服务使配置生效
docker-compose down
docker-compose up -d

# 3. 检查 API 密钥是否有效
# 登录对应的服务商网站验证
```

### 问题 3: 容器内存不足

**症状：** 容器被系统杀死或运行缓慢

**解决方案：**

```bash
# 1. 增加 Docker Desktop 内存限制
# Mac/Windows: Docker Desktop -> Settings -> Resources -> Memory

# 2. 查看容器资源使用
docker stats

# 3. 限制特定服务的资源使用
# 在 docker-compose.yml 中添加：
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

### 问题 4: 数据卷权限问题

**症状：** 无法写入文件或读取数据

**解决方案：**

```bash
# 修复数据目录权限
sudo chown -R $(whoami):$(whoami) ./data ./logs

# 或在 Dockerfile 中指定用户
```

### 问题 5: MCP 服务连接超时

**症状：** 主程序无法连接到 MCP 服务

**解决方案：**

```bash
# 1. 检查服务健康状态
docker-compose ps

# 2. 手动测试端口连接
curl http://localhost:8000
curl http://localhost:8001
curl http://localhost:8002
curl http://localhost:8003

# 3. 查看 MCP 服务日志
docker-compose logs mcp-math
docker-compose logs mcp-search
docker-compose logs mcp-trade
docker-compose logs mcp-price

# 4. 增加启动等待时间
# 在 docker-compose.yml 中调整 healthcheck 参数
```

---

## 开发模式

### 挂载本地代码

如果你想修改代码并实时测试：

```yaml
# 在 docker-compose.yml 中添加代码卷映射
services:
  ai-trader:
    volumes:
      - ./:/app  # 挂载整个项目目录
      - ./data:/app/data
      - ./logs:/app/logs
```

```bash
# 代码修改后重启服务
docker-compose restart ai-trader
```

### 使用本地 Python 环境

```bash
# 仅启动 MCP 服务
docker-compose up -d mcp-math mcp-search mcp-trade mcp-price

# 本地运行主程序
export OPENAI_API_KEY=your-key
python main.py
```

---

## 性能优化

### 1. 使用多阶段构建

Dockerfile 已经优化，但可以进一步改进：

```dockerfile
# 多阶段构建示例
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
```

### 2. 使用 Docker 缓存

```bash
# 利用 BuildKit 加速构建
DOCKER_BUILDKIT=1 docker-compose build
```

### 3. 限制日志大小

```yaml
# 在 docker-compose.yml 中添加
services:
  ai-trader:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 生产环境部署

### 使用 Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署服务栈
docker stack deploy -c docker-compose.yml ai-trader

# 查看服务状态
docker service ls
```

### 使用 Kubernetes

```bash
# 使用 Kompose 转换 docker-compose.yml
kompose convert

# 部署到 Kubernetes
kubectl apply -f .
```

---

## 安全建议

1. **不要将 .env 文件提交到 Git**
   ```bash
   # 确保 .gitignore 包含
   .env
   ```

2. **使用 Docker Secrets (Swarm/Kubernetes)**
   ```bash
   # 创建 secret
   echo "your-api-key" | docker secret create openai_key -
   ```

3. **限制容器权限**
   ```yaml
   # 在 docker-compose.yml 中
   services:
     ai-trader:
       security_opt:
         - no-new-privileges:true
       read_only: true
   ```

---

## 监控和日志

### 集成 Prometheus + Grafana

```yaml
# 添加到 docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 使用 ELK Stack

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
  logstash:
    image: logstash:8.11.0
  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
```

---

## 备份和恢复

### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

mkdir -p $BACKUP_DIR

# 备份数据
tar -czf $BACKUP_DIR/data_$DATE.tar.gz ./data

# 备份配置
tar -czf $BACKUP_DIR/config_$DATE.tar.gz ./configs ./.env

echo "✅ 备份完成: $BACKUP_DIR"
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 恢复数据
tar -xzf backups/data_20251105.tar.gz

# 重启服务
docker-compose up -d
```

---

## 支持和贡献

- **问题反馈**: [GitHub Issues](https://github.com/HKUDS/AI-Trader/issues)
- **文档**: [项目 README](README.md)
- **贡献指南**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 常见问题 (FAQ)

**Q: 如何更新到最新版本？**

```bash
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

**Q: 可以在云服务器上运行吗？**

A: 可以！在 AWS、GCP、Azure 等云平台的 VM 上安装 Docker 后即可运行。

**Q: 如何同时运行多个配置？**

A: 复制 docker-compose.yml 并修改服务名称和端口，然后使用 `-f` 参数：

```bash
docker-compose -f docker-compose-test.yml up -d
```

**Q: 数据会丢失吗？**

A: 数据存储在 `./data` 和 `./logs` 目录中，即使删除容器也不会丢失。

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

**🎉 祝你使用愉快！如有问题，欢迎提交 Issue。**
