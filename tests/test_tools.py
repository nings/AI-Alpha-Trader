"""
AI-Trader Tools Tests
Test cases for utility functions
"""

import pytest
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tools.general_tools import extract_conversation, extract_tool_messages


class TestGeneralTools:
    """Test general utility functions"""

    def test_extract_conversation_final(self):
        """Test extracting final conversation"""
        conversation = {
            'messages': [
                {'role': 'user', 'content': 'Hello'},
                {
                    'role': 'assistant',
                    'content': 'Final response',
                    'response_metadata': {'finish_reason': 'stop'}
                }
            ]
        }

        result = extract_conversation(conversation, 'final')
        assert result == 'Final response'

    def test_extract_conversation_all(self):
        """Test extracting all messages"""
        conversation = {
            'messages': [
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Hi there'}
            ]
        }

        result = extract_conversation(conversation, 'all')
        assert len(result) == 2
        assert result[0]['content'] == 'Hello'

    def test_extract_tool_messages(self):
        """Test extracting tool messages"""
        conversation = {
            'messages': [
                {'role': 'user', 'content': 'Hello'},
                {'tool_call_id': '123', 'content': 'Tool result'},
                {'role': 'assistant', 'content': 'Response'}
            ]
        }

        tool_msgs = extract_tool_messages(conversation)
        assert len(tool_msgs) == 1
        assert tool_msgs[0]['tool_call_id'] == '123'


class TestConfigManagement:
    """Test configuration management"""

    def test_config_read_write(self, tmp_path):
        """Test config read and write"""
        from tools.general_tools import get_config_value, write_config_value

        # Set up temp config file
        config_file = tmp_path / "test_config.json"
        os.environ['RUNTIME_ENV_PATH'] = str(config_file)

        # Write config
        write_config_value('TEST_KEY', 'test_value')

        # Read config
        value = get_config_value('TEST_KEY')
        assert value == 'test_value'

        # Clean up
        del os.environ['RUNTIME_ENV_PATH']


class TestPerformanceCalculator:
    """Test performance calculation"""

    @pytest.fixture
    def sample_positions(self):
        """Sample position data"""
        return [
            {
                'date': '2025-01-01',
                'id': 0,
                'positions': {'AAPL': 0, 'CASH': 10000.0}
            },
            {
                'date': '2025-01-02',
                'id': 1,
                'this_action': {'action': 'buy', 'symbol': 'AAPL', 'amount': 10},
                'positions': {'AAPL': 10, 'CASH': 8500.0}
            }
        ]

    def test_position_loading(self, tmp_path, sample_positions):
        """Test loading position data"""
        from calculate_performance import PerformanceCalculator

        # Create test data
        agent_data = tmp_path / "agent_data"
        agent_dir = agent_data / "test-agent" / "position"
        agent_dir.mkdir(parents=True)

        position_file = agent_dir / "position.jsonl"
        with open(position_file, 'w') as f:
            for pos in sample_positions:
                f.write(json.dumps(pos) + '\n')

        # Test loading
        calc = PerformanceCalculator(str(agent_data))
        positions = calc.load_position_data('test-agent')

        assert len(positions) == 2
        assert positions[0]['positions']['CASH'] == 10000.0

    def test_returns_calculation(self, sample_positions):
        """Test returns calculation"""
        from calculate_performance import PerformanceCalculator

        calc = PerformanceCalculator()
        returns = calc.calculate_returns(sample_positions)

        # Should calculate return between two positions
        assert len(returns) >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
