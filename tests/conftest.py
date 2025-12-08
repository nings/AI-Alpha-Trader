"""
Pytest 配置文件
提供测试所需的 fixtures 和配置
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def sample_position() -> Dict[str, Any]:
    """示例持仓数据"""
    return {
        "AAPL": 10,
        "MSFT": 5,
        "NVDA": 0,
        "CASH": 5000.0
    }


@pytest.fixture
def sample_prices() -> Dict[str, float]:
    """示例价格数据"""
    return {
        "AAPL_price": 150.0,
        "MSFT_price": 380.0,
        "NVDA_price": 500.0,
        "GOOGL_price": 140.0,
        "AMZN_price": 180.0
    }


@pytest.fixture
def sample_historical_prices() -> list:
    """示例历史价格数据（用于技术指标计算）"""
    # 模拟30天的价格数据
    base_price = 100.0
    prices = []
    for i in range(30):
        # 模拟价格波动
        price = base_price + (i * 0.5) + ((i % 5) - 2)
        prices.append(price)
    return prices


@pytest.fixture
def temp_data_dir(tmp_path):
    """创建临时数据目录"""
    data_dir = tmp_path / "data" / "agent_data" / "test_agent" / "position"
    data_dir.mkdir(parents=True)
    return data_dir


@pytest.fixture
def temp_position_file(temp_data_dir):
    """创建临时持仓文件"""
    position_file = temp_data_dir / "position.jsonl"
    
    # 写入初始持仓
    initial_position = {
        "date": "2025-01-01",
        "id": 0,
        "positions": {
            "AAPL": 0,
            "MSFT": 0,
            "NVDA": 0,
            "CASH": 10000.0
        }
    }
    
    with open(position_file, "w") as f:
        f.write(json.dumps(initial_position) + "\n")
    
    return position_file


@pytest.fixture
def mock_runtime_env(tmp_path):
    """创建模拟的运行时环境配置"""
    runtime_env = tmp_path / "runtime_env.json"
    
    config = {
        "SIGNATURE": "test_agent",
        "TODAY_DATE": "2025-01-20",
        "IF_TRADE": False
    }
    
    with open(runtime_env, "w") as f:
        json.dump(config, f)
    
    # 设置环境变量
    os.environ["RUNTIME_ENV_PATH"] = str(runtime_env)
    
    yield runtime_env
    
    # 清理
    if "RUNTIME_ENV_PATH" in os.environ:
        del os.environ["RUNTIME_ENV_PATH"]


@pytest.fixture
def sample_merged_data(tmp_path):
    """创建示例的 merged.jsonl 数据"""
    merged_file = tmp_path / "merged.jsonl"
    
    # 创建示例数据
    sample_data = {
        "Meta Data": {
            "2. Symbol": "AAPL"
        },
        "Time Series (Daily)": {
            "2025-01-20": {
                "1. buy price": "150.00",
                "2. high": "155.00",
                "3. low": "148.00",
                "4. sell price": "152.00",
                "5. volume": "1000000"
            },
            "2025-01-19": {
                "1. buy price": "148.00",
                "2. high": "151.00",
                "3. low": "147.00",
                "4. sell price": "150.00",
                "5. volume": "900000"
            }
        }
    }
    
    with open(merged_file, "w") as f:
        f.write(json.dumps(sample_data) + "\n")
    
    return merged_file
