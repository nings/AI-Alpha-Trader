# 🚀 AI-Trader Quick Start Guide

快速上手指南，5分钟让AI开始交易！

## 📋 前置要求

- Python 3.10+
- API Keys:
  - OpenAI API Key (或其他兼容的LLM API)
  - Alpha Vantage API Key (免费获取: https://www.alphavantage.co/)
  - Jina AI API Key (免费获取: https://jina.ai/)

## ⚡ 快速开始（3步）

### 1️⃣ 初始化项目

```bash
# 克隆并进入项目
git clone https://github.com/HKUDS/AI-Trader.git
cd AI-Trader

# 运行初始化脚本
./init.sh
```

初始化脚本会自动：
- ✅ 检查Python版本
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 创建配置文件

### 2️⃣ 配置API密钥

编辑 `.env` 文件，填入你的API密钥：

```bash
# 编辑配置
vim .env  # 或使用其他编辑器

# 必须配置的密钥：
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-openai-key-here
ALPHAADVANTAGE_API_KEY=your-alpha-vantage-key
JINA_API_KEY=your-jina-key
```

### 3️⃣ 运行AI交易

```bash
# 一键运行完整流程
./run.sh
```

这个命令会：
1. 📊 刷新股票数据（可选）
2. 🚀 启动MCP服务
3. 🤖 运行AI交易
4. 📈 生成性能报告

## 📖 分步运行（详细）

如果你想分步执行，可以使用以下命令：

### 步骤1: 获取数据

```bash
./fresh_data.sh
```

### 步骤2: 启动MCP服务

```bash
./start_services.sh
```

### 步骤3: 运行交易

```bash
# 使用默认配置
python main.py

# 或使用自定义配置
python main.py configs/my_config.json
```

### 步骤4: 查看结果

```bash
# 计算性能指标
./calc_perf.sh

# 查看性能报告
cat performance_report.json
```

### 步骤5: 停止服务

```bash
./stop_services.sh
```

## ⚙️ 配置说明

### 修改交易日期

编辑 `configs/default_config.json`:

```json
{
  "date_range": {
    "init_date": "2025-10-01",  // 开始日期
    "end_date": "2025-10-21"     // 结束日期
  }
}
```

### 选择AI模型

在配置文件中启用/禁用模型：

```json
{
  "models": [
    {
      "name": "gpt-5",
      "basemodel": "openai/gpt-5",
      "signature": "gpt-5",
      "enabled": true  // 设为true启用，false禁用
    }
  ]
}
```

### 调整初始资金

```json
{
  "agent_config": {
    "initial_cash": 10000.0  // 修改初始资金
  }
}
```

## 📊 查看结果

### 交易记录

```bash
# 查看某个模型的交易记录
cat data/agent_data/gpt-5/position/position.jsonl
```

### 交易日志

```bash
# 查看某天的详细日志
cat data/agent_data/gpt-5/log/2025-10-15/log.jsonl
```

### 性能排行榜

运行性能计算后会显示排行榜：

```
🏆 AI-TRADER PERFORMANCE LEADERBOARD 🏆
==================================================
Rank   Model                  Return %    Sharpe
--------------------------------------------------
🥇     gpt-5                  +8.39%      1.23
🥈     claude-3.7             +7.96%      1.15
🥉     qwen3-max              +6.14%      0.98
==================================================
```

## 🐛 常见问题

### Q: API密钥配置后仍报错？

A: 确保：
1. `.env` 文件在项目根目录
2. 没有多余的引号
3. 重启终端或重新加载环境变量

### Q: 数据下载很慢？

A: Alpha Vantage免费版有速率限制：
- 5次请求/分钟
- 500次请求/天
建议使用现有数据或升级API plan

### Q: MCP服务启动失败？

A: 检查端口是否被占用：
```bash
# 查看端口占用
lsof -i :8000
lsof -i :8001
lsof -i :8002
lsof -i :8003

# 停止所有服务
./stop_services.sh
```

### Q: 如何添加新的AI模型？

A: 在 `configs/default_config.json` 中添加：

```json
{
  "name": "my-new-model",
  "basemodel": "provider/model-name",
  "signature": "my-new-model",
  "enabled": true,
  "openai_base_url": "https://your-api-endpoint.com/v1",
  "openai_api_key": "your-api-key"
}
```

## 🎯 下一步

- 📖 阅读完整文档: [README.md](README.md)
- ⚙️ 配置详解: [configs/README.md](configs/README.md)
- 🤖 添加自定义策略
- 📊 分析历史表现
- 🌐 部署前端界面

## 💬 需要帮助？

- 📝 查看 [README.md](README.md) 完整文档
- 🐛 提交 Issue: https://github.com/HKUDS/AI-Trader/issues
- 💬 加入讨论: [GitHub Discussions](https://github.com/HKUDS/AI-Trader/discussions)

---

🌟 **开始你的AI交易之旅！**
