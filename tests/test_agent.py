"""
AI-Trader Agent Tests
Test cases for the BaseAgent class
"""

import pytest
import asyncio
import os
import json
from pathlib import Path
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from agent.base_agent.base_agent import BaseAgent


class TestBaseAgent:
    """Test cases for BaseAgent"""

    @pytest.fixture
    def test_config(self):
        """Test configuration"""
        return {
            'signature': 'test-agent',
            'basemodel': 'gpt-4',
            'stock_symbols': ['AAPL', 'MSFT', 'GOOGL'],
            'log_path': './test_data/agent_data',
            'max_steps': 5,
            'max_retries': 2,
            'base_delay': 0.1,
            'initial_cash': 10000.0,
            'init_date': '2025-01-01'
        }

    @pytest.fixture
    def agent(self, test_config):
        """Create test agent instance"""
        agent = BaseAgent(**test_config)
        return agent

    def test_agent_initialization(self, agent, test_config):
        """Test agent initialization"""
        assert agent.signature == test_config['signature']
        assert agent.basemodel == test_config['basemodel']
        assert len(agent.stock_symbols) == 3
        assert agent.initial_cash == 10000.0

    def test_get_default_mcp_config(self, agent):
        """Test default MCP configuration"""
        config = agent._get_default_mcp_config()

        assert 'math' in config
        assert 'stock_local' in config
        assert 'search' in config
        assert 'trade' in config

        # Check transport type
        for service in config.values():
            assert service['transport'] == 'streamable_http'
            assert 'url' in service

    def test_setup_logging(self, agent, tmp_path):
        """Test logging setup"""
        agent.base_log_path = str(tmp_path)

        today_date = '2025-01-15'
        log_file = agent._setup_logging(today_date)

        assert Path(log_file).exists()
        assert today_date in log_file

    def test_register_agent(self, agent, tmp_path):
        """Test agent registration"""
        agent.data_path = str(tmp_path / agent.signature)
        agent.position_file = str(tmp_path / agent.signature / "position" / "position.jsonl")

        agent.register_agent()

        # Check position file was created
        assert Path(agent.position_file).exists()

        # Check initial position
        with open(agent.position_file, 'r') as f:
            position = json.loads(f.readline())
            assert position['positions']['CASH'] == 10000.0
            assert position['id'] == 0

    def test_get_trading_dates(self, agent):
        """Test trading dates generation"""
        init_date = '2025-01-01'
        end_date = '2025-01-05'

        dates = agent.get_trading_dates(init_date, end_date)

        # Should only include weekdays
        assert all(
            datetime.strptime(date, '%Y-%m-%d').weekday() < 5
            for date in dates
        )

    def test_position_summary(self, agent, tmp_path):
        """Test position summary"""
        agent.data_path = str(tmp_path / agent.signature)
        agent.position_file = str(tmp_path / agent.signature / "position" / "position.jsonl")

        # Register agent to create initial position
        agent.register_agent()

        summary = agent.get_position_summary()

        assert summary['signature'] == agent.signature
        assert summary['total_records'] == 1
        assert 'CASH' in summary['positions']

    def test_agent_str_representation(self, agent):
        """Test agent string representation"""
        agent_str = str(agent)

        assert 'BaseAgent' in agent_str
        assert agent.signature in agent_str
        assert agent.basemodel in agent_str


class TestAgentTools:
    """Test MCP tools integration"""

    def test_mcp_config_structure(self):
        """Test MCP configuration structure"""
        from agent.base_agent.base_agent import BaseAgent

        agent = BaseAgent(
            signature='test',
            basemodel='gpt-4',
            initial_cash=10000.0
        )

        config = agent._get_default_mcp_config()

        required_services = ['math', 'stock_local', 'search', 'trade']
        for service in required_services:
            assert service in config
            assert 'transport' in config[service]
            assert 'url' in config[service]


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations"""

    async def test_agent_initialization_async(self):
        """Test async agent initialization"""
        # This would require actual MCP services running
        # For now, just test that the method exists
        agent = BaseAgent(
            signature='test-async',
            basemodel='gpt-4',
            initial_cash=10000.0
        )

        assert hasattr(agent, 'initialize')
        assert asyncio.iscoroutinefunction(agent.initialize)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
