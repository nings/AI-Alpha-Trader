# 🚀 AI-Alpha-Trader Docker 快速开始

5分钟快速启动指南！

---

## ✅ 前置条件检查

```bash
# 检查 Docker 是否安装
docker --version
# 应该显示: Docker version 20.10+ 或更高

# 检查 Docker Compose 是否安装
docker compose version
# 应该显示: Docker Compose version v2.x.x
```

如果没有安装，请访问：https://docs.docker.com/get-docker/

---

## 🎯 三步启动

### 步骤 1: 配置 API 密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或者用你喜欢的编辑器
```

**最少配置（必需）：**

```bash
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

### 步骤 2: 启动服务

```bash
# 使用启动脚本（推荐）
./docker-start.sh

# 或者手动启动
docker compose up -d
```

### 步骤 3: 查看运行状态

```bash
# 查看服务状态
docker compose ps

# 查看实时日志
docker compose logs -f ai-trader
```

---

## 📊 验证服务

检查所有服务是否正常运行：

```bash
# 查看所有容器状态
docker compose ps

# 应该看到5个服务都在运行：
# ✅ ai-trader-main        (主程序)
# ✅ ai-trader-mcp-math    (数学服务)
# ✅ ai-trader-mcp-search  (搜索服务)
# ✅ ai-trader-mcp-trade   (交易服务)
# ✅ ai-trader-mcp-price   (价格服务)
```

测试 MCP 服务端口：

```bash
# 测试各个服务是否响应
curl http://localhost:8000  # Math Service
curl http://localhost:8001  # Search Service
curl http://localhost:8002  # Trade Service
curl http://localhost:8003  # Price Service
```

---

## 📈 查看交易结果

```bash
# 查看交易记录目录
ls -la ./data/agent_data/

# 查看特定AI的交易记录
cat ./data/agent_data/gpt-5/position/position.jsonl

# 查看日志
ls -la ./logs/
```

---

## 🛑 停止服务

```bash
# 使用停止脚本
./docker-stop.sh

# 或者手动停止
docker compose down
```

---

## 🔧 配置调整

### 修改交易日期范围

编辑 `configs/default_config.json`：

```json
{
  "date_range": {
    "init_date": "2025-01-01",  // 修改开始日期
    "end_date": "2025-01-31"    // 修改结束日期
  }
}
```

### 启用/禁用AI模型

在 `configs/default_config.json` 中：

```json
{
  "models": [
    {
      "name": "gpt-5",
      "enabled": true   // 改为 false 禁用此模型
    }
  ]
}
```

### 修改后重启

```bash
docker compose restart ai-trader
```

---

## 💡 常用命令

```bash
# 查看所有日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f ai-trader
docker compose logs -f mcp-trade

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 重新构建并启动
docker compose up -d --build

# 进入容器
docker compose exec ai-trader bash

# 查看资源使用
docker stats
```

---

## ❓ 常见问题

### Q1: 端口被占用怎么办？

修改 `.env` 文件中的端口：

```bash
MATH_HTTP_PORT=8010      # 改为其他端口
SEARCH_HTTP_PORT=8011
TRADE_HTTP_PORT=8012
GETPRICE_HTTP_PORT=8013
```

然后重启：

```bash
docker compose down
docker compose up -d
```

### Q2: 如何查看详细的错误信息？

```bash
# 查看容器日志
docker compose logs ai-trader --tail=100

# 进入容器检查
docker compose exec ai-trader bash
cat /app/logs/*.log
```

### Q3: 如何更新代码？

```bash
git pull origin main
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Q4: 数据会丢失吗？

不会！数据存储在宿主机的 `./data` 和 `./logs` 目录中。

### Q5: 如何备份数据？

```bash
tar -czf backup_$(date +%Y%m%d).tar.gz ./data ./logs
```

---

## 🎓 更多信息

- **详细文档**: 查看 [DOCKER_README.md](DOCKER_README.md)
- **初学者指南**: 查看 [初学者代码指南.md](初学者代码指南.md)
- **项目主页**: 查看 [README.md](README.md)

---

## 🐛 故障排查

### 服务启动失败

```bash
# 1. 检查Docker是否运行
docker ps

# 2. 查看详细日志
docker compose logs

# 3. 检查配置
docker compose config

# 4. 重新构建
docker compose build --no-cache
docker compose up -d
```

### API连接失败

```bash
# 1. 验证 .env 文件
cat .env | grep API_KEY

# 2. 重新加载环境变量
docker compose down
docker compose up -d
```

---

## 📞 获取帮助

- **GitHub Issues**: https://github.com/HKUDS/AI-Trader/issues
- **讨论区**: https://github.com/HKUDS/AI-Trader/discussions

---

**🎉 现在开始你的AI交易之旅吧！**
