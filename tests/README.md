# AI-Trader Tests

测试套件说明文档

## 📁 测试结构

```
tests/
├── __init__.py           # 测试模块初始化
├── test_agent.py         # Agent类测试
├── test_tools.py         # 工具函数测试
└── README.md            # 本文档
```

## 🚀 运行测试

### 运行所有测试

```bash
pytest tests/
```

### 运行特定测试文件

```bash
# 测试Agent
pytest tests/test_agent.py

# 测试工具
pytest tests/test_tools.py
```

### 详细输出

```bash
pytest tests/ -v
```

### 覆盖率报告

```bash
pytest tests/ --cov=. --cov-report=html
```

## 📝 测试说明

### test_agent.py

测试 BaseAgent 类的核心功能：

- ✅ Agent初始化
- ✅ MCP配置
- ✅ 日志设置
- ✅ Agent注册
- ✅ 交易日期生成
- ✅ 持仓摘要

### test_tools.py

测试工具函数：

- ✅ 对话提取
- ✅ 工具消息提取
- ✅ 配置读写
- ✅ 性能计算

## ⚙️ 测试配置

测试使用临时目录和模拟数据，不会影响实际数据。

## 🐛 调试测试

```bash
# 运行单个测试
pytest tests/test_agent.py::TestBaseAgent::test_agent_initialization -v

# 查看打印输出
pytest tests/ -s

# 进入调试器
pytest tests/ --pdb
```

## 📊 测试覆盖率

运行测试并生成覆盖率报告：

```bash
pytest tests/ --cov=agent --cov=tools --cov-report=html
```

查看报告：
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔄 持续集成

测试可以集成到CI/CD流程中：

```yaml
# .github/workflows/test.yml 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
```

## 📝 添加新测试

创建新测试时遵循以下模式：

```python
import pytest

class TestMyFeature:
    """Test my new feature"""

    @pytest.fixture
    def setup_data(self):
        """Setup test data"""
        return {'key': 'value'}

    def test_feature(self, setup_data):
        """Test the feature"""
        assert setup_data['key'] == 'value'
```

## 🎯 测试最佳实践

1. **使用fixtures** - 复用测试数据和设置
2. **独立测试** - 每个测试应该独立运行
3. **清理资源** - 测试后清理临时文件
4. **有意义的断言** - 使用清晰的断言消息
5. **测试边界情况** - 测试正常和异常情况

## 📚 更多资源

- [pytest 文档](https://docs.pytest.org/)
- [测试驱动开发](https://en.wikipedia.org/wiki/Test-driven_development)
- [Python 测试最佳实践](https://docs.python-guide.org/writing/tests/)
