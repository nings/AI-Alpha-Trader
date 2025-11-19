# 🚀 传统交易策略快速开始

## 1分钟快速启动

### 步骤 1: 启动MCP服务

```bash
cd agent_tools
python start_mcp_services.py
```

### 步骤 2: 运行传统策略

```bash
# 返回项目根目录
cd ..

# 使用传统策略配置运行
python main.py configs/traditional_config.json
```

就这么简单！🎉

---

## 🔍 查看结果

### 查看交易记录

```bash
# 查看持仓变化
cat data/agent_data/traditional-multi-indicator/position/position.jsonl | tail -5

# 查看详细日志
ls data/agent_data/traditional-multi-indicator/log/
```

---

## ⚙️ 自定义策略

编辑 `configs/traditional_config.json`:

```json
{
  "agent_type": "TraditionalAgent",
  "date_range": {
    "init_date": "2025-10-01",  // 修改起始日期
    "end_date": "2025-10-21"     // 修改结束日期
  },
  "models": [
    {
      "name": "我的策略",
      "signature": "my-strategy",
      "enabled": true,
      "max_position_pct": 0.20,  // 单股最大仓位20%
      "top_n_stocks": 8          // 持有8只股票
    }
  ],
  "agent_config": {
    "initial_cash": 10000.0      // 初始资金
  }
}
```

---

## 📊 与AI策略对比

### 方案1: 分别运行

```bash
# 运行传统策略
python main.py configs/traditional_config.json

# 运行AI策略
python main.py configs/default_config.json

# 对比结果
python calculate_performance.py
```

### 方案2: 创建混合配置

创建 `configs/mixed_config.json`:

```json
{
  "agent_type": "BaseAgent",
  "date_range": {
    "init_date": "2025-10-01",
    "end_date": "2025-10-21"
  },
  "models": [
    {
      "name": "GPT-4",
      "basemodel": "openai/gpt-4",
      "signature": "gpt-4",
      "enabled": true
    }
  ]
}
```

然后分别运行两个配置。

---

## 💡 策略说明

### 多指标综合策略（默认）

- **买入条件**: 至少2个技术指标发出买入信号
- **卖出条件**: 至少2个技术指标发出卖出信号
- **使用指标**: MA、RSI、MACD、布林带

### 工作原理

```
1. 每天分析100只纳斯达克股票
   ↓
2. 计算每只股票的技术指标
   ↓
3. 综合多个指标得出买卖信号
   ↓
4. 选择信号最强的前10只股票
   ↓
5. 执行买卖操作
   ↓
6. 记录交易结果
```

---

## 🎯 优势

✅ **无需AI API** - 不需要OpenAI等API密钥
✅ **运行快速** - 纯Python计算，秒级完成
✅ **成本为零** - 无额外API调用费用
✅ **结果稳定** - 相同数据得到相同结果
✅ **规则透明** - 可以清楚看到决策逻辑

---

## 📚 更多信息

详细文档请查看：
- [传统交易策略模块说明.md](传统交易策略模块说明.md) - 完整使用指南
- [初学者代码指南.md](初学者代码指南.md) - 代码原理解释

---

## ❓ 常见问题

**Q: 需要配置.env文件吗？**
A: 传统策略不需要AI API密钥，但如果要使用搜索等功能，仍需配置。基本的价格查询和交易功能不需要任何API。

**Q: 可以修改技术指标参数吗？**
A: 可以！编辑 `tools/technical_indicators.py` 中的默认参数，例如RSI的周期、MA的天数等。

**Q: 如何添加新的技术指标？**
A: 在 `tools/technical_indicators.py` 中添加新的计算函数，然后在 `get_technical_signals()` 中调用即可。

---

## 🎉 开始交易吧！

```bash
# 一键启动
python main.py configs/traditional_config.json
```

祝你交易顺利！📈
