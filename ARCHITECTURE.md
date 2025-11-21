# 🏗️ AI-Trader Architecture

AI-Trader项目的模块化架构设计文档

## 📐 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     AI-Trader System                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │   Main.py   │──▶│  BaseAgent   │──▶│ MCP Tools   │  │
│  │   Entry     │   │   Trading    │   │   Suite     │  │
│  │   Point     │   │   Engine     │   │             │  │
│  └─────────────┘   └──────────────┘   └─────────────┘  │
│         │                  │                   │         │
│         ▼                  ▼                   ▼         │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │   Config    │   │  Data Store  │   │   Price     │  │
│  │   Manager   │   │  Position    │   │   Data      │  │
│  └─────────────┘   └──────────────┘   └─────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 🎯 核心模块

### 1. 主程序模块 (main.py)

**职责**：
- 程序入口和流程控制
- 配置加载和验证
- Agent实例化和管理
- 多模型并发控制

**主要功能**：
```python
# 加载配置
config = load_config(config_path)

# 动态加载Agent类
AgentClass = get_agent_class(agent_type)

# 运行交易
await agent.run_date_range(init_date, end_date)
```

### 2. Agent模块 (agent/base_agent/)

**职责**：
- AI代理核心逻辑
- MCP工具管理
- 交易决策循环
- 状态管理

**类结构**：
```python
class BaseAgent:
    - __init__(): 初始化Agent
    - initialize(): 初始化MCP和AI模型
    - run_trading_session(): 运行单日交易
    - run_date_range(): 运行日期范围
    - register_agent(): 注册新Agent
    - get_position_summary(): 获取持仓摘要
```

**关键特性**：
- ✅ 异步操作
- ✅ 自动重试机制
- ✅ 完整的日志记录
- ✅ 状态持久化

### 3. MCP工具链 (agent_tools/)

**职责**：
- 提供标准化工具接口
- 执行具体交易操作
- 数据查询和搜索

**工具列表**：

| 工具 | 文件 | 功能 |
|------|------|------|
| **交易工具** | tool_trade.py | buy(), sell() |
| **价格工具** | tool_get_price_local.py | get_price_local() |
| **搜索工具** | tool_jina_search.py | get_information() |
| **数学工具** | tool_math.py | 基础数学运算 |

**服务架构**：
```
┌──────────────┐
│ start_mcp_   │
│ services.py  │
└──────┬───────┘
       │
       ├─▶ Math Service (Port 8000)
       ├─▶ Search Service (Port 8001)
       ├─▶ Trade Service (Port 8002)
       └─▶ GetPrice Service (Port 8003)
```

### 4. 数据模块 (data/)

**职责**：
- 股票价格数据获取
- 数据格式转换
- 数据存储和检索

**文件结构**：
```
data/
├── get_daily_price.py      # 获取日线数据
├── get_interdaily_price.py # 获取分钟级数据
├── merge_jsonl.py          # 数据合并
├── merged.jsonl            # 统一数据格式
└── agent_data/             # Agent交易数据
    └── {signature}/
        ├── position/       # 持仓记录
        └── log/           # 交易日志
```

**数据流**：
```
Alpha Vantage API
       │
       ▼
get_daily_price.py
       │
       ▼
daily_prices_*.json
       │
       ▼
merge_jsonl.py
       │
       ▼
merged.jsonl (统一格式)
       │
       ▼
Agent (读取和使用)
```

### 5. 工具模块 (tools/)

**职责**：
- 通用工具函数
- 价格处理
- 结果分析

**模块列表**：

| 模块 | 功能 |
|------|------|
| general_tools.py | 配置管理、消息提取 |
| price_tools.py | 价格查询、持仓管理 |
| result_tools.py | 结果分析、报告生成 |

### 6. 提示词模块 (prompts/)

**职责**：
- AI提示词管理
- 系统提示生成

**核心功能**：
```python
def get_agent_system_prompt(date, signature):
    """生成Agent系统提示

    包含:
    - 当前日期
    - 持仓信息
    - 价格信息
    - 交易规则
    """
```

### 7. 性能分析模块 (calculate_performance.py)

**职责**：
- 性能指标计算
- 交易分析
- 排行榜生成

**核心指标**：
- 📈 总收益率
- 📊 夏普比率
- 📉 最大回撤
- 🎯 胜率
- 💼 交易次数

**类结构**：
```python
class PerformanceCalculator:
    - load_position_data(): 加载持仓数据
    - calculate_total_value(): 计算总价值
    - calculate_returns(): 计算收益率
    - calculate_sharpe_ratio(): 计算夏普比率
    - calculate_max_drawdown(): 计算最大回撤
    - analyze_all_agents(): 分析所有Agent
```

## 🔧 配置系统

### 配置文件 (configs/)

**结构**：
```json
{
  "agent_type": "BaseAgent",
  "date_range": {
    "init_date": "2025-10-01",
    "end_date": "2025-10-21"
  },
  "models": [...],
  "agent_config": {
    "max_steps": 30,
    "max_retries": 3,
    "base_delay": 1.0,
    "initial_cash": 10000.0
  },
  "log_config": {
    "log_path": "./data/agent_data"
  }
}
```

### 环境变量 (.env)

```bash
# API配置
OPENAI_API_BASE=...
OPENAI_API_KEY=...
ALPHAADVANTAGE_API_KEY=...
JINA_API_KEY=...

# 服务端口
MATH_HTTP_PORT=8000
SEARCH_HTTP_PORT=8001
TRADE_HTTP_PORT=8002
GETPRICE_HTTP_PORT=8003

# Agent配置
AGENT_MAX_STEP=30
RUNTIME_ENV_PATH=./.runtime_env.json
```

## 🔄 数据流

### 交易流程

```
1. 初始化
   ├─▶ 加载配置
   ├─▶ 创建Agent实例
   └─▶ 初始化MCP连接

2. 交易循环
   ├─▶ 获取市场数据
   ├─▶ AI分析决策
   ├─▶ 执行交易操作
   ├─▶ 更新持仓
   └─▶ 记录日志

3. 性能分析
   ├─▶ 加载交易记录
   ├─▶ 计算性能指标
   ├─▶ 生成报告
   └─▶ 输出排行榜
```

### 数据存储

```
position.jsonl 格式:
{
  "date": "2025-10-15",
  "id": 1,
  "this_action": {
    "action": "buy",
    "symbol": "AAPL",
    "amount": 10
  },
  "positions": {
    "AAPL": 10,
    "MSFT": 0,
    "CASH": 9500.0
  }
}
```

## 🎨 设计模式

### 1. 工厂模式 (Agent Registry)

```python
AGENT_REGISTRY = {
    "BaseAgent": {
        "module": "agent.base_agent.base_agent",
        "class": "BaseAgent"
    }
}

def get_agent_class(agent_type):
    """动态加载Agent类"""
    ...
```

### 2. 模板方法模式 (BaseAgent)

```python
class BaseAgent:
    async def run_trading_session(self):
        """模板方法"""
        self._setup_logging()
        while not stopped:
            response = await self._ainvoke_with_retry()
            self._handle_trading_result()
```

### 3. 策略模式 (不同AI模型)

```python
# 不同模型使用相同接口
agent_gpt = BaseAgent(basemodel="openai/gpt-5")
agent_claude = BaseAgent(basemodel="anthropic/claude-3.7")
```

## 🚀 扩展性

### 添加新Agent类型

```python
# 1. 创建新Agent类
class CustomAgent(BaseAgent):
    def custom_logic(self):
        ...

# 2. 注册到Registry
AGENT_REGISTRY["CustomAgent"] = {
    "module": "agent.custom.custom_agent",
    "class": "CustomAgent"
}

# 3. 配置使用
{
  "agent_type": "CustomAgent",
  ...
}
```

### 添加新MCP工具

```python
# 1. 创建工具文件
@mcp.tool()
def my_custom_tool(param: str):
    """自定义工具"""
    return result

# 2. 添加到start_mcp_services.py

# 3. Agent自动加载
```

### 添加新AI模型

```json
{
  "models": [
    {
      "name": "new-model",
      "basemodel": "provider/model-name",
      "signature": "new-model",
      "enabled": true
    }
  ]
}
```

## 🛡️ 错误处理

### 重试机制

```python
async def _ainvoke_with_retry(self):
    for attempt in range(self.max_retries):
        try:
            return await self.agent.ainvoke(...)
        except Exception as e:
            if attempt == self.max_retries:
                raise
            await asyncio.sleep(self.base_delay * attempt)
```

### 异常捕获

```python
try:
    await agent.run_trading_session(date)
except Exception as e:
    logger.error(f"Trading error: {e}")
    # 继续处理下一个模型
```

## 📊 性能优化

### 异步操作

- 使用 `async/await` 处理I/O密集操作
- MCP工具并发调用
- 多模型并行运行

### 数据缓存

- 价格数据本地缓存
- 配置文件缓存
- 减少API调用

## 🔒 安全考虑

### API密钥管理

- 使用 `.env` 文件
- 不提交到版本控制
- 环境变量覆盖

### 数据验证

- 交易前验证余额
- 价格数据有效性检查
- 配置文件格式验证

## 📚 依赖管理

### 核心依赖

```
langchain: AI框架
langchain-openai: OpenAI集成
langchain-mcp-adapters: MCP适配器
fastmcp: MCP服务框架
python-dotenv: 环境变量管理
numpy, pandas: 数据处理
```

### 依赖版本

查看 `requirements.txt` 获取完整依赖列表和版本要求。

## 🎯 最佳实践

1. **模块化设计** - 每个模块职责单一
2. **配置驱动** - 通过配置文件控制行为
3. **完整日志** - 记录所有关键操作
4. **错误处理** - 优雅的错误处理和恢复
5. **测试覆盖** - 单元测试和集成测试
6. **文档完善** - 代码注释和文档

---

📖 更多信息请查看：
- [README.md](README.md) - 项目总览
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [configs/README.md](configs/README.md) - 配置指南
