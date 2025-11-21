#!/usr/bin/env python3
"""
AI-Trader Performance Analysis Module
Calculate performance metrics for AI trading models
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import numpy as np


class PerformanceCalculator:
    """Calculate trading performance metrics"""

    def __init__(self, agent_data_path: str = "./data/agent_data"):
        """
        Initialize performance calculator

        Args:
            agent_data_path: Path to agent data directory
        """
        self.agent_data_path = Path(agent_data_path)

    def load_position_data(self, signature: str) -> List[Dict]:
        """
        Load position data for a specific agent

        Args:
            signature: Agent signature/model name

        Returns:
            List of position records
        """
        position_file = self.agent_data_path / signature / "position" / "position.jsonl"

        if not position_file.exists():
            print(f"⚠️  Position file not found for {signature}")
            return []

        positions = []
        with open(position_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    positions.append(json.loads(line))

        return positions

    def calculate_total_value(self, position: Dict, prices: Dict) -> float:
        """
        Calculate total portfolio value

        Args:
            position: Position dictionary
            prices: Stock prices dictionary

        Returns:
            Total portfolio value
        """
        total_value = position.get('CASH', 0)

        for symbol, amount in position.items():
            if symbol != 'CASH' and amount > 0:
                price = prices.get(symbol, 0)
                total_value += amount * price

        return total_value

    def calculate_returns(self, positions: List[Dict]) -> List[float]:
        """
        Calculate daily returns

        Args:
            positions: List of position records

        Returns:
            List of daily returns
        """
        if len(positions) < 2:
            return []

        returns = []
        for i in range(1, len(positions)):
            prev_value = sum(v for k, v in positions[i-1]['positions'].items() if k != 'CASH')
            prev_value += positions[i-1]['positions'].get('CASH', 0)

            curr_value = sum(v for k, v in positions[i]['positions'].items() if k != 'CASH')
            curr_value += positions[i]['positions'].get('CASH', 0)

            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)

        return returns

    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio

        Args:
            returns: List of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate

        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe

    def calculate_max_drawdown(self, positions: List[Dict]) -> float:
        """
        Calculate maximum drawdown

        Args:
            positions: List of position records

        Returns:
            Maximum drawdown percentage
        """
        if len(positions) < 2:
            return 0.0

        values = []
        for pos in positions:
            total = sum(v for k, v in pos['positions'].items() if k != 'CASH')
            total += pos['positions'].get('CASH', 0)
            values.append(total)

        max_dd = 0.0
        peak = values[0]

        for value in values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd * 100  # Return as percentage

    def calculate_win_rate(self, positions: List[Dict]) -> float:
        """
        Calculate win rate (percentage of profitable trades)

        Args:
            positions: List of position records

        Returns:
            Win rate percentage
        """
        if len(positions) < 2:
            return 0.0

        wins = 0
        total_trades = 0

        for i in range(1, len(positions)):
            if 'this_action' in positions[i]:
                total_trades += 1
                prev_value = sum(v for k, v in positions[i-1]['positions'].items() if k != 'CASH')
                prev_value += positions[i-1]['positions'].get('CASH', 0)

                curr_value = sum(v for k, v in positions[i]['positions'].items() if k != 'CASH')
                curr_value += positions[i]['positions'].get('CASH', 0)

                if curr_value > prev_value:
                    wins += 1

        return (wins / total_trades * 100) if total_trades > 0 else 0.0

    def calculate_all_metrics(self, signature: str) -> Dict:
        """
        Calculate all performance metrics for an agent

        Args:
            signature: Agent signature/model name

        Returns:
            Dictionary of performance metrics
        """
        positions = self.load_position_data(signature)

        if not positions:
            return {
                'signature': signature,
                'error': 'No position data available'
            }

        # Basic info
        initial_cash = positions[0]['positions'].get('CASH', 0)
        final_position = positions[-1]['positions']
        final_cash = final_position.get('CASH', 0)

        # Calculate final portfolio value (assuming current price = initial price for simplicity)
        # In production, should fetch actual current prices
        final_value = final_cash
        for symbol, amount in final_position.items():
            if symbol != 'CASH':
                final_value += amount * 100  # Placeholder price

        # Returns
        total_return = ((final_value - initial_cash) / initial_cash * 100) if initial_cash > 0 else 0
        returns = self.calculate_returns(positions)

        # Risk metrics
        sharpe = self.calculate_sharpe_ratio(returns)
        max_dd = self.calculate_max_drawdown(positions)
        win_rate = self.calculate_win_rate(positions)

        # Trading activity
        total_trades = len([p for p in positions if 'this_action' in p])

        return {
            'signature': signature,
            'initial_cash': initial_cash,
            'final_value': final_value,
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(max_dd, 2),
            'win_rate': round(win_rate, 2),
            'total_trades': total_trades,
            'total_days': len(positions),
            'latest_date': positions[-1].get('date', 'N/A')
        }

    def analyze_all_agents(self) -> List[Dict]:
        """
        Analyze performance for all agents

        Returns:
            List of performance metrics for all agents
        """
        results = []

        if not self.agent_data_path.exists():
            print(f"❌ Agent data path not found: {self.agent_data_path}")
            return results

        # Find all agent directories
        agent_dirs = [d for d in self.agent_data_path.iterdir() if d.is_dir()]

        for agent_dir in agent_dirs:
            signature = agent_dir.name
            print(f"📊 Analyzing {signature}...")
            metrics = self.calculate_all_metrics(signature)
            results.append(metrics)

        # Sort by total return
        results.sort(key=lambda x: x.get('total_return', 0), reverse=True)

        return results

    def print_leaderboard(self, results: List[Dict]) -> None:
        """
        Print performance leaderboard

        Args:
            results: List of performance metrics
        """
        print("\n" + "=" * 80)
        print("🏆 AI-TRADER PERFORMANCE LEADERBOARD 🏆")
        print("=" * 80)
        print()

        # Header
        print(f"{'Rank':<6} {'Model':<25} {'Return %':<12} {'Sharpe':<10} {'Max DD %':<12} {'Trades':<8}")
        print("-" * 80)

        # Results
        for i, result in enumerate(results, 1):
            if 'error' in result:
                print(f"{i:<6} {result['signature']:<25} {'N/A':<12} {'N/A':<10} {'N/A':<12} {'N/A':<8}")
            else:
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                print(f"{medal:<6} {result['signature']:<25} {result['total_return']:>10.2f}% {result['sharpe_ratio']:>9.2f} {result['max_drawdown']:>10.2f}% {result['total_trades']:>7}")

        print("=" * 80)
        print()

    def save_results(self, results: List[Dict], output_file: str = "./performance_report.json") -> None:
        """
        Save performance results to file

        Args:
            results: List of performance metrics
            output_file: Output file path
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'results': results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"💾 Performance report saved to: {output_file}")


def main():
    """Main function"""
    print("🚀 AI-Trader Performance Analysis")
    print()

    # Create calculator
    calculator = PerformanceCalculator()

    # Analyze all agents
    results = calculator.analyze_all_agents()

    if not results:
        print("❌ No agent data found. Please run trading first.")
        return 1

    # Print leaderboard
    calculator.print_leaderboard(results)

    # Save results
    calculator.save_results(results)

    print("✅ Performance analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
